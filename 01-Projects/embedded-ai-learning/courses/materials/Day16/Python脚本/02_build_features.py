"""Build leakage-resistant time and frequency feature datasets."""

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
    calculate_activity_score,
    extract_feature_table,
    feature_columns,
    load_all_clean_data,
    resample_clean_frame,
    split_frame_by_time,
    write_json,
)

HARD_WALK_REPLAY_FACTOR = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-rate", type=float, default=40.0)
    parser.add_argument("--window-samples", type=int, default=64)
    parser.add_argument("--hop-samples", type=int, default=16)
    parser.add_argument("--stairs-cutoff-json", type=Path, required=True)
    return parser.parse_args()


def save_npz(
    table: pd.DataFrame,
    columns: list[str],
    output_path: Path,
) -> None:
    arrays: dict[str, np.ndarray] = {
        "feature_names": np.asarray(columns),
        "class_names": np.asarray(CLASS_NAMES),
    }
    for split_name in ("train", "validation", "test"):
        subset = table[
            (table["split"] == split_name)
            & (table["quality_decision"] == "keep")
        ].copy()
        if split_name == "train":
            hard_walk = subset[
                subset["source_class"] == "stairs_tail_relabel_walk"
            ]
            if not hard_walk.empty:
                subset = pd.concat(
                    [subset]
                    + [hard_walk.copy() for _ in range(HARD_WALK_REPLAY_FACTOR - 1)],
                    ignore_index=True,
                )
        arrays[f"x_{split_name}"] = subset[columns].to_numpy(dtype=np.float32)
        arrays[f"y_{split_name}"] = subset["label_id"].to_numpy(dtype=np.int64)
        arrays[f"start_ms_{split_name}"] = subset["start_ms"].to_numpy(
            dtype=np.float64
        )
        arrays[f"source_class_{split_name}"] = subset[
            "source_class"
        ].astype(str).to_numpy(dtype=str)
    np.savez_compressed(output_path, **arrays)


