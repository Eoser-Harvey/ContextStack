"""Build STM32 deployment contracts, C headers, test vectors, and reports."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from pipeline_common import CLASS_NAMES, sha256_file, write_json


MODEL_KEYS = ("time_only", "time_frequency")
MODEL_CHINESE_NAMES = {
    "time_only": "模型A_无频域",
    "time_frequency": "模型B_含频域",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day11-root", type=Path, required=True)
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--training-dir", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--conversion-dir", type=Path, required=True)
    parser.add_argument("--delivery-root", type=Path, required=True)
    return parser.parse_args()


def c_float(value: float) -> str:
    return f"{float(value):.9e}f"


def c_array(values: list[float], indent: str = "  ") -> str:
    rows = []
    for start in range(0, len(values), 6):
        row = ", ".join(c_float(value) for value in values[start : start + 6])
        rows.append(indent + row)
    return ",\n".join(rows)


def generate_c_header(
    model_key: str,
    preprocessing: dict[str, object],
    validation: dict[str, object],
) -> str:
    prefix = f"DAY16_{model_key.upper()}"
    int8_info = validation["int8_tflite"]["tensor_details"]
    input_scale, input_zero = int8_info["input"]["quantization"]
    output_scale, output_zero = int8_info["output"]["quantization"]
    feature_names = list(preprocessing["selected_feature_names"])
    feature_comment = "\n".join(
        f" * {index:02d}: {name}" for index, name in enumerate(feature_names)
    )
    return f"""#ifndef {prefix}_PARAMS_H
#define {prefix}_PARAMS_H

#include <stdint.h>

/*
 * Generated deployment parameters for {model_key}.
 * Feature order is part of the model ABI and must not be changed.
{feature_comment}
 */

#define {prefix}_SAMPLE_RATE_HZ       (40.0f)
#define {prefix}_SAMPLE_PERIOD_MS     (25U)
#define {prefix}_WINDOW_SAMPLES       (64U)
#define {prefix}_HOP_SAMPLES          (16U)
#define {prefix}_FEATURE_COUNT        ({len(feature_names)}U)
#define {prefix}_CLASS_COUNT          (3U)
#define {prefix}_INPUT_SCALE          ({c_float(input_scale)})
#define {prefix}_INPUT_ZERO_POINT     ({int(input_zero)})
#define {prefix}_OUTPUT_SCALE         ({c_float(output_scale)})
#define {prefix}_OUTPUT_ZERO_POINT    ({int(output_zero)})

static const char *const {prefix.lower()}_labels[3] = {{
  "idle", "walk", "stairs"
}};

static const float {prefix.lower()}_clip_low[{len(feature_names)}] = {{
{c_array(preprocessing["clip_low_selected"])}
}};

static const float {prefix.lower()}_clip_high[{len(feature_names)}] = {{
{c_array(preprocessing["clip_high_selected"])}
}};

static const float {prefix.lower()}_mean[{len(feature_names)}] = {{
{c_array(preprocessing["normalization_mean"])}
}};

static const float {prefix.lower()}_std[{len(feature_names)}] = {{
{c_array(preprocessing["normalization_std"])}
}};

static inline int8_t {prefix.lower()}_quantize_input(float value)
{{
  float qf = value / {prefix}_INPUT_SCALE
             + (float){prefix}_INPUT_ZERO_POINT;
  int32_t quantized = (int32_t)(qf + (qf >= 0.0f ? 0.5f : -0.5f));
  if (quantized > 127) quantized = 127;
  if (quantized < -128) quantized = -128;
  return (int8_t)quantized;
}}

static inline float {prefix.lower()}_dequantize_output(int8_t value)
{{
  return ((float)value - (float){prefix}_OUTPUT_ZERO_POINT)
         * {prefix}_OUTPUT_SCALE;
}}

