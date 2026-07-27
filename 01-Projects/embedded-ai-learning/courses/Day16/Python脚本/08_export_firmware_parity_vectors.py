"""Export raw 64-sample windows for Python/C/INT8 firmware parity tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from pipeline_common import (
    CLASS_NAMES,
    PipelineConfig,
    extract_frequency_features,
    extract_time_features,
    load_all_clean_data,
    resample_clean_frame,
)


CHANNELS = (
    "lin_x",
    "lin_y",
    "lin_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "acc_norm_centered",
)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    validation_root = script_dir.parents[1]
    day16_root = validation_root.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=day16_root / "数据")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=validation_root / "01_交付文件" / "模型B_含频域",
    )
    parser.add_argument(
        "--output-header",
        type=Path,
        default=validation_root
        / "01_交付文件"
        / "STM32部署参数"
        / "day16_parity_vectors.h",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=validation_root
        / "02_过程与中间文件"
        / "09_端到端一致性诊断"
        / "firmware_parity_vectors.json",
    )
    return parser.parse_args()


def extract_selected(window, preprocessing: dict, sample_rate_hz: float) -> np.ndarray:
    window = window.copy()
    window.loc[window.index[0], "lin_delta_norm"] = 0.0
    window.loc[window.index[0], "gyro_delta_norm"] = 0.0
    _, time_values = extract_time_features(window)
    _, frequency_values = extract_frequency_features(window, sample_rate_hz)
    all_values = np.concatenate((time_values, frequency_values)).astype(np.float64)
    return all_values[np.asarray(preprocessing["selected_indices"], dtype=np.int64)]


def preprocess_and_quantize(
    raw_features: np.ndarray,
    preprocessing: dict,
    input_scale: float,
    input_zero_point: int,
) -> np.ndarray:
    low = np.asarray(preprocessing["clip_low_selected"], dtype=np.float64)
    high = np.asarray(preprocessing["clip_high_selected"], dtype=np.float64)
    mean = np.asarray(preprocessing["normalization_mean"], dtype=np.float64)
    std = np.asarray(preprocessing["normalization_std"], dtype=np.float64)
    normalized = (np.clip(raw_features, low, high) - mean) / std
    qf = normalized / input_scale + input_zero_point
    quantized = np.where(qf >= 0.0, np.floor(qf + 0.5), np.ceil(qf - 0.5))
    return np.clip(quantized, -128, 127).astype(np.int8)


def invoke(interpreter, quantized_input: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    interpreter.set_tensor(
        input_detail["index"],
        quantized_input.reshape(input_detail["shape"]).astype(input_detail["dtype"]),
    )
    interpreter.invoke()
    qout = interpreter.get_tensor(output_detail["index"]).reshape(-1).astype(np.int8)
    scale, zero_point = output_detail["quantization"]
    probs = (qout.astype(np.float64) - zero_point) * scale
    return qout, probs


def float_array(values: np.ndarray, indent: str = "    ") -> str:
    rows = []
    for start in range(0, len(values), 7):
        chunk = values[start : start + 7]
        rows.append(indent + ", ".join(f"{float(value):.9e}f" for value in chunk))
    return ",\n".join(rows)


def int_array(values: np.ndarray, indent: str = "    ") -> str:
    rows = []
    for start in range(0, len(values), 14):
        chunk = values[start : start + 14]
        rows.append(indent + ", ".join(str(int(value)) for value in chunk))
    return ",\n".join(rows)


def main() -> None:
    args = parse_args()
    config = PipelineConfig()
    preprocessing = json.loads(
        (args.model_dir / "preprocessing.json").read_text(encoding="utf-8")
    )

    import tensorflow as tf

    interpreter = tf.lite.Interpreter(
        model_content=(args.model_dir / "model_int8.tflite").read_bytes()
    )
    interpreter.allocate_tensors()
    input_scale, input_zero_point = interpreter.get_input_details()[0]["quantization"]

    frames = load_all_clean_data(args.data_root)
    vectors: list[dict[str, object]] = []
    for label_id, class_name in enumerate(CLASS_NAMES):
        frame = frames[class_name]
        if class_name == "stairs":
            frame = frame[frame["t_ms"] < 290768.0].reset_index(drop=True)
        resampled = resample_clean_frame(frame, config)
        stop = len(resampled) - config.window_samples + 1
        candidate_starts = range(
            max(0, int(stop * 0.65)),
            max(1, int(stop * 0.90)),
            config.hop_samples,
        )
        selected = None
        for start in candidate_starts:
            window = resampled.iloc[start : start + config.window_samples].copy()
            raw_features = extract_selected(
                window, preprocessing, config.target_sample_rate_hz
            )
            qin = preprocess_and_quantize(
                raw_features, preprocessing, input_scale, input_zero_point
            )
            qout, probs = invoke(interpreter, qin)
            if int(np.argmax(probs)) == label_id:
                selected = (window, raw_features, qin, qout, probs)
                break
        if selected is None:
            raise RuntimeError(f"No correctly classified parity window for {class_name}")
        window, raw_features, qin, qout, probs = selected
        vectors.append(
            {
                "class_name": class_name,
                "label_id": label_id,
                "start_ms": float(window["t_ms"].iloc[0]),
                "end_ms": float(window["t_ms"].iloc[-1]),
                "samples": window.loc[:, CHANNELS].to_numpy(dtype=np.float32),
                "raw_features": raw_features.astype(np.float32),
                "quantized_input": qin,
                "quantized_output": qout,
                "probabilities": probs.astype(np.float32),
            }
        )

    header = [
        "#ifndef DAY16_PARITY_VECTORS_H",
        "#define DAY16_PARITY_VECTORS_H",
        "",
        "#include <stdint.h>",
        "",
        "#define DAY16_PARITY_VECTOR_COUNT (3U)",
        "#define DAY16_PARITY_SAMPLE_CHANNELS (7U)",
        "",
        "static const int8_t day16_parity_labels[3] = {0, 1, 2};",
        "",
        "static const float day16_parity_samples[3][64][7] = {",
    ]
    for vector in vectors:
        header.append("  {")
        for sample in vector["samples"]:
            header.append("    {" + ", ".join(f"{float(v):.9e}f" for v in sample) + "},")
        header.append("  },")
    header.extend(
        [
            "};",
            "",
            "static const int8_t day16_parity_expected_input[3][56] = {",
        ]
    )
    for vector in vectors:
        header.append("  {")
        header.append(int_array(vector["quantized_input"], indent="    "))
        header.append("  },")
    header.extend(
        [
            "};",
            "",
            "static const int8_t day16_parity_expected_output[3][3] = {",
        ]
    )
    for vector in vectors:
        header.append(
            "  {" + ", ".join(str(int(v)) for v in vector["quantized_output"]) + "},"
        )
    header.extend(["};", "", "#endif /* DAY16_PARITY_VECTORS_H */", ""])

    args.output_header.parent.mkdir(parents=True, exist_ok=True)
    args.output_header.write_text("\n".join(header), encoding="ascii")

    json_records = []
    for vector in vectors:
        json_records.append(
            {
                key: value.tolist() if isinstance(value, np.ndarray) else value
                for key, value in vector.items()
                if key != "samples"
            }
        )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(
            {
                "model": str(args.model_dir / "model_int8.tflite"),
                "input_quantization": [input_scale, input_zero_point],
                "vectors": json_records,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(args.output_header)
    print(args.output_json)


if __name__ == "__main__":
    main()
