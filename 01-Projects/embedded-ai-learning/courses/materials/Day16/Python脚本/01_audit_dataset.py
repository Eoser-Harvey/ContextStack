"""Audit Day11 clean CSV files before any model training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pipeline_common import (
    CLASS_NAMES,
    PipelineConfig,
    build_sha256_manifest,
    load_all_clean_data,
    resample_clean_frame,
    timestamp_diagnostics,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-rate", type=float, default=40.0)
    return parser.parse_args()


def rolling_activity(frame: pd.DataFrame, sample_rate_hz: float) -> pd.DataFrame:
    block = max(1, int(round(sample_rate_hz)))
    records: list[dict[str, object]] = []
    for start in range(0, len(frame) - block + 1, block):
        part = frame.iloc[start : start + block]
        lin_norm = part["lin_norm"].to_numpy(dtype=np.float64)
        gyro_norm = part["gyro_norm"].to_numpy(dtype=np.float64)
        records.append(
            {
                "second_index": len(records),
                "start_ms": float(part["t_ms"].iloc[0]),
                "end_ms": float(part["t_ms"].iloc[-1]),
                "lin_norm_rms": float(np.sqrt(np.mean(lin_norm * lin_norm))),
                "gyro_norm_rms": float(
                    np.sqrt(np.mean(gyro_norm * gyro_norm))
                ),
                "lin_norm_mean_abs_diff": float(
                    np.mean(np.abs(np.diff(lin_norm)))
                ),
                "gyro_norm_mean_abs_diff": float(
                    np.mean(np.abs(np.diff(gyro_norm)))
                ),
            }
        )
    result = pd.DataFrame(records)
    result["activity_score"] = (
        result["lin_norm_rms"]
        + 0.60 * result["gyro_norm_rms"]
        + 1.50 * result["lin_norm_mean_abs_diff"]
        + 0.80 * result["gyro_norm_mean_abs_diff"]
    )
    return result


def make_plots(
    summary: pd.DataFrame,
    activity: pd.DataFrame,
    output_dir: Path,
) -> None:
    plt.figure(figsize=(9, 5))
    plt.bar(summary["class"], summary["duration_seconds"], color="#2878B5")
    plt.ylabel("Duration (seconds)")
    plt.title("Day16 source recording duration")
    plt.tight_layout()
    plt.savefig(output_dir / "01_recording_duration.png", dpi=180)
    plt.close()

    figure, axes = plt.subplots(len(CLASS_NAMES), 1, figsize=(12, 9), sharex=False)
    for axis, class_name in zip(axes, CLASS_NAMES):
        subset = activity[activity["class"] == class_name]
        axis.plot(
            subset["second_index"],
            subset["activity_score"],
            color="#D95319",
            linewidth=1.2,
        )
        axis.set_title(class_name)
        axis.set_ylabel("activity")
        axis.grid(alpha=0.25)
    axes[-1].set_xlabel("Recording time (seconds)")
    figure.suptitle("One-second activity score over time")
    figure.tight_layout()
    figure.savefig(output_dir / "02_activity_timeline.png", dpi=180)
    plt.close(figure)

    plt.figure(figsize=(9, 5))
    values = [
        activity.loc[activity["class"] == name, "activity_score"].to_numpy()
        for name in CLASS_NAMES
    ]
    plt.boxplot(values, tick_labels=CLASS_NAMES, showfliers=False)
    plt.ylabel("Activity score")
    plt.title("Activity distribution by source folder")
    plt.tight_layout()
    plt.savefig(output_dir / "03_activity_distribution.png", dpi=180)
    plt.close()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = PipelineConfig(target_sample_rate_hz=args.sample_rate)

    build_sha256_manifest(
        args.snapshot_root.resolve(),
        args.snapshot_root.resolve() / "SHA256_manifest.csv",
    )
    source_frames = load_all_clean_data(args.data_root.resolve())

    summary_records: list[dict[str, object]] = []
    quality_records: list[dict[str, object]] = []
    activity_frames: list[pd.DataFrame] = []
    resampled_frames: dict[str, pd.DataFrame] = {}

    for class_name in CLASS_NAMES:
        source = source_frames[class_name]
        diagnostics = timestamp_diagnostics(source)
        valid_rows = int(
            ((source["valid"].astype(int) == 1) & (source["clipped"] == 0)).sum()
        )
        summary_records.append(
            {
                "class": class_name,
                **diagnostics,
                "valid_unclipped_rows": valid_rows,
                "valid_unclipped_fraction": valid_rows / len(source),
            }
        )

        delta = np.diff(source["t_ms"].to_numpy(dtype=np.float64))
        for name, predicate in (
            ("non_increasing", delta <= 0),
            ("gap_over_100ms", delta > 100),
            ("period_below_15ms", (delta > 0) & (delta < 15)),
            ("period_above_40ms", delta > 40),
        ):
            quality_records.append(
                {
                    "class": class_name,
                    "check": name,
                    "count": int(np.sum(predicate)),
                }
            )

        resampled = resample_clean_frame(source, config)
        resampled_frames[class_name] = resampled
        per_second = rolling_activity(
            resampled,
            config.target_sample_rate_hz,
        )
        per_second.insert(0, "class", class_name)
        activity_frames.append(per_second)

    summary = pd.DataFrame(summary_records)
    quality = pd.DataFrame(quality_records)
    activity = pd.concat(activity_frames, ignore_index=True)
    summary.to_csv(output_dir / "dataset_summary.csv", index=False, encoding="utf-8-sig")
    quality.to_csv(
        output_dir / "timestamp_quality_checks.csv",
        index=False,
        encoding="utf-8-sig",
    )
    activity.to_csv(
        output_dir / "one_second_activity.csv",
        index=False,
        encoding="utf-8-sig",
    )
    for class_name, frame in resampled_frames.items():
        frame.to_csv(
            output_dir / f"{class_name}_resampled_40hz.csv",
            index=False,
            encoding="utf-8-sig",
        )

    idle_scores = activity.loc[
        activity["class"] == "idle",
        "activity_score",
    ].to_numpy(dtype=np.float64)
    thresholds = {
        "idle_activity_score_p95": float(np.percentile(idle_scores, 95)),
        "idle_activity_score_p99": float(np.percentile(idle_scores, 99)),
        "idle_activity_score_max": float(np.max(idle_scores)),
        "recommended_dynamic_floor": float(np.percentile(idle_scores, 99)),
    }
    write_json(output_dir / "activity_thresholds.json", thresholds)
    write_json(output_dir / "pipeline_config_initial.json", config.to_dict())
    make_plots(summary, activity, output_dir)

    report = {
        "config": config.to_dict(),
        "dataset_summary": json.loads(summary.to_json(orient="records")),
        "quality_checks": json.loads(quality.to_json(orient="records")),
        "activity_thresholds": thresholds,
        "important_input_contract": {
            "training_source": "*_clean.csv only",
            "linear_acceleration": (
                "Day11 low-pass acceleration minus Day11 gravity estimate"
            ),
            "gyroscope": "Day11 low-pass gyroscope",
            "scale": "CSV integer columns are divided by 1000.0",
            "resampling": "linear interpolation to an exact 40 Hz timeline",
            "raw_csv_not_used": (
                "raw files are sparse and are not the stream consumed by the model"
            ),
            "window_csv_not_used": (
                "window files contain only a small fixed summary and cannot "
                "support the two requested feature sets"
            ),
        },
    }
    write_json(output_dir / "dataset_audit_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
