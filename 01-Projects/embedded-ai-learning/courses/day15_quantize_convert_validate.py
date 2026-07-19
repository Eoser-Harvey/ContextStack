#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day15: 模型量化与转换实战脚本

这个脚本承接 Day14 的训练输出，把 Keras 模型转换成 TensorFlow Lite
模型，并完成转换后的基础验证。它面向零 AI 基础的嵌入式工程师，代码
刻意写得直接一些，方便课堂逐行讲解。

默认输入：
    Day14-模型验证/01_课程交付文件/Python脚本/day14_training_output

默认输出：
    当前目录/day15_quantization_output

最常用运行方式：
    python day15_quantize_convert_validate.py

指定 Day14 输出目录：
    python day15_quantize_convert_validate.py --day14-output D:/xxx/day14_training_output

指定输出目录：
    python day15_quantize_convert_validate.py --out D:/xxx/day15_quantization_output
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


RANDOM_SEED = 42

warnings.filterwarnings("ignore", message=".*tf.lite.Interpreter is deprecated.*")
warnings.filterwarnings("ignore", message="Statistics for quantized inputs.*")


@dataclass
class Day15Data:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    test_info: pd.DataFrame
    feature_columns: List[str]
    label_to_id: Dict[str, int]
    id_to_label: Dict[int, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Day14 Keras model to float/int8 TFLite and validate the result."
    )
    parser.add_argument(
        "--day14-output",
        type=Path,
        default=None,
        help="Day14 output folder that contains model.keras, scaler.json, label_map.json.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Keras model path. Default: best_model.keras first, then model.keras.",
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=None,
        help="features_all.csv path. Default: read from Day14 metrics.json.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output folder. Default: ./day15_quantization_output.",
    )
    parser.add_argument(
        "--representative-samples",
        type=int,
        default=120,
        help="Number of train samples used for int8 calibration.",
    )
    parser.add_argument(
        "--validation-samples",
        type=int,
        default=0,
        help="Number of test samples for validation. 0 means use all test samples.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument(
        "--skip-header",
        action="store_true",
        help="Do not generate C header from int8 TFLite file.",
    )
    return parser.parse_args()


def find_course_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if any(p.is_dir() and p.name.startswith("Day14") for p in parent.iterdir()):
            return parent
    return here.parent


def find_day_dir(prefix: str) -> Path | None:
    course_root = find_course_root()
    for item in course_root.iterdir():
        if item.is_dir() and item.name.startswith(prefix):
            return item
    return None


def first_child_dir(parent: Path, predicate: Callable[[Path], bool]) -> Path | None:
    if not parent.exists():
        return None
    for item in parent.iterdir():
        if item.is_dir() and predicate(item):
            return item
    return None


def discover_day14_output() -> Path:
    day14_dir = find_day_dir("Day14")
    if day14_dir is None:
        raise FileNotFoundError("Cannot find Day14 folder from the current course root.")

    delivery_dir = first_child_dir(day14_dir, lambda p: p.name.startswith("01_"))
    if delivery_dir is None:
        raise FileNotFoundError(f"Cannot find delivery folder under {day14_dir}.")

    python_dir = first_child_dir(delivery_dir, lambda p: "Python" in p.name)
    if python_dir is None:
        raise FileNotFoundError(f"Cannot find Python script folder under {delivery_dir}.")

    output_dir = python_dir / "day14_training_output"
    if not output_dir.exists():
        raise FileNotFoundError(f"Cannot find Day14 training output: {output_dir}")
    return output_dir


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def resolve_input_paths(args: argparse.Namespace) -> Tuple[Path, Path, Path]:
    day14_output = args.day14_output or discover_day14_output()
    day14_output = day14_output.resolve()
    if not day14_output.exists():
        raise FileNotFoundError(f"Day14 output folder does not exist: {day14_output}")

    if args.model is not None:
        model_path = args.model.resolve()
    else:
        preferred = [day14_output / "best_model.keras", day14_output / "model.keras"]
        model_path = next((p for p in preferred if p.exists()), preferred[-1])
    if not model_path.exists():
        raise FileNotFoundError(f"Keras model does not exist: {model_path}")

    if args.features is not None:
        features_csv = args.features.resolve()
    else:
        metrics_path = day14_output / "metrics.json"
        features_csv = None
        if metrics_path.exists():
            metrics = load_json(metrics_path)
            raw_path = metrics.get("input_csv")
            if raw_path:
                candidate = Path(raw_path)
                if candidate.exists():
                    features_csv = candidate.resolve()
        if features_csv is None:
            day12_dir = find_day_dir("Day12")
            candidates = list(day12_dir.rglob("features_all.csv")) if day12_dir else []
            features_csv = candidates[0].resolve() if candidates else None
        if features_csv is None:
            raise FileNotFoundError("Cannot find features_all.csv. Please pass --features.")

    if not features_csv.exists():
        raise FileNotFoundError(f"Feature CSV does not exist: {features_csv}")
    return day14_output, model_path, features_csv