#endif
"""


def run_int8_test_vectors(
    model_path: Path,
    x_test: np.ndarray,
    y_test: np.ndarray,
) -> tuple[list[dict[str, object]], np.ndarray, np.ndarray]:
    interpreter = tf.lite.Interpreter(model_content=model_path.read_bytes())
    interpreter.allocate_tensors()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    input_scale, input_zero = input_detail["quantization"]
    output_scale, output_zero = output_detail["quantization"]

    selected_indices: list[int] = []
    for class_id in range(len(CLASS_NAMES)):
        class_rows = np.flatnonzero(y_test == class_id)
        selected_indices.extend(class_rows[:3].tolist())

    input_vectors: list[np.ndarray] = []
    output_vectors: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    for vector_id, source_index in enumerate(selected_indices):
        normalized = x_test[source_index]
        quantized_input = np.clip(
            np.rint(normalized / input_scale + input_zero),
            -128,
            127,
        ).astype(np.int8)
        interpreter.set_tensor(
            input_detail["index"],
            quantized_input[np.newaxis, :],
        )
        interpreter.invoke()
        quantized_output = interpreter.get_tensor(output_detail["index"])[0]
        probabilities = (
            quantized_output.astype(np.float32) - output_zero
        ) * output_scale
        prediction = int(np.argmax(probabilities))
        input_vectors.append(quantized_input)
        output_vectors.append(quantized_output)
        records.append(
            {
                "vector_id": vector_id,
                "source_test_index": int(source_index),
                "expected_id": int(y_test[source_index]),
                "expected_label": CLASS_NAMES[int(y_test[source_index])],
                "predicted_id": prediction,
                "predicted_label": CLASS_NAMES[prediction],
                "probability_idle": float(probabilities[0]),
                "probability_walk": float(probabilities[1]),
                "probability_stairs": float(probabilities[2]),
            }
        )
    return records, np.vstack(input_vectors), np.vstack(output_vectors)


def build_model_package(model_key: str, args: argparse.Namespace) -> dict:
    chinese_name = MODEL_CHINESE_NAMES[model_key]
    destination = args.delivery_root / chinese_name
    destination.mkdir(parents=True, exist_ok=True)
    training = args.training_dir / model_key
    conversion = args.conversion_dir / model_key

    preprocessing = json.loads(
        (training / "preprocessing.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        (conversion / "tflite_validation.json").read_text(encoding="utf-8")
    )
    dataset = np.load(
        training / "normalized_selected_dataset.npz",
        allow_pickle=False,
    )
    x_test = dataset["x_test"].astype(np.float32)
    y_test = dataset["y_test"].astype(np.int64)

    for source_name, destination_name in (
        ("model_float32.keras", "model_float32.keras"),
        ("model_float32.tflite", "model_float32.tflite"),
        ("model_int8.tflite", "model_int8.tflite"),
        ("preprocessing.json", "preprocessing.json"),
        ("training_result.json", "training_result.json"),
        ("tflite_validation.json", "tflite_validation.json"),
        ("int8_analyzer.txt", "int8_analyzer.txt"),
    ):
        source_root = training if (training / source_name).exists() else conversion
        shutil.copy2(source_root / source_name, destination / destination_name)

    selected = pd.DataFrame(
        {
            "model_input_index": np.arange(
                len(preprocessing["selected_feature_names"])
            ),
            "full_feature_index": preprocessing["selected_indices"],
            "feature_name": preprocessing["selected_feature_names"],
            "clip_low": preprocessing["clip_low_selected"],
            "clip_high": preprocessing["clip_high_selected"],
            "mean": preprocessing["normalization_mean"],
            "std": preprocessing["normalization_std"],
        }
    )
    selected.to_csv(
        destination / "selected_features_and_normalization.csv",
        index=False,
        encoding="utf-8-sig",
    )

    header = generate_c_header(model_key, preprocessing, validation)
    (destination / f"day16_{model_key}_params.h").write_text(
        header,
        encoding="utf-8",
    )

    records, quantized_inputs, quantized_outputs = run_int8_test_vectors(
        destination / "model_int8.tflite",
        x_test,
        y_test,
    )
    pd.DataFrame(records).to_csv(
        destination / "deployment_test_vectors_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    np.savez_compressed(
        destination / "deployment_test_vectors.npz",
        quantized_inputs=quantized_inputs,
        expected_quantized_outputs=quantized_outputs,
        records_json=np.asarray(json.dumps(records, ensure_ascii=False)),
    )

    result = {
        "model_key": model_key,
        "delivery_folder": chinese_name,
        "feature_count": len(preprocessing["selected_feature_names"]),
        "int8_tflite_bytes": validation["int8_tflite"]["bytes"],
        "int8_tflite_sha256": sha256_file(destination / "model_int8.tflite"),
        "input_quantization": validation["int8_tflite"]["tensor_details"][
            "input"
        ]["quantization"],
        "output_quantization": validation["int8_tflite"]["tensor_details"][
            "output"
        ]["quantization"],
        "test_vector_count": len(records),
        "test_vectors_all_correct": all(
            item["expected_id"] == item["predicted_id"] for item in records
        ),
    }
    write_json(destination / "deployment_manifest.json", result)
    return result


def build_common_contract(args: argparse.Namespace) -> dict[str, object]:
    main_path = (
        args.day11_root
        / "Software_Package"
        / "Projects"
        / "31_QMI8658A"
        / "Appli"
        / "Core"
        / "Src"
        / "main.c"
    )
    qmi_path = (
        args.day11_root
        / "Software_Package"
        / "Drivers"
        / "BSP"
        / "QMI8658A"
        / "qmi8658.c"
    )
    cutoff = json.loads(
        (args.audit_dir / "stairs_tail_cutoff.json").read_text(encoding="utf-8")
    )
    feature_report = json.loads(
        (args.feature_dir / "feature_dataset_report.json").read_text(
            encoding="utf-8"
        )
    )
    return {
        "class_order": list(CLASS_NAMES),
        "sampling": {
            "target_rate_hz": 40.0,
            "target_period_ms": 25,
            "window_samples": 64,
            "window_duration_seconds": 1.6,
            "hop_samples": 16,
            "hop_duration_seconds": 0.4,
            "deployment_requirement": (
                "Use a fixed 25 ms scheduler. Do not rely on UART print time "
                "to create the sampling period."
            ),
        },
        "day11_cleaning_must_match": {
            "source_main_sha256": sha256_file(main_path),
            "source_qmi8658_sha256": sha256_file(qmi_path),
            "low_pass_alpha": 0.25,
            "gravity_alpha": 0.02,
            "acc_clip_integer_limit": 196140,
            "gyro_clip_integer_limit": 4000,
            "integer_to_model_scale": 0.001,
            "calibration": (
                "Keep the original Day11 qmi8658_init and first-100-sample "
                "software offset behavior unchanged."
            ),
            "critical_numeric_note": (
                "The captured acc_norm is numerically near 1.0 after dividing "
                "the CSV integer by 1000. The model follows that recorded "
                "numeric scale. Do not multiply model inputs by 9.807."
            ),
        },
        "stairs_to_walk_relabel": feature_report["stairs_to_walk_relabel"],
        "feature_pipeline": {
            "time_features": (
                "mean, std, RMS, min, max, peak-to-peak, mean absolute, "
                "mean absolute difference, zero-crossing rate"
            ),
            "rotation_invariants": (
                "vector norms, vector-delta norms, covariance eigenvalues, "
                "eigenvalue ratios, mean-vector norm, norm correlation"
            ),
            "frequency_features": (
                "64-point Hann-window RFFT at 40 Hz; DC removed; dominant "
                "frequency, centroid, entropy, three normalized band energies, "
                "low/high ratio, second-harmonic ratio"
            ),
            "preprocessing_order": (
                "extract full features -> select exact names -> clip -> "
                "normalize -> quantize to int8"
            ),
        },
        "int8_formula": {
            "input": "q = clamp(round(normalized / input_scale) + zero_point, -128, 127)",
            "output": "probability = (q - zero_point) * output_scale",
        },
    }


def generate_markdown_report(
    package_results: dict[str, dict],
    training: dict,
    tflite: dict,
    robustness: dict,
) -> str:
    lines = [
        "# Day16 最终模型设计与验证报告",
        "",
        "## 结论",
        "",
        "本次从 Day11 清洗数据重新完成了数据审计、窗口切分、两套特征工程、模型结构比较、时间块验证、INT8 量化和逐样本 TFLite 复核。",
        "训练、验证和测试按时间顺序切分，边界保留完整窗口隔离带，没有使用随机重叠窗口提高分数。",
        "",
        "| 模型 | 特征 | INT8大小 | Float测试准确率 | INT8测试准确率 | Keras/INT8一致率 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model_key in MODEL_KEYS:
        package = package_results[model_key]
        conversion = tflite[model_key]
        lines.append(
            "| {name} | {features} | {size} B | {float_acc:.2%} | "
            "{int8_acc:.2%} | {agreement:.2%} |".format(
                name=MODEL_CHINESE_NAMES[model_key],
                features=package["feature_count"],
                size=package["int8_tflite_bytes"],
                float_acc=conversion["float32_tflite_metrics"]["accuracy"],
                int8_acc=conversion["int8_tflite_metrics"]["accuracy"],
                agreement=conversion["keras_vs_int8_prediction_agreement"],
            )
        )
    lines.extend(
        [
            "",
            "## 数据处理",
            "",
            "- 仅使用 `*_clean.csv` 连续清洗数据，不使用稀疏 `raw.csv` 或板端简化 `window.csv`。",
            "- 统一插值到 40 Hz，窗口 64 点，窗口时长 1.6 秒，步长 16 点。",
            "- 自动检测到动作切换中心约为 `293968 ms`；`290768~297168 ms` 作为混合过渡区排除。",
            "- `297168 ms` 之后的用户确认尾段重标为 Walk，并以 2 倍硬样本权重参加训练。",
            "- 数据按 `idle_main`、`walk_main`、`stairs_core`、`stairs_tail_relabel_walk` 四个会话独立重采样，窗口不跨会话。",
            "- 时间域与频域均使用以模长、变化量和协方差特征值为主的旋转稳健特征。",
            "",
            "## 模型结果",
            "",
        ]
    )
    for model_key in MODEL_KEYS:
        test = training[model_key]["test_metrics"]
        sessions = robustness[model_key]["test_metrics_by_recording_session"]
        tail = robustness[model_key]["confirmed_walk_tail_after_transition"]
        lines.extend(
            [
                f"### {MODEL_CHINESE_NAMES[model_key]}",
                "",
                f"- 时间块测试准确率：{test['accuracy']:.2%}",
                f"- 时间块测试 Macro-F1：{test['macro_f1']:.2%}",
                f"- 静止 F1：{test['per_class']['idle']['f1']:.2%}",
                f"- 走路 F1：{test['per_class']['walk']['f1']:.2%}",
                f"- 上楼梯 F1：{test['per_class']['stairs']['f1']:.2%}",
                f"- 未参与训练的主 Walk 测试准确率：{sessions['walk_main']['accuracy']:.2%}",
                f"- 未参与训练的 Stairs 核心测试准确率：{sessions['stairs_core']['accuracy']:.2%}",
                f"- 已确认 Walk 尾段覆盖率：{tail['predicted_fractions']['walk']:.2%}（该尾段用于训练，不是独立泛化分数）",
                "",
            ]
        )
    lines.extend(
        [
            "## 必须保留的限制说明",
            "",
            "三类数据各只有一段连续录制，因此时间块测试仍然不是跨人员、跨天、跨安装位置验证。",
            "已确认 Walk 尾段作为训练硬样本后仍有部分窗口被判为 Stairs，说明现有特征空间中两类动作确实重叠。",
            "尾段覆盖率不能当作独立测试准确率；正式部署前仍应使用不同日期、不同握持方式的新数据做盲测。",
            "",
            "## 部署选择",
            "",
            "优先验证含频域 INT8 模型：它在主测试集和确认 Walk 尾段上的综合表现最好，但 MCU 端必须实现完全一致的频域特征与 FFT。",
            "无频域 INT8 模型更容易先完成端到端一致性验证，可作为板端基线和故障排查模型。",
            "",
            "## TFLite 量化复核",
            "",
            "- 两份模型均为全 INT8 输入和输出，类别顺序固定为 `idle, walk, stairs`。",
            "- 无频域模型文件 5840 B，含频域模型文件 6352 B。",
            "- Keras 与 INT8 TFLite 的测试预测一致率均为 99.73%。",
            "- 本轮只完成 TFLite 转换与逐样本复核；导入 STM32Cube.AI 后仍需重新生成并记录目标板 Flash、RAM 和算子报告。",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_to_simple_html(markdown: str) -> str:
    lines = markdown.splitlines()
    body: list[str] = []
    in_list = False
    in_table = False
    table_rows: list[list[str]] = []

    def flush_list() -> None:
        nonlocal in_list
        if in_list:
            body.append("</ul>")
            in_list = False

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not in_table:
            return
        body.append("<table>")
        for index, row in enumerate(table_rows):
            if index == 1 and all(set(cell) <= {"-", ":"} for cell in row):
                continue
            tag = "th" if index == 0 else "td"
            body.append(
                "<tr>"
                + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in row)
                + "</tr>"
            )
        body.append("</table>")
        in_table = False
        table_rows = []

    for line in lines:
        if line.startswith("|") and line.endswith("|"):
            flush_list()
            in_table = True
            table_rows.append([cell.strip() for cell in line.strip("|").split("|")])
            continue
        flush_table()
        if line.startswith("# "):
            flush_list()
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            flush_list()
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            flush_list()
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip():
            flush_list()
            body.append(f"<p>{html.escape(line)}</p>")
    flush_table()
    flush_list()
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day16 最终模型设计与验证报告</title>
<style>
body{font-family:"Microsoft YaHei",Arial,sans-serif;max-width:1100px;margin:0 auto;padding:32px;color:#1f2937;line-height:1.7}
h1{color:#0f4c81;border-bottom:4px solid #f58220;padding-bottom:12px}
h2{color:#0f4c81;margin-top:32px} h3{color:#2f6f9f}
table{border-collapse:collapse;width:100%;margin:18px 0}
th,td{border:1px solid #cbd5e1;padding:10px;text-align:left}
th{background:#eaf3f8} p,li{font-size:16px}
code{background:#eef2f7;padding:2px 5px;border-radius:3px}
</style></head><body>""" + "\n".join(body) + "</body></html>"