def plot_pca(
    table: pd.DataFrame,
    columns: list[str],
    output_path: Path,
    title: str,
) -> None:
    subset = table[table["quality_decision"] == "keep"].copy()
    matrix = subset[columns].to_numpy(dtype=np.float64)
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std[std < 1e-8] = 1.0
    normalized = (matrix - mean) / std
    _, _, right = np.linalg.svd(normalized, full_matrices=False)
    projected = normalized @ right[:2].T

    plt.figure(figsize=(9, 7))
    colors = {"idle": "#2878B5", "walk": "#F39C12", "stairs": "#C44E52"}
    for class_name in CLASS_NAMES:
        mask = subset["label"].to_numpy() == class_name
        plt.scatter(
            projected[mask, 0],
            projected[mask, 1],
            s=13,
            alpha=0.55,
            label=class_name,
            color=colors[class_name],
        )
    plt.xlabel("PCA component 1")
    plt.ylabel("PCA component 2")
    plt.title(title)
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_activity_by_split(table: pd.DataFrame, output_path: Path) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=True)
    for axis, split_name in zip(axes, ("train", "validation", "test")):
        values = [
            table.loc[
                (table["split"] == split_name) & (table["label"] == class_name),
                "activity_score",
            ].to_numpy()
            for class_name in CLASS_NAMES
        ]
        axis.boxplot(values, tick_labels=CLASS_NAMES, showfliers=False)
        axis.set_title(split_name)
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Activity score")
    figure.suptitle("Window activity distributions after chronological split")
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = PipelineConfig(
        target_sample_rate_hz=args.sample_rate,
        window_samples=args.window_samples,
        hop_samples=args.hop_samples,
        split_guard_samples=args.window_samples,
    )

    source_frames = load_all_clean_data(args.data_root.resolve())
    cutoff_payload = json.loads(
        args.stairs_cutoff_json.resolve().read_text(encoding="utf-8")
    )
    transition_start_ms = float(cutoff_payload["transition_start_ms"])
    transition_end_ms = float(cutoff_payload["transition_end_ms"])
    stairs_original_rows = len(source_frames["stairs"])
    stairs_core = source_frames["stairs"][
        source_frames["stairs"]["t_ms"] < transition_start_ms
    ].reset_index(drop=True)
    confirmed_walk_tail = source_frames["stairs"][
        source_frames["stairs"]["t_ms"] >= transition_end_ms
    ].copy()
    confirmed_walk_tail["label_id"] = 1
    confirmed_walk_tail["label"] = "walk"
    confirmed_walk_tail = confirmed_walk_tail.reset_index(drop=True)
    transition_rows = int(
        (
            (source_frames["stairs"]["t_ms"] >= transition_start_ms)
            & (source_frames["stairs"]["t_ms"] < transition_end_ms)
        ).sum()
    )
    sessions = (
        ("idle_main", "idle", source_frames["idle"]),
        ("walk_main", "walk", source_frames["walk"]),
        ("stairs_core", "stairs", stairs_core),
        ("stairs_tail_relabel_walk", "walk", confirmed_walk_tail),
    )
    time_tables: list[pd.DataFrame] = []
    frequency_tables: list[pd.DataFrame] = []
    split_records: list[dict[str, object]] = []

    for session_name, class_name, session_frame in sessions:
        resampled = resample_clean_frame(session_frame, config)
        if session_name == "stairs_tail_relabel_walk":
            # The tail is a small, user-confirmed hard example. Use all of it
            # for training and assess generalization only on untouched parts
            # of walk_main and stairs_core.
            split_frames = {"train": resampled}
        else:
            split_frames = split_frame_by_time(resampled, config)
        for split_name, split_frame in split_frames.items():
            split_records.append(
                {
                    "session": session_name,
                    "class": class_name,
                    "split": split_name,
                    "samples": int(len(split_frame)),
                    "start_ms": float(split_frame["t_ms"].iloc[0]),
                    "end_ms": float(split_frame["t_ms"].iloc[-1]),
                    "duration_seconds": float(
                        (
                            split_frame["t_ms"].iloc[-1]
                            - split_frame["t_ms"].iloc[0]
                        )
                        / 1000.0
                    ),
                }
            )
            time_tables.append(
                extract_feature_table(
                    split_frame,
                    config,
                    include_frequency=False,
                    split_name=split_name,
                    source_class=session_name,
                )
            )
            frequency_tables.append(
                extract_feature_table(
                    split_frame,
                    config,
                    include_frequency=True,
                    split_name=split_name,
                    source_class=session_name,
                )
            )

    time_table = pd.concat(time_tables, ignore_index=True)
    frequency_table = pd.concat(frequency_tables, ignore_index=True)
    time_table["activity_score"] = calculate_activity_score(time_table)
    frequency_table["activity_score"] = time_table["activity_score"].to_numpy()

    idle_train_scores = time_table.loc[
        (time_table["split"] == "train") & (time_table["label"] == "idle"),
        "activity_score",
    ].to_numpy(dtype=np.float64)
    dynamic_floor = float(np.percentile(idle_train_scores, 99))
    for table in (time_table, frequency_table):
        keep = (table["label"] == "idle") | (
            table["activity_score"] >= dynamic_floor
        )
        table["quality_decision"] = np.where(
            keep,
            "keep",
            "drop_dynamic_below_idle_p99",
        )

    time_columns = feature_columns(time_table)
    frequency_columns = feature_columns(frequency_table)
    if frequency_columns[: len(time_columns)] != time_columns:
        raise RuntimeError("Frequency table does not begin with time features")

    time_table.to_csv(
        output_dir / "features_time_only_all_windows.csv",
        index=False,
        encoding="utf-8-sig",
    )
    frequency_table.to_csv(
        output_dir / "features_time_frequency_all_windows.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(split_records).to_csv(
        output_dir / "chronological_split_manifest.csv",
        index=False,
        encoding="utf-8-sig",
    )
    (output_dir / "feature_names_time_only.txt").write_text(
        "\n".join(time_columns) + "\n",
        encoding="utf-8",
    )
    (output_dir / "feature_names_time_frequency.txt").write_text(
        "\n".join(frequency_columns) + "\n",
        encoding="utf-8",
    )
    save_npz(
        time_table,
        time_columns,
        output_dir / "dataset_time_only.npz",
    )
    save_npz(
        frequency_table,
        frequency_columns,
        output_dir / "dataset_time_frequency.npz",
    )

    counts = (
        time_table.groupby(
            ["split", "label", "quality_decision"],
            observed=True,
        )
        .size()
        .reset_index(name="windows")
    )
    counts.to_csv(
        output_dir / "window_counts.csv",
        index=False,
        encoding="utf-8-sig",
    )
    report = {
        "config": config.to_dict(),
        "time_only_feature_count": len(time_columns),
        "time_frequency_feature_count": len(frequency_columns),
        "frequency_feature_count": len(frequency_columns) - len(time_columns),
        "dynamic_activity_floor": dynamic_floor,
        "quality_rule": (
            "Keep every idle window. Drop a walk/stairs window only when its "
            "activity score is below the 99th percentile of training idle."
        ),
        "split_rule": (
            "Chronological 60/20/20 split inside each independent recording "
            "session, with one full 64-sample guard on both sides of every "
            "boundary. The confirmed short walk tail is training-only hard "
            "data and is replayed four times. Windows never cross sessions "
            "or split boundaries."
        ),
        "hard_walk_replay_factor": HARD_WALK_REPLAY_FACTOR,
        "window_counts": json.loads(counts.to_json(orient="records")),
        "stairs_to_walk_relabel": {
            "estimated_switch_center_ms": float(
                cutoff_payload["estimated_switch_center_ms"]
            ),
            "transition_start_ms": transition_start_ms,
            "transition_end_ms": transition_end_ms,
            "original_rows": stairs_original_rows,
            "stairs_core_rows": int(len(stairs_core)),
            "transition_excluded_rows": transition_rows,
            "tail_relabelled_as_walk_rows": int(len(confirmed_walk_tail)),
            "reason": (
                "The user confirmed that the end of the stairs recording is "
                "walking. Mixed switch windows are excluded and only the "
                "stable tail is relabeled as walk."
            ),
        },
    }
    write_json(output_dir / "feature_dataset_report.json", report)
    write_json(output_dir / "pipeline_config.json", config.to_dict())
    plot_pca(
        time_table,
        time_columns,
        output_dir / "01_pca_time_only.png",
        "Time-domain feature space",
    )
    plot_pca(
        frequency_table,
        frequency_columns,
        output_dir / "02_pca_time_frequency.png",
        "Time and frequency feature space",
    )
    plot_activity_by_split(
        time_table,
        output_dir / "03_activity_by_split.png",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