def load_feature_columns(day14_output: Path) -> List[str]:
    payload = load_json(day14_output / "feature_columns.json")
    if isinstance(payload, dict):
        columns = payload.get("feature_columns")
    else:
        columns = payload
    if not isinstance(columns, list) or not columns:
        raise ValueError("feature_columns.json must contain a non-empty feature column list.")
    return [str(x) for x in columns]


def load_scaler(day14_output: Path) -> Tuple[np.ndarray, np.ndarray]:
    scaler = load_json(day14_output / "scaler.json")
    mean = np.asarray(scaler["mean"], dtype=np.float32)
    std = np.asarray(scaler["std"], dtype=np.float32)
    std[std < 1e-8] = 1.0
    return mean, std


def load_label_map(day14_output: Path) -> Tuple[Dict[str, int], Dict[int, str]]:
    label_to_id = {str(k): int(v) for k, v in load_json(day14_output / "label_map.json").items()}
    id_to_label = {idx: name for name, idx in label_to_id.items()}
    return label_to_id, id_to_label


def stratified_split(
    y: np.ndarray,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = RANDOM_SEED,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx: List[int] = []
    val_idx: List[int] = []
    test_idx: List[int] = []

    for label_id in sorted(np.unique(y)):
        indices = np.where(y == label_id)[0]
        rng.shuffle(indices)
        n = len(indices)
        n_train = max(1, int(round(n * train_ratio)))
        n_val = max(1, int(round(n * val_ratio)))
        if n_train + n_val >= n:
            n_train = max(1, n - 2)
            n_val = 1
        train_idx.extend(indices[:n_train].tolist())
        val_idx.extend(indices[n_train : n_train + n_val].tolist())
        test_idx.extend(indices[n_train + n_val :].tolist())

    return np.array(train_idx), np.array(val_idx), np.array(test_idx)


def prepare_day15_data(features_csv: Path, day14_output: Path, seed: int) -> Day15Data:
    feature_columns = load_feature_columns(day14_output)
    scaler_mean, scaler_std = load_scaler(day14_output)
    label_to_id, id_to_label = load_label_map(day14_output)

    df = pd.read_csv(features_csv)
    if "label" not in df.columns:
        raise ValueError("features_all.csv must contain a label column.")

    missing = [name for name in feature_columns if name not in df.columns]
    if missing:
        preview = ", ".join(missing[:8])
        raise ValueError(f"features_all.csv is missing feature columns: {preview}")

    unknown_labels = sorted(set(df["label"].astype(str)) - set(label_to_id))
    if unknown_labels:
        raise ValueError(f"features_all.csv contains labels not in label_map.json: {unknown_labels}")

    x_df = df[feature_columns].copy()
    x_df = x_df.replace([np.inf, -np.inf], np.nan)
    x_df = x_df.fillna(x_df.median(numeric_only=True)).fillna(0.0)
    x_raw = x_df.to_numpy(dtype=np.float32)

    if len(scaler_mean) != x_raw.shape[1] or len(scaler_std) != x_raw.shape[1]:
        raise ValueError(
            "scaler.json length does not match feature_columns.json. "
            f"scaler={len(scaler_mean)}, features={x_raw.shape[1]}"
        )

    x_scaled = ((x_raw - scaler_mean) / scaler_std).astype(np.float32)
    y = df["label"].astype(str).map(label_to_id).to_numpy(dtype=np.int64)
    train_idx, _, test_idx = stratified_split(y, seed=seed)

    info_columns = [c for c in ["window_id", "label", "label_cn"] if c in df.columns]
    if not info_columns:
        info_columns = ["label"]
    test_info = df.iloc[test_idx][info_columns].copy().reset_index(drop=True)

    return Day15Data(
        x_train=x_scaled[train_idx],
        y_train=y[train_idx],
        x_test=x_scaled[test_idx],
        y_test=y[test_idx],
        test_info=test_info,
        feature_columns=feature_columns,
        label_to_id=label_to_id,
        id_to_label=id_to_label,
    )


def import_tensorflow():
    tmp_dir = find_course_root() / ".tmp_day15_tensorflow"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = str(tmp_dir)
    os.environ["TMP"] = str(tmp_dir)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

    try:
        import tensorflow as tf  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "TensorFlow is required for Day15 conversion. Install it in the same "
            "Python environment used for Day14, then rerun this script."
        ) from exc
    try:
        tf.get_logger().setLevel("ERROR")
    except Exception:
        pass
    return tf