def main() -> None:
    args = parse_args()
    for name in (
        "day11_root",
        "audit_dir",
        "feature_dir",
        "training_dir",
        "validation_dir",
        "conversion_dir",
        "delivery_root",
    ):
        setattr(args, name, getattr(args, name).resolve())
    args.delivery_root.mkdir(parents=True, exist_ok=True)

    package_results = {
        model_key: build_model_package(model_key, args)
        for model_key in MODEL_KEYS
    }
    common_contract = build_common_contract(args)
    common_dir = args.delivery_root / "STM32部署参数"
    common_dir.mkdir(parents=True, exist_ok=True)
    write_json(common_dir / "deployment_contract.json", common_contract)
    write_json(common_dir / "label_map.json", {
        "0": "idle",
        "1": "walk",
        "2": "stairs",
    })
    (common_dir / "requirements.txt").write_text(
        "numpy==2.4.4\npandas==3.0.2\nmatplotlib==3.10.8\n"
        "tensorflow==2.21.0\n",
        encoding="ascii",
    )

    training = json.loads(
        (args.training_dir / "training_comparison.json").read_text(
            encoding="utf-8"
        )
    )
    tflite = json.loads(
        (args.conversion_dir / "tflite_comparison.json").read_text(
            encoding="utf-8"
        )
    )
    robustness = json.loads(
        (args.validation_dir / "robustness_validation.json").read_text(
            encoding="utf-8"
        )
    )
    report = generate_markdown_report(
        package_results,
        training,
        tflite,
        robustness,
    )
    report_dir = args.delivery_root / "验证报告"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "Day16_最终模型设计与验证报告.md").write_text(
        report,
        encoding="utf-8",
    )
    (report_dir / "Day16_最终模型设计与验证报告.html").write_text(
        markdown_to_simple_html(report),
        encoding="utf-8",
    )
    final_manifest = {
        "models": package_results,
        "recommended_model": "time_frequency",
        "recommended_file": (
            "模型B_含频域/model_int8.tflite"
        ),
        "baseline_model": "time_only",
        "baseline_file": "模型A_无频域/model_int8.tflite",
    }
    write_json(args.delivery_root / "FINAL_MANIFEST.json", final_manifest)
    print(json.dumps(final_manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
