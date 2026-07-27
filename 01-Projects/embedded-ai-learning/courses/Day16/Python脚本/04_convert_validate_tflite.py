"""Convert both Keras models to deployable TFLite and verify every test row."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
from pathlib import Path

import numpy as np
import tensorflow as tf

from pipeline_common import (
    CLASS_NAMES,
    classification_metrics,
    sha256_file,
    write_json,
)


MODEL_KEYS = ("time_only", "time_frequency")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--delivery-dir", type=Path, required=True)
    return parser.parse_args()


def representative_dataset(x_train: np.ndarray):
    count = min(300, len(x_train))
    indices = np.linspace(0, len(x_train) - 1, count, dtype=int)

    def generator():
        for index in indices:
            yield [x_train[index : index + 1].astype(np.float32)]

    return generator, indices


def convert_float32(model: tf.keras.Model) -> bytes:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    return converter.convert()


def convert_int8(model: tf.keras.Model, x_train: np.ndarray) -> tuple[bytes, np.ndarray]:
    generator, indices = representative_dataset(x_train)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = generator
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS_INT8
    ]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    return converter.convert(), indices


def tensor_detail_to_json(detail: dict[str, object]) -> dict[str, object]:
    quantization_parameters = detail["quantization_parameters"]
    return {
        "name": str(detail["name"]),
        "index": int(detail["index"]),
        "shape": np.asarray(detail["shape"]).astype(int).tolist(),
        "shape_signature": np.asarray(detail["shape_signature"])
        .astype(int)
        .tolist(),
        "dtype": np.dtype(detail["dtype"]).name,
        "quantization": [
            float(detail["quantization"][0]),
            int(detail["quantization"][1]),
        ],
        "quantization_parameters": {
            "scales": np.asarray(quantization_parameters["scales"])
            .astype(float)
            .tolist(),
            "zero_points": np.asarray(
                quantization_parameters["zero_points"]
            )
            .astype(int)
            .tolist(),
            "quantized_dimension": int(
                quantization_parameters["quantized_dimension"]
            ),
        },
    }


def run_tflite(model_path: Path, matrix: np.ndarray) -> tuple[np.ndarray, dict]:
    # The TensorFlow Windows wrapper cannot reliably open non-ASCII paths.
    interpreter = tf.lite.Interpreter(model_content=model_path.read_bytes())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]

    probabilities: list[np.ndarray] = []
    input_dtype = np.dtype(input_detail["dtype"])
    output_dtype = np.dtype(output_detail["dtype"])
    input_scale, input_zero_point = input_detail["quantization"]
    output_scale, output_zero_point = output_detail["quantization"]

    for row in matrix:
        value = row[np.newaxis, :].astype(np.float32)
        if np.issubdtype(input_dtype, np.integer):
            if input_scale <= 0:
                raise ValueError("Integer input has an invalid quantization scale")
            limits = np.iinfo(input_dtype)
            value = np.clip(
                np.rint(value / input_scale + input_zero_point),
                limits.min,
                limits.max,
            ).astype(input_dtype)
        interpreter.set_tensor(input_detail["index"], value)
        interpreter.invoke()
        output = interpreter.get_tensor(output_detail["index"])[0]
        if np.issubdtype(output_dtype, np.integer):
            output = (
                output.astype(np.float32) - float(output_zero_point)
            ) * float(output_scale)
        probabilities.append(output.astype(np.float32))

    details = {
        "input": tensor_detail_to_json(input_detail),
        "output": tensor_detail_to_json(output_detail),
        "tensor_count": len(interpreter.get_tensor_details()),
    }
    return np.vstack(probabilities), details


def analyze_tflite(model_content: bytes) -> str:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        tf.lite.experimental.Analyzer.analyze(
            model_content=model_content,
            gpu_compatibility=False,
        )
    return output.getvalue()


def convert_model(
    model_key: str,
    args: argparse.Namespace,
) -> dict[str, object]:
    training_model_dir = args.training_dir / model_key
    output_model_dir = args.output_dir / model_key
    delivery_model_dir = args.delivery_dir / model_key
    output_model_dir.mkdir(parents=True, exist_ok=True)
    delivery_model_dir.mkdir(parents=True, exist_ok=True)

    model = tf.keras.models.load_model(
        training_model_dir / "model_float32.keras"
    )
    dataset = np.load(
        training_model_dir / "normalized_selected_dataset.npz",
        allow_pickle=False,
    )
    x_train = dataset["x_train"].astype(np.float32)
    x_test = dataset["x_test"].astype(np.float32)
    y_test = dataset["y_test"].astype(np.int64)

    float32_content = convert_float32(model)
    int8_content, representative_indices = convert_int8(model, x_train)
    float32_path = output_model_dir / "model_float32.tflite"
    int8_path = output_model_dir / "model_int8.tflite"
    float32_path.write_bytes(float32_content)
    int8_path.write_bytes(int8_content)

    keras_probabilities = model.predict(x_test, verbose=0).astype(np.float32)
    float32_probabilities, float32_details = run_tflite(float32_path, x_test)
    int8_probabilities, int8_details = run_tflite(int8_path, x_test)
    keras_prediction = np.argmax(keras_probabilities, axis=1)
    float32_prediction = np.argmax(float32_probabilities, axis=1)
    int8_prediction = np.argmax(int8_probabilities, axis=1)

    keras_metrics = classification_metrics(y_test, keras_prediction)
    float32_metrics = classification_metrics(y_test, float32_prediction)
    int8_metrics = classification_metrics(y_test, int8_prediction)
    result = {
        "model_key": model_key,
        "class_order": list(CLASS_NAMES),
        "test_rows": int(len(y_test)),
        "keras_metrics": keras_metrics,
        "float32_tflite_metrics": float32_metrics,
        "int8_tflite_metrics": int8_metrics,
        "keras_vs_float32_prediction_agreement": float(
            np.mean(keras_prediction == float32_prediction)
        ),
        "keras_vs_int8_prediction_agreement": float(
            np.mean(keras_prediction == int8_prediction)
        ),
        "float32_vs_int8_prediction_agreement": float(
            np.mean(float32_prediction == int8_prediction)
        ),
        "keras_vs_float32_probability_mae": float(
            np.mean(np.abs(keras_probabilities - float32_probabilities))
        ),
        "keras_vs_int8_probability_mae": float(
            np.mean(np.abs(keras_probabilities - int8_probabilities))
        ),
        "keras_vs_int8_probability_max_error": float(
            np.max(np.abs(keras_probabilities - int8_probabilities))
        ),
        "float32_tflite": {
            "bytes": len(float32_content),
            "sha256": sha256_file(float32_path),
            "tensor_details": float32_details,
        },
        "int8_tflite": {
            "bytes": len(int8_content),
            "sha256": sha256_file(int8_path),
            "tensor_details": int8_details,
            "representative_row_count": int(len(representative_indices)),
            "representative_indices": representative_indices.tolist(),
        },
    }
    write_json(output_model_dir / "tflite_validation.json", result)
    (output_model_dir / "float32_analyzer.txt").write_text(
        analyze_tflite(float32_content),
        encoding="utf-8",
    )
    (output_model_dir / "int8_analyzer.txt").write_text(
        analyze_tflite(int8_content),
        encoding="utf-8",
    )
    np.savez_compressed(
        output_model_dir / "tflite_test_outputs.npz",
        y_test=y_test,
        keras_probabilities=keras_probabilities,
        float32_probabilities=float32_probabilities,
        int8_probabilities=int8_probabilities,
    )
    np.savez_compressed(
        output_model_dir / "representative_dataset_normalized.npz",
        x_representative=x_train[representative_indices],
        source_train_indices=representative_indices,
    )

    shutil.copy2(float32_path, delivery_model_dir / "model_float32.tflite")
    shutil.copy2(int8_path, delivery_model_dir / "model_int8.tflite")
    shutil.copy2(
        output_model_dir / "tflite_validation.json",
        delivery_model_dir / "tflite_validation.json",
    )
    shutil.copy2(
        output_model_dir / "int8_analyzer.txt",
        delivery_model_dir / "int8_analyzer.txt",
    )
    return result


def main() -> None:
    args = parse_args()
    args.training_dir = args.training_dir.resolve()
    args.output_dir = args.output_dir.resolve()
    args.delivery_dir = args.delivery_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {
        model_key: convert_model(model_key, args)
        for model_key in MODEL_KEYS
    }
    write_json(args.output_dir / "tflite_comparison.json", results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