def make_representative_dataset(
    x_train: np.ndarray,
    max_samples: int,
    seed: int,
) -> Tuple[Callable[[], Iterable[List[np.ndarray]]], int]:
    if max_samples <= 0 or max_samples >= len(x_train):
        selected = np.arange(len(x_train))
    else:
        rng = np.random.default_rng(seed)
        selected = rng.choice(len(x_train), size=max_samples, replace=False)

    samples = x_train[selected].astype(np.float32)

    def representative_dataset() -> Iterable[List[np.ndarray]]:
        for row in samples:
            yield [row.reshape(1, -1).astype(np.float32)]

    return representative_dataset, len(samples)


def convert_float_tflite(tf, model: Any, out_path: Path) -> bytes:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    model_bytes = converter.convert()
    out_path.write_bytes(model_bytes)
    return model_bytes


def convert_int8_tflite(
    tf,
    model: Any,
    representative_dataset: Callable[[], Iterable[List[np.ndarray]]],
    out_path: Path,
) -> bytes:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    model_bytes = converter.convert()
    out_path.write_bytes(model_bytes)
    return model_bytes


def array_to_list(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.generic,)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): array_to_list(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [array_to_list(v) for v in value]
    if hasattr(value, "__name__"):
        return value.__name__
    return value


def get_model_io_details(tf, model_path: Path) -> Dict[str, Any]:
    # On Windows, some TensorFlow Lite builds cannot open a model_path that
    # contains non-ASCII characters. Loading from bytes avoids that path issue.
    interpreter = tf.lite.Interpreter(model_content=model_path.read_bytes())
    interpreter.allocate_tensors()
    return {
        "inputs": array_to_list(interpreter.get_input_details()),
        "outputs": array_to_list(interpreter.get_output_details()),
    }


def fit_input_shape(row: np.ndarray, shape: np.ndarray) -> Tuple[int, ...]:
    target = [1 if int(dim) in (-1, 0) else int(dim) for dim in shape]
    if int(np.prod(target)) != row.size:
        target = [1, row.size]
    return tuple(target)


def quantize_tensor(x: np.ndarray, detail: Dict[str, Any]) -> np.ndarray:
    dtype = detail["dtype"]
    if np.issubdtype(dtype, np.floating):
        return x.astype(dtype)

    scale, zero_point = detail.get("quantization", (0.0, 0))
    scale = float(scale)
    zero_point = int(zero_point)
    if scale == 0:
        raise ValueError("TFLite tensor has integer dtype but zero quantization scale.")

    q = np.round(x / scale + zero_point)
    limits = np.iinfo(dtype)
    q = np.clip(q, limits.min, limits.max)
    return q.astype(dtype)


def dequantize_tensor(x: np.ndarray, detail: Dict[str, Any]) -> np.ndarray:
    dtype = detail["dtype"]
    if np.issubdtype(dtype, np.floating):
        return x.astype(np.float32)

    scale, zero_point = detail.get("quantization", (0.0, 0))
    scale = float(scale)
    zero_point = int(zero_point)
    if scale == 0:
        return x.astype(np.float32)
    return (x.astype(np.float32) - zero_point) * scale


def predict_tflite(tf, model_path: Path, x: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    # See get_model_io_details(): model_content is safer for Chinese paths.
    interpreter = tf.lite.Interpreter(model_content=model_path.read_bytes())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]

    outputs: List[np.ndarray] = []
    for row in x.astype(np.float32):
        sample = row.reshape(fit_input_shape(row, input_detail["shape"]))
        sample = quantize_tensor(sample, input_detail)
        interpreter.set_tensor(input_detail["index"], sample)
        interpreter.invoke()
        raw_output = interpreter.get_tensor(output_detail["index"])
        outputs.append(dequantize_tensor(raw_output, output_detail).reshape(-1))

    details = {
        "input": array_to_list(input_detail),
        "output": array_to_list(output_detail),
    }
    return np.vstack(outputs), details


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for true_id, pred_id in zip(y_true, y_pred):
        cm[int(true_id), int(pred_id)] += 1
    return cm


def classification_report(cm: np.ndarray, id_to_label: Dict[int, str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for class_id in range(cm.shape[0]):
        tp = float(cm[class_id, class_id])
        fp = float(cm[:, class_id].sum() - tp)
        fn = float(cm[class_id, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append(
            {
                "label": id_to_label[class_id],
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": int(cm[class_id, :].sum()),
            }
        )
    return rows


def metrics_from_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    id_to_label: Dict[int, str],
) -> Dict[str, Any]:
    cm = confusion_matrix(y_true, y_pred, len(id_to_label))
    report = classification_report(cm, id_to_label)
    return {
        "accuracy": float(np.mean(y_true == y_pred)),
        "macro_f1": float(np.mean([row["f1"] for row in report])),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


def write_prediction_compare(
    out_csv: Path,
    data: Day15Data,
    keras_pred: np.ndarray,
    float_pred: np.ndarray,
    int8_pred: np.ndarray,
) -> None:
    compare = data.test_info.copy()
    compare["true_id"] = data.y_test
    compare["keras_pred_id"] = keras_pred
    compare["float_tflite_pred_id"] = float_pred
    compare["int8_tflite_pred_id"] = int8_pred
    compare["keras_pred_label"] = [data.id_to_label[int(i)] for i in keras_pred]
    compare["float_tflite_pred_label"] = [data.id_to_label[int(i)] for i in float_pred]
    compare["int8_tflite_pred_label"] = [data.id_to_label[int(i)] for i in int8_pred]
    compare["float_matches_keras"] = keras_pred == float_pred
    compare["int8_matches_keras"] = keras_pred == int8_pred
    compare.to_csv(out_csv, index=False, encoding="utf-8-sig")


def write_classification_csv(out_csv: Path, model_reports: Dict[str, Dict[str, Any]]) -> None:
    fieldnames = ["model", "label", "precision", "recall", "f1", "support"]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for model_name, metrics in model_reports.items():
            for row in metrics["classification_report"]:
                writer.writerow({"model": model_name, **row})


def write_c_header(tflite_path: Path, header_path: Path, array_name: str) -> None:
    data = tflite_path.read_bytes()
    guard = f"{array_name.upper()}_H_"
    lines = [
        "/* Auto-generated by Day15 model quantization script. */",
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
        "#ifdef __cplusplus",
        'extern "C" {',
        "#endif",
        "",
        f"const unsigned char {array_name}[] __attribute__((aligned(4))) = {{",
    ]

    for start in range(0, len(data), 12):
        chunk = data[start : start + 12]
        lines.append("  " + ", ".join(f"0x{byte:02x}" for byte in chunk) + ",")

    lines.extend(
        [
            "};",
            f"const unsigned int {array_name}_len = {len(data)};",
            "",
            "#ifdef __cplusplus",
            "}",
            "#endif",
            "",
            f"#endif /* {guard} */",
            "",
        ]
    )
    header_path.write_text("\n".join(lines), encoding="utf-8")


def file_size(path: Path) -> int:
    return int(path.stat().st_size) if path.exists() else 0


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copy2(src, dst)


def write_run_summary(out_path: Path, report: Dict[str, Any]) -> None:
    size = report["model_size_bytes"]
    validation = report["validation"]
    lines = [
        "Day15 模型量化与转换输出摘要",
        "================================",
        f"Keras 模型: {report['input_files']['keras_model']}",
        f"特征表: {report['input_files']['features_csv']}",
        f"特征数量: {report['dataset']['num_features']}",
        f"测试样本数: {report['dataset']['test_samples']}",
        "",
        "模型文件大小:",
        f"  Keras:        {size['keras_model']} bytes",
        f"  Float TFLite: {size['float_tflite']} bytes",
        f"  Int8 TFLite:  {size['int8_tflite']} bytes",
        "",
        "验证指标:",
        f"  Keras accuracy / macro F1:        {validation['keras']['accuracy']:.4f} / {validation['keras']['macro_f1']:.4f}",
        f"  Float TFLite accuracy / macro F1: {validation['float_tflite']['accuracy']:.4f} / {validation['float_tflite']['macro_f1']:.4f}",
        f"  Int8 TFLite accuracy / macro F1:  {validation['int8_tflite']['accuracy']:.4f} / {validation['int8_tflite']['macro_f1']:.4f}",
        "",
        "主要输出文件:",
        "  model_float32.tflite",
        "  model_int8.tflite",
        "  model_int8_data.h",
        "  quantization_report.json",
        "  conversion_compare.csv",
        "  model_io_details.json",
        "  day16_handoff_manifest.json",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    day14_output, model_path, features_csv = resolve_input_paths(args)
    out_dir = (args.out or (Path(__file__).resolve().parent / "day15_quantization_output")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Preparing Day15 data...")
    data = prepare_day15_data(features_csv, day14_output, args.seed)
    if args.validation_samples and args.validation_samples > 0:
        limit = min(args.validation_samples, len(data.x_test))
        data.x_test = data.x_test[:limit]
        data.y_test = data.y_test[:limit]
        data.test_info = data.test_info.iloc[:limit].reset_index(drop=True)

    print("Importing TensorFlow...")
    tf = import_tensorflow()
    try:
        tf.keras.utils.set_random_seed(args.seed)
    except Exception:
        pass

    print(f"Loading Keras model: {model_path}")
    model = tf.keras.models.load_model(model_path, compile=False)

    print("Converting float TFLite...")
    float_path = out_dir / "model_float32.tflite"
    convert_float_tflite(tf, model, float_path)

    print("Converting full integer int8 TFLite...")
    representative_dataset, representative_count = make_representative_dataset(
        data.x_train,
        args.representative_samples,
        args.seed,
    )
    int8_path = out_dir / "model_int8.tflite"
    convert_int8_tflite(tf, model, representative_dataset, int8_path)

    print("Inspecting TFLite input/output details...")
    io_details = {
        "float_tflite": get_model_io_details(tf, float_path),
        "int8_tflite": get_model_io_details(tf, int8_path),
    }
    save_json(out_dir / "model_io_details.json", io_details)

    if not args.skip_header:
        print("Writing C header for TensorFlow Lite Micro style integration...")
        write_c_header(int8_path, out_dir / "model_int8_data.h", "g_day15_action_model_int8")

    print("Validating Keras, float TFLite and int8 TFLite on the same test samples...")
    keras_probs = model.predict(data.x_test.astype(np.float32), verbose=0)
    keras_pred = np.argmax(keras_probs, axis=1)

    float_probs, float_runtime_details = predict_tflite(tf, float_path, data.x_test)
    float_pred = np.argmax(float_probs, axis=1)

    int8_probs, int8_runtime_details = predict_tflite(tf, int8_path, data.x_test)
    int8_pred = np.argmax(int8_probs, axis=1)

    model_reports = {
        "keras": metrics_from_predictions(data.y_test, keras_pred, data.id_to_label),
        "float_tflite": metrics_from_predictions(data.y_test, float_pred, data.id_to_label),
        "int8_tflite": metrics_from_predictions(data.y_test, int8_pred, data.id_to_label),
    }

    write_prediction_compare(out_dir / "conversion_compare.csv", data, keras_pred, float_pred, int8_pred)
    write_classification_csv(out_dir / "classification_report.csv", model_reports)

    for name in ["scaler.json", "label_map.json", "feature_columns.json"]:
        copy_if_exists(day14_output / name, out_dir / name)

    report = {
        "input_files": {
            "day14_output": str(day14_output),
            "keras_model": str(model_path),
            "features_csv": str(features_csv),
        },
        "output_files": {
            "float_tflite": str(float_path),
            "int8_tflite": str(int8_path),
            "c_header": str(out_dir / "model_int8_data.h"),
            "model_io_details": str(out_dir / "model_io_details.json"),
            "conversion_compare": str(out_dir / "conversion_compare.csv"),
        },
        "dataset": {
            "num_features": len(data.feature_columns),
            "num_classes": len(data.label_to_id),
            "train_samples": int(len(data.x_train)),
            "test_samples": int(len(data.x_test)),
            "representative_samples": representative_count,
            "label_to_id": data.label_to_id,
        },
        "model_size_bytes": {
            "keras_model": file_size(model_path),
            "float_tflite": file_size(float_path),
            "int8_tflite": file_size(int8_path),
        },
        "validation": model_reports,
        "runtime_quantization_details": {
            "float_tflite": float_runtime_details,
            "int8_tflite": int8_runtime_details,
        },
    }
    save_json(out_dir / "quantization_report.json", report)
    save_json(
        out_dir / "day16_handoff_manifest.json",
        {
            "model_int8_tflite": str(int8_path),
            "model_float32_tflite": str(float_path),
            "model_int8_header": str(out_dir / "model_int8_data.h"),
            "scaler_json": str(out_dir / "scaler.json"),
            "label_map_json": str(out_dir / "label_map.json"),
            "feature_columns_json": str(out_dir / "feature_columns.json"),
            "quantization_report_json": str(out_dir / "quantization_report.json"),
            "note": "Use these files as the starting point for Day16 STM32 deployment.",
        },
    )
    write_run_summary(out_dir / "run_summary.txt", report)

    print("\nDone. Day15 output folder:")
    print(out_dir)
    print(f"Keras accuracy:        {model_reports['keras']['accuracy']:.4f}")
    print(f"Float TFLite accuracy: {model_reports['float_tflite']['accuracy']:.4f}")
    print(f"Int8 TFLite accuracy:  {model_reports['int8_tflite']['accuracy']:.4f}")


if __name__ == "__main__":
    main()
