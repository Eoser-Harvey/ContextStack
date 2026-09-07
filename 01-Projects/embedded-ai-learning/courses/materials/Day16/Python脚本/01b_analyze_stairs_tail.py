"""Locate the stairs-to-walk switch and build a conservative relabel plan."""

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
    PipelineConfig,
    extract_feature_table,
    feature_columns,
    load_all_clean_data,
    resample_clean_frame,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def robust_distance(
    matrix: np.ndarray,
    centroid: np.ndarray,
    scale: np.ndarray,
) -> np.ndarray:
    normalized = (matrix - centroid) / scale
    return np.sqrt(np.mean(normalized * normalized, axis=1))


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # Use the deployment hop so the change-point analysis sees the same
    # overlapping windows as the final model.
    config = PipelineConfig(hop_samples=16)
    frames = load_all_clean_data(args.data_root.resolve())
    walk = resample_clean_frame(frames["walk"], config)
    stairs = resample_clean_frame(frames["stairs"], config)

    walk_features = extract_feature_table(
        walk,
        config,
        include_frequency=True,
        split_name="all",
        source_class="walk",
    )
    stairs_features = extract_feature_table(
        stairs,
        config,
        include_frequency=True,
        split_name="all",
        source_class="stairs",
    )
    columns = feature_columns(walk_features)
    walk_matrix = walk_features[columns].to_numpy(dtype=np.float64)
    stairs_matrix = stairs_features[columns].to_numpy(dtype=np.float64)

    stairs_reference_count = int(len(stairs_matrix) * 0.60)
    stairs_reference = stairs_matrix[:stairs_reference_count]
    pooled = np.vstack((walk_matrix, stairs_reference))
    low = np.percentile(pooled, 1.0, axis=0)
    high = np.percentile(pooled, 99.0, axis=0)
    pooled_clipped = np.clip(pooled, low, high)
    scale = np.std(pooled_clipped, axis=0)
    scale[scale < 1e-6] = 1.0
    walk_centroid = np.mean(np.clip(walk_matrix, low, high), axis=0)
    stairs_centroid = np.mean(np.clip(stairs_reference, low, high), axis=0)
    stairs_clipped = np.clip(stairs_matrix, low, high)

    distance_walk = robust_distance(stairs_clipped, walk_centroid, scale)
    distance_stairs = robust_distance(stairs_clipped, stairs_centroid, scale)
    similarity_margin = distance_stairs - distance_walk
    smoothed = (
        pd.Series(similarity_margin)
        .rolling(window=25, center=True, min_periods=13)
        .median()
        .bfill()
        .ffill()
        .to_numpy()
    )

    minimum_index = int(len(smoothed) * 0.65)
    maximum_index = int(len(smoothed) * 0.95)
    candidate_indices = range(minimum_index, max(minimum_index + 1, maximum_index))
    best_index = minimum_index
    best_cost = float("inf")
    for index in candidate_indices:
        before = smoothed[:index]
        after = smoothed[index:]
        # Before should be stairs-like (negative), after should be walk-like (positive).
        cost = float(
            np.mean(np.maximum(before, 0.0) ** 2)
            + np.mean(np.maximum(-after, 0.0) ** 2)
        )
        if cost < best_cost:
            best_cost = cost
            best_index = index

    cutoff_ms = float(stairs_features["start_ms"].iloc[best_index])
    # A 3.2 s guard on each side is two complete 64-sample windows. Samples in
    # this interval are intentionally not assigned to either class.
    transition_guard_ms = 3200.0
    transition_start_ms = cutoff_ms - transition_guard_ms
    transition_end_ms = cutoff_ms + transition_guard_ms
    recording_start_ms = float(stairs_features["start_ms"].iloc[0])
    cutoff_seconds = (cutoff_ms - recording_start_ms) / 1000.0
    result = stairs_features[
        ["window_index", "start_ms", "end_ms"]
    ].copy()
    result["distance_to_walk"] = distance_walk
    result["distance_to_stairs_early"] = distance_stairs
    result["walk_similarity_margin"] = similarity_margin
    result["walk_similarity_margin_smoothed"] = smoothed
    result["region"] = np.select(
        (
            result["end_ms"] < transition_start_ms,
            result["start_ms"] >= transition_end_ms,
        ),
        ("stairs_core", "confirmed_walk_tail"),
        default="transition_excluded",
    )
    result.to_csv(
        output_dir / "stairs_tail_similarity.csv",
        index=False,
        encoding="utf-8-sig",
    )

    plt.figure(figsize=(12, 5))
    seconds = (
        result["start_ms"].to_numpy(dtype=np.float64) - recording_start_ms
    ) / 1000.0
    plt.plot(seconds, smoothed, color="#2878B5", label="walk similarity margin")
    plt.axhline(0.0, color="#333333", linewidth=1)
    plt.axvline(
        cutoff_seconds,
        color="#C44E52",
        linestyle="--",
        label=f"recommended cutoff: {cutoff_seconds:.1f}s",
    )
    plt.xlabel("Stairs recording time (seconds)")
    plt.ylabel("Positive means more walk-like")
    plt.title("Known mislabeled tail: robust feature similarity analysis")
    plt.grid(alpha=0.2)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "04_stairs_tail_similarity.png", dpi=180)
    plt.close()

    report = {
        "method": (
            "Compare rotation-robust time/frequency windows with the complete "
            "walk reference and the first 60% of the stairs recording. Search "
            "for one sustained tail boundary between 65% and 95% of the "
            "recording, then exclude a two-window guard on both sides."
        ),
        "recommended_cutoff_ms": cutoff_ms,
        "estimated_switch_center_ms": cutoff_ms,
        "transition_guard_ms_each_side": transition_guard_ms,
        "transition_start_ms": transition_start_ms,
        "transition_end_ms": transition_end_ms,
        "stairs_keep_before_ms": transition_start_ms,
        "relabel_walk_from_ms": transition_end_ms,
        "recommended_cutoff_seconds_from_recording_start": cutoff_seconds,
        "windows_before_cutoff": best_index,
        "windows_at_or_after_cutoff": int(len(result) - best_index),
        "stairs_core_windows": int(np.sum(result["region"] == "stairs_core")),
        "transition_excluded_windows": int(
            np.sum(result["region"] == "transition_excluded")
        ),
        "confirmed_walk_tail_windows": int(
            np.sum(result["region"] == "confirmed_walk_tail")
        ),
        "optimization_cost": best_cost,
        "note": (
            "The user confirmed that the end of the stairs recording is walk. "
            "Only the stable tail after the transition guard is relabeled as "
            "walk; mixed transition windows are excluded."
        ),
    }
    write_json(output_dir / "stairs_tail_cutoff.json", report)
    write_json(output_dir / "stairs_to_walk_relabel_plan.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
