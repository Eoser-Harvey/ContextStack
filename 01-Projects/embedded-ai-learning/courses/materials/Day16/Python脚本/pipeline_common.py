"""Shared, deployment-oriented utilities for the Day16 action models."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


CLASS_NAMES = ("idle", "walk", "stairs")
CLASS_TO_ID = {name: index for index, name in enumerate(CLASS_NAMES)}

CLEAN_COLUMNS = (
    "t_ms",
    "label_id",
    "label",
    "lin_ax_mps2_x1000",
    "lin_ay_mps2_x1000",
    "lin_az_mps2_x1000",
    "gx_radps_x1000",
    "gy_radps_x1000",
    "gz_radps_x1000",
    "acc_norm_x1000",
    "gyro_norm_x1000",
    "valid",
    "clipped",
)

BASE_CHANNELS = (
    "lin_norm",
    "gyro_norm",
    "acc_norm_centered",
    "lin_delta_norm",
    "gyro_delta_norm",
)

FREQUENCY_CHANNELS = (
    "lin_norm",
    "gyro_norm",
    "lin_delta_norm",
    "gyro_delta_norm",
)

TIME_STAT_NAMES = (
    "mean",
    "std",
    "rms",
    "min",
    "max",
    "peak_to_peak",
    "mean_abs",
    "mean_abs_diff",
    "zero_crossing_rate",
)

FREQUENCY_STAT_NAMES = (
    "dominant_frequency_hz",
    "spectral_centroid_hz",
    "spectral_entropy",
    "band_energy_0p3_1p5",
    "band_energy_1p5_3p0",
    "band_energy_3p0_8p0",
    "low_high_energy_ratio",
    "second_harmonic_ratio",
)

@dataclass(frozen=True)
class PipelineConfig:
    target_sample_rate_hz: float = 40.0
    window_samples: int = 64
    hop_samples: int = 16
    train_fraction: float = 0.60
    validation_fraction: float = 0.20
    test_fraction: float = 0.20
    split_guard_samples: int = 64
    random_seed: int = 20260723
    valid_required: int = 1
    max_clipped: int = 0

    @property
    def target_period_ms(self) -> float:
        return 1000.0 / self.target_sample_rate_hz

    def to_dict(self) -> dict[str, object]:
        return {
            "target_sample_rate_hz": self.target_sample_rate_hz,
            "target_period_ms": self.target_period_ms,
            "window_samples": self.window_samples,
            "window_duration_seconds": self.window_samples
            / self.target_sample_rate_hz,
            "hop_samples": self.hop_samples,
            "hop_duration_seconds": self.hop_samples
            / self.target_sample_rate_hz,
            "train_fraction": self.train_fraction,
            "validation_fraction": self.validation_fraction,
            "test_fraction": self.test_fraction,
            "split_guard_samples": self.split_guard_samples,
            "random_seed": self.random_seed,
            "valid_required": self.valid_required,
            "max_clipped": self.max_clipped,
        }


def set_global_determinism(seed: int) -> None:
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf

        tf.keras.utils.set_random_seed(seed)
        tf.config.experimental.enable_op_determinism()
    except (ImportError, RuntimeError):
        pass


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_sha256_manifest(root: Path, output_path: Path) -> None:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() == output_path.resolve():
            continue
        records.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("relative_path", "bytes", "sha256"),
        )
        writer.writeheader()
        writer.writerows(records)


def find_clean_csv_files(data_root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for class_name in CLASS_NAMES:
        candidates = sorted((data_root / class_name).glob("*_clean.csv"))
        if len(candidates) != 1:
            raise ValueError(
                f"Expected exactly one *_clean.csv for {class_name}, "
                f"found {len(candidates)} in {data_root / class_name}"
            )
        files[class_name] = candidates[0]
    return files


def load_clean_csv(path: Path, expected_class: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [column for column in CLEAN_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    frame = frame.loc[:, CLEAN_COLUMNS].copy()

    numeric_columns = [column for column in CLEAN_COLUMNS if column != "label"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if frame[numeric_columns].isna().any().any():
        bad_rows = int(frame[numeric_columns].isna().any(axis=1).sum())
        raise ValueError(f"{path} has {bad_rows} rows with non-numeric values")
    if set(frame["label"].astype(str).str.lower().unique()) != {expected_class}:
        raise ValueError(f"{path} contains labels other than {expected_class}")
    if set(frame["label_id"].astype(int).unique()) != {
        CLASS_TO_ID[expected_class]
    }:
        raise ValueError(f"{path} has an unexpected label_id")

    frame["source_row"] = np.arange(len(frame), dtype=np.int64)
    frame["label"] = expected_class
    frame["label_id"] = CLASS_TO_ID[expected_class]
    return frame


def load_all_clean_data(data_root: Path) -> dict[str, pd.DataFrame]:
    files = find_clean_csv_files(data_root)
    return {
        class_name: load_clean_csv(path, class_name)
        for class_name, path in files.items()
    }


def timestamp_diagnostics(frame: pd.DataFrame) -> dict[str, object]:
    timestamps = frame["t_ms"].to_numpy(dtype=np.float64)
    delta = np.diff(timestamps)
    positive = delta[delta > 0]
    return {
        "rows": int(len(frame)),
        "start_ms": int(timestamps[0]),
        "end_ms": int(timestamps[-1]),
        "duration_seconds": float((timestamps[-1] - timestamps[0]) / 1000.0),
        "non_increasing_steps": int(np.sum(delta <= 0)),
        "gaps_over_100ms": int(np.sum(delta > 100.0)),
        "median_period_ms": float(np.median(positive)) if positive.size else None,
        "mean_period_ms": float(np.mean(positive)) if positive.size else None,
        "p01_period_ms": float(np.percentile(positive, 1))
        if positive.size
        else None,
        "p99_period_ms": float(np.percentile(positive, 99))
        if positive.size
        else None,
        "effective_rate_hz": float(1000.0 / np.median(positive))
        if positive.size
        else None,
    }


def split_continuous_segments(
    frame: pd.DataFrame,
    max_gap_ms: float = 100.0,
) -> list[pd.DataFrame]:
    timestamps = frame["t_ms"].to_numpy(dtype=np.float64)
    delta = np.diff(timestamps)
    boundaries = np.flatnonzero((delta <= 0) | (delta > max_gap_ms)) + 1
    segments = np.split(np.arange(len(frame)), boundaries)
    return [frame.iloc[index].reset_index(drop=True) for index in segments if len(index)]


def _interpolate_column(
    source_time_ms: np.ndarray,
    values: np.ndarray,
    target_time_ms: np.ndarray,
) -> np.ndarray:
    return np.interp(target_time_ms, source_time_ms, values)


def resample_clean_frame(
    frame: pd.DataFrame,
    config: PipelineConfig,
) -> pd.DataFrame:
    valid = frame[
        (frame["valid"].astype(int) == config.valid_required)
        & (frame["clipped"].astype(int) <= config.max_clipped)
    ].copy()
    if len(valid) < config.window_samples:
        raise ValueError("Not enough valid samples after quality filtering")

    output_frames: list[pd.DataFrame] = []
    segment_id = 0
    value_columns = (
        "lin_ax_mps2_x1000",
        "lin_ay_mps2_x1000",
        "lin_az_mps2_x1000",
        "gx_radps_x1000",
        "gy_radps_x1000",
        "gz_radps_x1000",
        "acc_norm_x1000",
        "gyro_norm_x1000",
    )
    for segment in split_continuous_segments(valid):
        if len(segment) < config.window_samples:
            continue
        source_time = segment["t_ms"].to_numpy(dtype=np.float64)
        target_time = np.arange(
            source_time[0],
            source_time[-1] + config.target_period_ms * 0.25,
            config.target_period_ms,
            dtype=np.float64,
        )
        if len(target_time) < config.window_samples:
            continue

        payload: dict[str, object] = {
            "t_ms": target_time,
            "label_id": np.full(len(target_time), int(segment["label_id"].iloc[0])),
            "label": np.full(len(target_time), str(segment["label"].iloc[0])),
            "segment_id": np.full(len(target_time), segment_id),
        }
        for column in value_columns:
            payload[column] = _interpolate_column(
                source_time,
                segment[column].to_numpy(dtype=np.float64),
                target_time,
            )
        output_frames.append(pd.DataFrame(payload))
        segment_id += 1

    if not output_frames:
        raise ValueError("No continuous segment is long enough for one window")
    result = pd.concat(output_frames, ignore_index=True)
    return add_model_channels(result)


def add_model_channels(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    scale = 1.0 / 1000.0
    result["lin_x"] = result["lin_ax_mps2_x1000"] * scale
    result["lin_y"] = result["lin_ay_mps2_x1000"] * scale
    result["lin_z"] = result["lin_az_mps2_x1000"] * scale
    result["gyro_x"] = result["gx_radps_x1000"] * scale
    result["gyro_y"] = result["gy_radps_x1000"] * scale
    result["gyro_z"] = result["gz_radps_x1000"] * scale
    result["lin_norm"] = np.sqrt(
        result["lin_x"] ** 2 + result["lin_y"] ** 2 + result["lin_z"] ** 2
    )
    result["gyro_norm"] = np.sqrt(
        result["gyro_x"] ** 2
        + result["gyro_y"] ** 2
        + result["gyro_z"] ** 2
    )
    result["acc_norm_centered"] = result["acc_norm_x1000"] * scale - 1.0
    linear = result[["lin_x", "lin_y", "lin_z"]].to_numpy(dtype=np.float64)
    gyro = result[["gyro_x", "gyro_y", "gyro_z"]].to_numpy(dtype=np.float64)
    linear_delta = np.diff(linear, axis=0, prepend=linear[[0], :])
    gyro_delta = np.diff(gyro, axis=0, prepend=gyro[[0], :])
    result["lin_delta_norm"] = np.linalg.norm(linear_delta, axis=1)
    result["gyro_delta_norm"] = np.linalg.norm(gyro_delta, axis=1)
    return result


def split_frame_by_time(
    frame: pd.DataFrame,
    config: PipelineConfig,
) -> dict[str, pd.DataFrame]:
    if not np.isclose(
        config.train_fraction
        + config.validation_fraction
        + config.test_fraction,
        1.0,
    ):
        raise ValueError("Train, validation, and test fractions must sum to 1")

    n = len(frame)
    train_end = int(n * config.train_fraction)
    validation_end = int(
        n * (config.train_fraction + config.validation_fraction)
    )
    guard = config.split_guard_samples
    ranges = {
        "train": (0, max(0, train_end - guard)),
        "validation": (
            min(n, train_end + guard),
            max(min(n, train_end + guard), validation_end - guard),
        ),
        "test": (min(n, validation_end + guard), n),
    }
    output: dict[str, pd.DataFrame] = {}
    for split_name, (start, end) in ranges.items():
        subset = frame.iloc[start:end].reset_index(drop=True)
        if len(subset) < config.window_samples:
            raise ValueError(
                f"{split_name} split has only {len(subset)} samples after guard"
            )
        output[split_name] = subset
    return output


def _safe_correlation(x: np.ndarray, y: np.ndarray) -> float:
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)
    denominator = np.sqrt(
        np.sum(x_centered * x_centered)
        * np.sum(y_centered * y_centered)
    )
    if denominator <= 1e-12:
        return 0.0
    return float(np.sum(x_centered * y_centered) / denominator)


def extract_time_features(
    window: pd.DataFrame,
) -> tuple[list[str], np.ndarray]:
    names: list[str] = []
    values: list[float] = []
    for channel in BASE_CHANNELS:
        x = window[channel].to_numpy(dtype=np.float64)
        centered = x - np.mean(x)
        signs = centered >= 0.0
        stats = (
            float(np.mean(x)),
            float(np.std(x)),
            float(np.sqrt(np.mean(x * x))),
            float(np.min(x)),
            float(np.max(x)),
            float(np.max(x) - np.min(x)),
            float(np.mean(np.abs(x))),
            float(np.mean(np.abs(np.diff(x)))) if len(x) > 1 else 0.0,
            float(np.mean(signs[1:] != signs[:-1])) if len(x) > 1 else 0.0,
        )
        for stat_name, value in zip(TIME_STAT_NAMES, stats):
            names.append(f"{channel}__{stat_name}")
            values.append(value)

    for prefix, columns in (
        ("lin", ("lin_x", "lin_y", "lin_z")),
        ("gyro", ("gyro_x", "gyro_y", "gyro_z")),
    ):
        vectors = window.loc[:, columns].to_numpy(dtype=np.float64)
        covariance = np.cov(vectors, rowvar=False, bias=True)
        eigenvalues = np.linalg.eigvalsh(covariance)[::-1]
        eigenvalues = np.maximum(eigenvalues, 0.0)
        for index, eigenvalue in enumerate(eigenvalues):
            names.append(f"{prefix}_covariance_eigenvalue_{index}")
            values.append(float(eigenvalue))
        principal = max(float(eigenvalues[0]), 1e-12)
        names.append(f"{prefix}_covariance_ratio_1_to_0")
        values.append(float(eigenvalues[1] / principal))
        names.append(f"{prefix}_covariance_ratio_2_to_0")
        values.append(float(eigenvalues[2] / principal))
        names.append(f"{prefix}_mean_vector_norm")
        values.append(float(np.linalg.norm(np.mean(vectors, axis=0))))

    names.append("corr__lin_norm__gyro_norm")
    values.append(
        _safe_correlation(
            window["lin_norm"].to_numpy(dtype=np.float64),
            window["gyro_norm"].to_numpy(dtype=np.float64),
        )
    )
    return names, np.asarray(values, dtype=np.float32)


def _band_energy(
    frequencies: np.ndarray,
    power: np.ndarray,
    low_hz: float,
    high_hz: float,
) -> float:
    mask = (frequencies >= low_hz) & (frequencies < high_hz)
    return float(np.sum(power[mask]))


def extract_frequency_features(
    window: pd.DataFrame,
    sample_rate_hz: float,
) -> tuple[list[str], np.ndarray]:
    names: list[str] = []
    values: list[float] = []
    n = len(window)
    taper = np.hanning(n)
    frequencies = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)

    for channel in FREQUENCY_CHANNELS:
        x = window[channel].to_numpy(dtype=np.float64)
        spectrum = np.fft.rfft((x - np.mean(x)) * taper)
        power = np.abs(spectrum) ** 2
        power[0] = 0.0
        total_power = float(np.sum(power))
        if total_power <= 1e-20:
            stats = (0.0,) * len(FREQUENCY_STAT_NAMES)
        else:
            dominant_index = int(np.argmax(power))
            dominant_frequency = float(frequencies[dominant_index])
            centroid = float(np.sum(frequencies * power) / total_power)
            probability = power / total_power
            nonzero = probability[probability > 0.0]
            entropy = float(
                -np.sum(nonzero * np.log(nonzero))
                / np.log(max(2, len(probability) - 1))
            )
            low = _band_energy(frequencies, power, 0.3, 1.5)
            middle = _band_energy(frequencies, power, 1.5, 3.0)
            high = _band_energy(frequencies, power, 3.0, 8.0)
            low_high_ratio = float((low + middle) / (high + 1e-12))

            second_harmonic_frequency = 2.0 * dominant_frequency
            if second_harmonic_frequency <= frequencies[-1]:
                second_index = int(
                    np.argmin(np.abs(frequencies - second_harmonic_frequency))
                )
                harmonic_ratio = float(
                    power[second_index] / (power[dominant_index] + 1e-12)
                )
            else:
                harmonic_ratio = 0.0
            stats = (
                dominant_frequency,
                centroid,
                entropy,
                low / total_power,
                middle / total_power,
                high / total_power,
                low_high_ratio,
                harmonic_ratio,
            )

        for stat_name, value in zip(FREQUENCY_STAT_NAMES, stats):
            names.append(f"{channel}__{stat_name}")
            values.append(value)
    return names, np.asarray(values, dtype=np.float32)


def iter_windows(
    frame: pd.DataFrame,
    config: PipelineConfig,
) -> Iterable[tuple[int, pd.DataFrame]]:
    for segment_id in sorted(frame["segment_id"].unique()):
        segment = frame[frame["segment_id"] == segment_id].reset_index(drop=True)
        stop = len(segment) - config.window_samples + 1
        for start in range(0, max(0, stop), config.hop_samples):
            yield start, segment.iloc[start : start + config.window_samples]


def extract_feature_table(
    frame: pd.DataFrame,
    config: PipelineConfig,
    include_frequency: bool,
    split_name: str,
    source_class: str,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    expected_names: list[str] | None = None
    for window_index, (_, window) in enumerate(iter_windows(frame, config)):
        time_names, time_values = extract_time_features(window)
        names = list(time_names)
        values = list(time_values)
        if include_frequency:
            frequency_names, frequency_values = extract_frequency_features(
                window,
                config.target_sample_rate_hz,
            )
            names.extend(frequency_names)
            values.extend(frequency_values)
        if expected_names is None:
            expected_names = names
        elif names != expected_names:
            raise RuntimeError("Feature order changed between windows")

        record: dict[str, object] = {
            "split": split_name,
            "source_class": source_class,
            "label_id": int(window["label_id"].iloc[0]),
            "label": str(window["label"].iloc[0]),
            "window_index": window_index,
            "start_ms": float(window["t_ms"].iloc[0]),
            "end_ms": float(window["t_ms"].iloc[-1]),
        }
        record.update(zip(names, values))
        records.append(record)
    return pd.DataFrame.from_records(records)


def feature_columns(frame: pd.DataFrame) -> list[str]:
    metadata = {
        "split",
        "source_class",
        "label_id",
        "label",
        "window_index",
        "start_ms",
        "end_ms",
        "activity_score",
        "quality_decision",
    }
    return [column for column in frame.columns if column not in metadata]


def calculate_activity_score(feature_frame: pd.DataFrame) -> np.ndarray:
    required = (
        "lin_norm__rms",
        "gyro_norm__rms",
        "lin_norm__mean_abs_diff",
        "gyro_norm__mean_abs_diff",
    )
    for column in required:
        if column not in feature_frame:
            raise ValueError(f"Missing activity feature: {column}")
    return (
        feature_frame["lin_norm__rms"].to_numpy(dtype=np.float64)
        + 0.60
        * feature_frame["gyro_norm__rms"].to_numpy(dtype=np.float64)
        + 1.50
        * feature_frame["lin_norm__mean_abs_diff"].to_numpy(dtype=np.float64)
        + 0.80
        * feature_frame["gyro_norm__mean_abs_diff"].to_numpy(dtype=np.float64)
    )


def confusion_matrix(
    truth: np.ndarray,
    prediction: np.ndarray,
    class_count: int,
) -> np.ndarray:
    matrix = np.zeros((class_count, class_count), dtype=np.int64)
    for expected, actual in zip(truth.astype(int), prediction.astype(int)):
        matrix[expected, actual] += 1
    return matrix


def classification_metrics(
    truth: np.ndarray,
    prediction: np.ndarray,
    class_names: tuple[str, ...] = CLASS_NAMES,
) -> dict[str, object]:
    matrix = confusion_matrix(truth, prediction, len(class_names))
    per_class: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for index, class_name in enumerate(class_names):
        true_positive = int(matrix[index, index])
        false_positive = int(np.sum(matrix[:, index]) - true_positive)
        false_negative = int(np.sum(matrix[index, :]) - true_positive)
        support = int(np.sum(matrix[index, :]))
        precision = true_positive / max(1, true_positive + false_positive)
        recall = true_positive / max(1, true_positive + false_negative)
        f1 = 2.0 * precision * recall / max(1e-12, precision + recall)
        f1_values.append(f1)
        per_class[class_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    return {
        "accuracy": float(np.mean(truth == prediction)),
        "macro_f1": float(np.mean(f1_values)),
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
        "class_order": list(class_names),
    }
