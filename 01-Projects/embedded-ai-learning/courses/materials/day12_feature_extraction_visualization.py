#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Day12 feature extraction and visualization for STM32N647/QMI8658A data.

Input:
  - Day11 GUI capture folders containing idle_clean.csv, walk_clean.csv,
    stairs_clean.csv, or
  - one folder containing any *_clean.csv files, or
  - --demo to generate synthetic data when the board dataset is unavailable.

Output:
  - features_all.csv: one row per window, one column per feature
  - dataset_summary.csv: sample/window count by label
  - feature_dictionary.md: formulas and meaning of each feature group
  - plots/*.png: time series, FFT, feature distributions, correlation, PCA-like map
"""

from __future__ import annotations

import argparse
import math
import os
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Iterable

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


LABEL_ORDER = ["idle", "walk", "stairs"]
LABEL_ID = {"idle": 0, "walk": 1, "stairs": 2}
LABEL_CN = {"idle": "静止", "walk": "走路", "stairs": "上楼梯"}
LABEL_DISPLAY = {"idle": "idle / 静止", "walk": "walk / 走路", "stairs": "stairs / 上楼梯"}

SAMPLE_RATE_HZ = 50.0
DEFAULT_WINDOW_SIZE = 64
DEFAULT_STEP_SIZE = 32
EPS = 1e-12
SCRIPT_DIR = Path(__file__).resolve().parent
DAY12_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "Course_Code" else SCRIPT_DIR
COURSE_DIR = DAY12_DIR.parent
DAY11_DIR = COURSE_DIR / "Day11-数据采集与清洗"
DEFAULT_OUTPUT_DIR = DAY12_DIR / "day12_feature_outputs"
DEFAULT_DAY11_DATA_DIR = DAY11_DIR / "Course_Data" / "dataset_day11"
if not DEFAULT_DAY11_DATA_DIR.exists():
    DEFAULT_DAY11_DATA_DIR = DAY12_DIR / "dataset_day11"
if not DEFAULT_DAY11_DATA_DIR.exists():
    DEFAULT_DAY11_DATA_DIR = DAY11_DIR

CLEAN_COLUMNS = [
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
]

BASE_SIGNAL_COLUMNS = [
    "lin_ax_mps2",
    "lin_ay_mps2",
    "lin_az_mps2",
    "lin_acc_mag_mps2",
    "gx_radps",
    "gy_radps",
    "gz_radps",
    "gyro_mag_radps",
]

TIME_FEATURES = [
    "mean",
    "max",
    "min",
    "variance",
    "std",
    "peak_to_peak",
    "rms",
    "skewness",
    "kurtosis",
    "slope",
    "change_rate",
]

FREQ_FEATURES = [
    "dominant_freq_hz",
    "dominant_magnitude",
    "spectral_centroid_hz",
    "low_band_energy",
    "mid_band_energy",
    "high_band_energy",
    "low_band_ratio",
    "mid_band_ratio",
    "high_band_ratio",
    "harmonic_2_freq_hz",
    "harmonic_2_ratio",
    "harmonic_3_freq_hz",
    "harmonic_3_ratio",
]


@dataclass
class WindowConfig:
    sample_rate_hz: float
    window_size: int
    step_size: int
    low_band: tuple[float, float]
    mid_band: tuple[float, float]
    high_band: tuple[float, float] | None
    harmonic_tolerance_hz: float
    drop_invalid: bool


def infer_label_from_path(path: Path) -> str:
    name = path.name.lower()
    for label in LABEL_ORDER:
        if label in name:
            return label
    return "unknown"


def ordered_labels(labels: Iterable[str]) -> list[str]:
    seen = {str(label) for label in labels if str(label) and str(label) != "nan"}
    return [label for label in LABEL_ORDER if label in seen] + sorted(seen - set(LABEL_ORDER))


def discover_clean_csvs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.exists():
        return []
    files = sorted(input_path.rglob("*_clean.csv"))
    if not files:
        files = sorted(input_path.rglob("*clean*.csv"))
    return files


def read_clean_csv(path: Path) -> pd.DataFrame:
    """Read GUI-created clean CSV or raw DAY11_CLEAN serial lines."""
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    if len(df.columns) > 0 and str(df.columns[0]).startswith("DAY11_CLEAN"):
        df = pd.read_csv(path, header=None)

    if "DAY11_CLEAN" in [str(c) for c in df.columns] or (len(df.columns) and str(df.iloc[0, 0]).startswith("DAY11_CLEAN")):
        df = pd.read_csv(path, header=None)
        df = df[df.iloc[:, 0].astype(str).str.startswith("DAY11_CLEAN")]
        df = df.iloc[:, 1 : 1 + len(CLEAN_COLUMNS)]
        df.columns = CLEAN_COLUMNS[: len(df.columns)]

    normalized_required = {"t_ms", "label", "lin_ax_mps2", "lin_ay_mps2", "lin_az_mps2", "gx_radps", "gy_radps", "gz_radps"}
    if normalized_required.issubset(df.columns):
        out = df.copy()
        label_from_file = infer_label_from_path(path)
        if label_from_file != "unknown":
            out["label"] = label_from_file
            out["label_id"] = LABEL_ID[label_from_file]
        elif "label_id" not in out.columns:
            out["label_id"] = out["label"].map(LABEL_ID).fillna(-1)
        for col in ["t_ms", "label_id", "lin_ax_mps2", "lin_ay_mps2", "lin_az_mps2", "gx_radps", "gy_radps", "gz_radps"]:
            out[col] = pd.to_numeric(out[col], errors="coerce")
        out = out.dropna(subset=["t_ms"]).copy()
        out["valid"] = pd.to_numeric(out["valid"], errors="coerce").fillna(1).astype(int) if "valid" in out.columns else 1
        out["clipped"] = pd.to_numeric(out["clipped"], errors="coerce").fillna(0).astype(int) if "clipped" in out.columns else 0
        out["lin_acc_mag_mps2"] = np.sqrt(
            out["lin_ax_mps2"] ** 2 + out["lin_ay_mps2"] ** 2 + out["lin_az_mps2"] ** 2
        )
        out["gyro_mag_radps"] = np.sqrt(out["gx_radps"] ** 2 + out["gy_radps"] ** 2 + out["gz_radps"] ** 2)
        return out.sort_values("t_ms").reset_index(drop=True)

    if "t_ms" not in df.columns:
        if len(df.columns) >= len(CLEAN_COLUMNS):
            df = df.iloc[:, : len(CLEAN_COLUMNS)]
            df.columns = CLEAN_COLUMNS
        else:
            raise ValueError(f"{path} does not look like a Day11 clean CSV file.")

    label_from_file = infer_label_from_path(path)
    if "label" not in df.columns or df["label"].isna().all():
        df["label"] = label_from_file
    if label_from_file != "unknown":
        df["label"] = label_from_file
        df["label_id"] = LABEL_ID[label_from_file]

    for col in CLEAN_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col not in {"label"} else label_from_file

    numeric_cols = [c for c in CLEAN_COLUMNS if c != "label"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["t_ms"]).copy()
    df = df.sort_values("t_ms").reset_index(drop=True)
    return normalize_units(df)


def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Day11 x1000 integer columns back to physical units."""
    out = df.copy()
    mapping = {
        "lin_ax_mps2_x1000": "lin_ax_mps2",
        "lin_ay_mps2_x1000": "lin_ay_mps2",
        "lin_az_mps2_x1000": "lin_az_mps2",
        "gx_radps_x1000": "gx_radps",
        "gy_radps_x1000": "gy_radps",
        "gz_radps_x1000": "gz_radps",
        "acc_norm_x1000": "acc_norm_mps2",
        "gyro_norm_x1000": "gyro_norm_radps",
    }
    for src, dst in mapping.items():
        out[dst] = pd.to_numeric(out[src], errors="coerce").fillna(0.0) / 1000.0

    out["lin_acc_mag_mps2"] = np.sqrt(
        out["lin_ax_mps2"] ** 2 + out["lin_ay_mps2"] ** 2 + out["lin_az_mps2"] ** 2
    )
    out["gyro_mag_radps"] = np.sqrt(out["gx_radps"] ** 2 + out["gy_radps"] ** 2 + out["gz_radps"] ** 2)
    out["valid"] = pd.to_numeric(out["valid"], errors="coerce").fillna(1).astype(int)
    out["clipped"] = pd.to_numeric(out["clipped"], errors="coerce").fillna(0).astype(int)
    return out


def generate_demo_data() -> pd.DataFrame:
    rows: list[dict] = []
    rng = np.random.default_rng(42)
    t_ms = 0
    for label in LABEL_ORDER:
        label_id = LABEL_ID[label]
        n = int(45 * SAMPLE_RATE_HZ)
        freq = 0.2 if label == "idle" else 1.7 if label == "walk" else 2.3
        amp = 0.20 if label == "idle" else 1.8 if label == "walk" else 3.1
        gyro_amp = 0.03 if label == "idle" else 0.45 if label == "walk" else 0.78
        for i in range(n):
            t = i / SAMPLE_RATE_HZ
            phase = 2.0 * np.pi * freq * t
            lin_ax = amp * np.sin(phase) + rng.normal(0, 0.10)
            lin_ay = 0.45 * amp * np.sin(phase + 0.8) + rng.normal(0, 0.10)
            lin_az = 0.65 * amp * np.sin(phase + 1.5) + rng.normal(0, 0.10)
            gx = gyro_amp * np.sin(phase + 0.3) + rng.normal(0, 0.02)
            gy = 0.7 * gyro_amp * np.sin(phase + 1.1) + rng.normal(0, 0.02)
            gz = 0.35 * gyro_amp * np.sin(phase + 2.0) + rng.normal(0, 0.02)
            if label != "idle" and i in {300, 901}:
                lin_ax += 7.5
                gz -= 1.2
            rows.append(
                {
                    "t_ms": t_ms,
                    "label_id": label_id,
                    "label": label,
                    "lin_ax_mps2": lin_ax,
                    "lin_ay_mps2": lin_ay,
                    "lin_az_mps2": lin_az,
                    "gx_radps": gx,
                    "gy_radps": gy,
                    "gz_radps": gz,
                    "valid": 1,
                    "clipped": 0,
                }
            )
            t_ms += int(1000 / SAMPLE_RATE_HZ)
    df = pd.DataFrame(rows)
    df["lin_acc_mag_mps2"] = np.sqrt(df["lin_ax_mps2"] ** 2 + df["lin_ay_mps2"] ** 2 + df["lin_az_mps2"] ** 2)
    df["gyro_mag_radps"] = np.sqrt(df["gx_radps"] ** 2 + df["gy_radps"] ** 2 + df["gz_radps"] ** 2)
    df["acc_norm_mps2"] = df["lin_acc_mag_mps2"]
    df["gyro_norm_radps"] = df["gyro_mag_radps"]
    return df


def load_dataset(input_path: Path | None, demo: bool) -> pd.DataFrame:
    if demo:
        return generate_demo_data()
    if input_path is None:
        raise ValueError("Please provide --input or use --demo.")
    files = discover_clean_csvs(input_path)
    if not files:
        raise FileNotFoundError(f"No *_clean.csv files found under: {input_path}")
    frames = []
    for path in files:
        df = read_clean_csv(path)
        if not df.empty:
            df["source_file"] = str(path)
            frames.append(df)
    if not frames:
        raise ValueError("Clean CSV files were found, but no valid rows were loaded.")
    return pd.concat(frames, ignore_index=True)


def iter_windows(df: pd.DataFrame, cfg: WindowConfig) -> Iterable[tuple[str, int, pd.DataFrame]]:
    window_id = 0
    for label in ordered_labels(df["label"].astype(str).unique()):
        label_df = df[df["label"].astype(str) == label].sort_values("t_ms").reset_index(drop=True)
        if label_df.empty:
            continue
        for start in range(0, len(label_df) - cfg.window_size + 1, cfg.step_size):
            win = label_df.iloc[start : start + cfg.window_size].copy()
            if cfg.drop_invalid and "valid" in win.columns and (win["valid"] == 0).any():
                continue
            yield label, window_id, win
            window_id += 1


def time_features(x: np.ndarray, sample_rate_hz: float) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    mean = float(np.mean(x))
    centered = x - mean
    var = float(np.mean(centered**2))
    std = math.sqrt(max(var, 0.0))
    rms = float(np.sqrt(np.mean(x**2)))
    t = np.arange(len(x), dtype=float) / sample_rate_hz
    t_centered = t - np.mean(t)
    slope = float(np.sum(t_centered * centered) / (np.sum(t_centered**2) + EPS))
    change_rate = float(np.mean(np.abs(np.diff(x))) * sample_rate_hz) if len(x) > 1 else 0.0
    skewness = float(np.mean(centered**3) / ((std**3) + EPS))
    kurtosis = float(np.mean(centered**4) / ((std**4) + EPS))
    return {
        "mean": mean,
        "max": float(np.max(x)),
        "min": float(np.min(x)),
        "variance": var,
        "std": std,
        "peak_to_peak": float(np.max(x) - np.min(x)),
        "rms": rms,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "slope": slope,
        "change_rate": change_rate,
    }


def band_energy(freqs: np.ndarray, power: np.ndarray, band: tuple[float, float]) -> float:
    lo, hi = band
    mask = (freqs >= lo) & (freqs < hi)
    if not np.any(mask):
        return 0.0
    return float(np.sum(power[mask]))


def harmonic_ratio(freqs: np.ndarray, power: np.ndarray, target_hz: float, tolerance_hz: float) -> float:
    if target_hz <= 0.0:
        return 0.0
    total = float(np.sum(power) + EPS)
    mask = np.abs(freqs - target_hz) <= tolerance_hz
    if not np.any(mask):
        nearest = int(np.argmin(np.abs(freqs - target_hz)))
        return float(power[nearest] / total)
    return float(np.sum(power[mask]) / total)


def frequency_features(x: np.ndarray, cfg: WindowConfig) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    x = x - np.mean(x)
    window = np.hanning(len(x))
    spectrum = np.fft.rfft(x * window)
    freqs = np.fft.rfftfreq(len(x), d=1.0 / cfg.sample_rate_hz)
    magnitude = np.abs(spectrum)
    power = magnitude**2

    non_dc = freqs > 0
    if not np.any(non_dc):
        dominant_freq = 0.0
        dominant_mag = 0.0
    else:
        idxs = np.where(non_dc)[0]
        dominant_idx = idxs[int(np.argmax(magnitude[non_dc]))]
        dominant_freq = float(freqs[dominant_idx])
        dominant_mag = float(magnitude[dominant_idx])

    power_no_dc = power.copy()
    power_no_dc[freqs == 0] = 0.0
    total_energy = float(np.sum(power_no_dc) + EPS)
    spectral_centroid = float(np.sum(freqs * power_no_dc) / total_energy)
    high_band = cfg.high_band if cfg.high_band else (cfg.mid_band[1], cfg.sample_rate_hz / 2.0 + EPS)
    low_energy = band_energy(freqs, power_no_dc, cfg.low_band)
    mid_energy = band_energy(freqs, power_no_dc, cfg.mid_band)
    high_energy = band_energy(freqs, power_no_dc, high_band)
    h2 = 2.0 * dominant_freq
    h3 = 3.0 * dominant_freq

    return {
        "dominant_freq_hz": dominant_freq,
        "dominant_magnitude": dominant_mag,
        "spectral_centroid_hz": spectral_centroid,
        "low_band_energy": low_energy,
        "mid_band_energy": mid_energy,
        "high_band_energy": high_energy,
        "low_band_ratio": low_energy / total_energy,
        "mid_band_ratio": mid_energy / total_energy,
        "high_band_ratio": high_energy / total_energy,
        "harmonic_2_freq_hz": h2,
        "harmonic_2_ratio": harmonic_ratio(freqs, power_no_dc, h2, cfg.harmonic_tolerance_hz),
        "harmonic_3_freq_hz": h3,
        "harmonic_3_ratio": harmonic_ratio(freqs, power_no_dc, h3, cfg.harmonic_tolerance_hz),
    }


def extract_features(df: pd.DataFrame, cfg: WindowConfig) -> pd.DataFrame:
    rows: list[dict] = []
    for label, window_id, win in iter_windows(df, cfg):
        row: dict[str, float | int | str] = {
            "window_id": window_id,
            "label": label,
            "label_cn": LABEL_CN.get(label, label),
            "label_id": int(LABEL_ID.get(label, -1)),
            "start_ms": int(win["t_ms"].iloc[0]),
            "end_ms": int(win["t_ms"].iloc[-1]),
            "n_samples": int(len(win)),
            "duration_s": float((win["t_ms"].iloc[-1] - win["t_ms"].iloc[0]) / 1000.0),
            "clipped_sum": int(win["clipped"].sum()) if "clipped" in win.columns else 0,
            "valid_ratio": float(win["valid"].mean()) if "valid" in win.columns else 1.0,
        }
        for signal in BASE_SIGNAL_COLUMNS:
            x = win[signal].to_numpy(dtype=float)
            for name, value in time_features(x, cfg.sample_rate_hz).items():
                row[f"{signal}__time__{name}"] = value
            for name, value in frequency_features(x, cfg).items():
                row[f"{signal}__freq__{name}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def safe_feature_columns(features: pd.DataFrame) -> list[str]:
    skip = {"window_id", "label", "label_cn", "label_id", "start_ms", "end_ms", "n_samples", "duration_s"}
    cols = [c for c in features.columns if c not in skip and pd.api.types.is_numeric_dtype(features[c])]
    return cols


def write_summary(raw: pd.DataFrame, features: pd.DataFrame, out_dir: Path) -> None:
    sample_summary = raw.groupby("label").agg(samples=("t_ms", "count"), duration_s=("t_ms", lambda x: (x.max() - x.min()) / 1000.0 if len(x) else 0.0))
    window_summary = features.groupby("label").agg(windows=("window_id", "count")) if not features.empty else pd.DataFrame()
    summary = sample_summary.join(window_summary, how="outer").fillna(0).reset_index()
    summary["label_cn"] = summary["label"].map(LABEL_CN).fillna(summary["label"])
    summary.to_csv(out_dir / "dataset_summary.csv", index=False, encoding="utf-8-sig")


def plot_time_series(raw: pd.DataFrame, out_dir: Path) -> None:
    labels = ordered_labels(raw["label"].astype(str).unique())
    fig, axes = plt.subplots(len(labels), 1, figsize=(12, max(4, 2.6 * len(labels))), sharex=False)
    if len(labels) == 1:
        axes = [axes]
    for ax, label in zip(axes, labels):
        part = raw[raw["label"] == label].head(800)
        if part.empty:
            ax.axis("off")
            continue
        t = (part["t_ms"] - part["t_ms"].iloc[0]) / 1000.0
        ax.plot(t, part["lin_acc_mag_mps2"], label="linear acc magnitude", linewidth=1.2)
        ax.plot(t, part["gyro_mag_radps"], label="gyro magnitude", linewidth=1.0)
        ax.set_title(f"{label} / {LABEL_CN.get(label, label)}")
        ax.set_ylabel("value")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="upper right")
    axes[-1].set_xlabel("time (s)")
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "time_series_by_label.png", dpi=160)
    plt.close(fig)


def average_fft_by_label(raw: pd.DataFrame, cfg: WindowConfig, out_dir: Path) -> None:
    rows = []
    fig, ax = plt.subplots(figsize=(11, 6))
    for label in ordered_labels(raw["label"].astype(str).unique()):
        spectra = []
        freqs_ref = None
        part = raw[raw["label"] == label].reset_index(drop=True)
        for start in range(0, len(part) - cfg.window_size + 1, cfg.window_size):
            x = part["lin_acc_mag_mps2"].iloc[start : start + cfg.window_size].to_numpy(dtype=float)
            x = x - np.mean(x)
            spectrum = np.fft.rfft(x * np.hanning(len(x)))
            freqs = np.fft.rfftfreq(len(x), d=1.0 / cfg.sample_rate_hz)
            power = np.abs(spectrum) ** 2
            power[freqs == 0] = 0
            spectra.append(power)
            freqs_ref = freqs
        if spectra and freqs_ref is not None:
            avg_power = np.mean(np.vstack(spectra), axis=0)
            ax.plot(freqs_ref, avg_power, label=f"{label}/{LABEL_CN.get(label, label)}")
            for f, p in zip(freqs_ref, avg_power):
                rows.append({"label": label, "frequency_hz": f, "avg_power": p})
    ax.set_title("Average FFT spectrum of linear acceleration magnitude")
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("average power")
    ax.set_xlim(0, min(12, cfg.sample_rate_hz / 2.0))
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "average_fft_lin_acc_mag.png", dpi=160)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(out_dir / "average_fft_lin_acc_mag.csv", index=False, encoding="utf-8-sig")


def plot_feature_distributions(features: pd.DataFrame, out_dir: Path) -> None:
    selected = [
        "lin_acc_mag_mps2__time__rms",
        "lin_acc_mag_mps2__time__peak_to_peak",
        "lin_acc_mag_mps2__time__change_rate",
        "lin_acc_mag_mps2__freq__dominant_freq_hz",
        "lin_acc_mag_mps2__freq__spectral_centroid_hz",
        "gyro_mag_radps__time__rms",
    ]
    selected = [c for c in selected if c in features.columns]
    if not selected:
        return
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()
    labels = ordered_labels(features["label"].astype(str).unique())
    for ax, col in zip(axes, selected):
        data = [features.loc[features["label"] == label, col].dropna().to_numpy() for label in labels]
        ax.boxplot(data, tick_labels=[LABEL_CN.get(l, l) for l in labels], showfliers=False)
        ax.set_title(col.replace("__", "\n"))
        ax.grid(True, axis="y", alpha=0.25)
    for ax in axes[len(selected) :]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "feature_distribution_boxplots.png", dpi=160)
    plt.close(fig)


def plot_correlation(features: pd.DataFrame, out_dir: Path) -> None:
    candidates = [
        "lin_acc_mag_mps2__time__mean",
        "lin_acc_mag_mps2__time__std",
        "lin_acc_mag_mps2__time__rms",
        "lin_acc_mag_mps2__time__peak_to_peak",
        "lin_acc_mag_mps2__time__change_rate",
        "lin_acc_mag_mps2__freq__dominant_freq_hz",
        "lin_acc_mag_mps2__freq__spectral_centroid_hz",
        "lin_acc_mag_mps2__freq__low_band_ratio",
        "lin_acc_mag_mps2__freq__high_band_ratio",
        "gyro_mag_radps__time__rms",
    ]
    cols = [c for c in candidates if c in features.columns]
    if len(cols) < 2:
        return
    corr = features[cols].corr(numeric_only=True).fillna(0.0)
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels([c.replace("lin_acc_mag_mps2__", "").replace("gyro_mag_radps__", "gyro_") for c in cols], rotation=60, ha="right", fontsize=8)
    ax.set_yticklabels([c.replace("lin_acc_mag_mps2__", "").replace("gyro_mag_radps__", "gyro_") for c in cols], fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Feature correlation heatmap")
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "feature_correlation_heatmap.png", dpi=160)
    plt.close(fig)


def plot_pca_like(features: pd.DataFrame, out_dir: Path) -> None:
    cols = safe_feature_columns(features)
    cols = [c for c in cols if "__time__" in c or "__freq__" in c]
    if len(cols) < 2 or len(features) < 3:
        return
    x = features[cols].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=float)
    x = (x - x.mean(axis=0)) / (x.std(axis=0) + EPS)
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    coords = x @ vt[:2].T
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = {"idle": "#70AD47", "walk": "#4472C4", "stairs": "#ED7D31"}
    for label in ordered_labels(features["label"].astype(str).unique()):
        mask = features["label"].to_numpy() == label
        if np.any(mask):
            ax.scatter(
                coords[mask, 0],
                coords[mask, 1],
                s=32,
                alpha=0.75,
                label=f"{label}/{LABEL_CN.get(label, label)}",
                c=colors.get(label, "#808080"),
            )
    ax.axhline(0, color="#cccccc", linewidth=0.8)
    ax.axvline(0, color="#cccccc", linewidth=0.8)
    ax.set_title("PCA-like 2D view from extracted features")
    ax.set_xlabel("component 1")
    ax.set_ylabel("component 2")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "plots" / "feature_pca_like_scatter.png", dpi=160)
    plt.close(fig)


def write_feature_dictionary(out_dir: Path, cfg: WindowConfig) -> None:
    text = f"""# Day12 Feature Dictionary

## Window configuration

- sample_rate_hz: {cfg.sample_rate_hz}
- window_size: {cfg.window_size} samples
- step_size: {cfg.step_size} samples
- low_band: {cfg.low_band[0]} to {cfg.low_band[1]} Hz
- mid_band: {cfg.mid_band[0]} to {cfg.mid_band[1]} Hz
- high_band: {cfg.high_band if cfg.high_band else (cfg.mid_band[1], cfg.sample_rate_hz / 2.0)} Hz

## Time-domain features

- mean: average value in one window. In this case it shows axis bias or posture tendency.
- max / min: maximum and minimum. They show the strongest positive and negative motion in the window.
- variance: average squared distance from the mean. It measures motion dispersion.
- std: square root of variance. It is easier to read because it has the same unit as the signal.
- peak_to_peak: max minus min. It measures motion amplitude.
- rms: sqrt(mean(x^2)). It measures signal energy or activity strength.
- skewness: third standardized moment. It shows whether the waveform is asymmetric.
- kurtosis: fourth standardized moment. It shows whether the window contains sharp peaks or impacts.
- slope: linear regression slope over time. It shows whether the window is trending upward/downward.
- change_rate: mean(abs(diff(x))) * sample_rate. It measures how quickly the signal changes.

## Frequency-domain features

- FFT spectrum: magnitude/power distribution over frequency bins.
- dominant_freq_hz: frequency bin with maximum non-DC magnitude. In walking/stairs it often relates to step rhythm.
- band_energy: sum of power in a frequency range.
- spectral_centroid_hz: weighted average frequency. Higher means more high-frequency components.
- low_band_energy / ratio: energy from {cfg.low_band[0]} to {cfg.low_band[1]} Hz. Often related to human motion rhythm.
- high_band_energy / ratio: energy in higher frequencies. It can represent abrupt motion, vibration, impact, or noise.
- harmonic_2_ratio / harmonic_3_ratio: energy near 2x and 3x dominant frequency. It describes periodic waveform structure.
"""
    (out_dir / "feature_dictionary.md").write_text(text, encoding="utf-8")


def make_plots(raw: pd.DataFrame, features: pd.DataFrame, cfg: WindowConfig, out_dir: Path) -> None:
    (out_dir / "plots").mkdir(parents=True, exist_ok=True)
    plot_time_series(raw, out_dir)
    average_fft_by_label(raw, cfg, out_dir)
    if not features.empty:
        plot_feature_distributions(features, out_dir)
        plot_correlation(features, out_dir)
        plot_pca_like(features, out_dir)


def filter_by_labels(raw: pd.DataFrame, labels: list[str] | None) -> pd.DataFrame:
    if not labels:
        return raw
    selected = set(labels)
    filtered = raw[raw["label"].astype(str).isin(selected)].copy()
    if "label_id" in filtered.columns:
        filtered["label_id"] = filtered["label"].map(LABEL_ID).fillna(filtered["label_id"]).astype(int)
    return filtered


def summarize_labels(raw: pd.DataFrame) -> str:
    parts = []
    for label in ordered_labels(raw["label"].astype(str).unique()):
        count = int((raw["label"].astype(str) == label).sum())
        parts.append(f"{label}/{LABEL_CN.get(label, label)}: {count} rows")
    return ", ".join(parts) if parts else "no rows"


def run_feature_pipeline(
    input_path: Path | None,
    demo: bool,
    out_dir: Path,
    cfg: WindowConfig,
    labels: list[str] | None = None,
    log: Callable[[str], None] | None = None,
) -> dict[str, object]:
    def emit(message: str) -> None:
        if log is not None:
            log(message)

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    emit("1/6 读取数据...")
    raw = load_dataset(input_path, demo)
    raw = filter_by_labels(raw, labels)
    if raw.empty:
        raise ValueError("选中的标签没有可用数据。请重新选择标签，或检查 Day11 的 *_clean.csv 文件。")
    emit(f"   数据行数: {len(raw)}")
    emit(f"   标签分布: {summarize_labels(raw)}")

    emit("2/6 按窗口切片并提取时域、频域特征...")
    features = extract_features(raw, cfg)
    if features.empty:
        raise RuntimeError("没有生成任何窗口。请减小窗口大小，或检查每个标签下的样本数量是否足够。")
    emit(f"   窗口数量: {len(features)}")
    emit(f"   特征列数: {len(features.columns)}")

    emit("3/6 保存归一化后的清洗数据和特征表...")
    clean_path = out_dir / "clean_data_normalized.csv"
    feature_path = out_dir / "features_all.csv"
    raw.to_csv(clean_path, index=False, encoding="utf-8-sig")
    features.to_csv(feature_path, index=False, encoding="utf-8-sig")

    emit("4/6 保存数据摘要和特征字典...")
    write_summary(raw, features, out_dir)
    write_feature_dictionary(out_dir, cfg)

    emit("5/6 生成可视化图片...")
    make_plots(raw, features, cfg, out_dir)

    plots_dir = out_dir / "plots"
    plot_files = sorted(plots_dir.glob("*.png")) if plots_dir.exists() else []
    emit("6/6 完成。")
    return {
        "out_dir": out_dir,
        "clean_path": clean_path,
        "feature_path": feature_path,
        "plots_dir": plots_dir,
        "plot_files": plot_files,
        "raw_rows": len(raw),
        "windows": len(features),
        "columns": len(features.columns),
        "labels": ordered_labels(raw["label"].astype(str).unique()),
    }


class Day12FeatureExtractionApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("特征提取与可视化 - 【AI+嵌入式：让单片机学会思考】课程配套工具")
        self.root.geometry("1080x760")
        self.root.minsize(980, 680)

        default_input = DEFAULT_DAY11_DATA_DIR if DEFAULT_DAY11_DATA_DIR.exists() else COURSE_DIR
        self.input_var = tk.StringVar(value=str(default_input))
        self.output_var = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.mode_var = tk.StringVar(value="real")
        self.sample_rate_var = tk.StringVar(value=str(SAMPLE_RATE_HZ))
        self.window_size_var = tk.StringVar(value=str(DEFAULT_WINDOW_SIZE))
        self.step_size_var = tk.StringVar(value=str(DEFAULT_STEP_SIZE))
        self.low_lo_var = tk.StringVar(value="0.3")
        self.low_hi_var = tk.StringVar(value="3.0")
        self.mid_lo_var = tk.StringVar(value="3.0")
        self.mid_hi_var = tk.StringVar(value="8.0")
        self.high_lo_var = tk.StringVar(value="8.0")
        self.high_hi_var = tk.StringVar(value="25.0")
        self.harmonic_tol_var = tk.StringVar(value="0.4")
        self.drop_invalid_var = tk.BooleanVar(value=True)
        self.label_vars = {label: tk.BooleanVar(value=True) for label in LABEL_ORDER}

        self.queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.running = False
        self.preview_photo = None

        self._build_ui()
        self._scan_input_files()
        self._poll_queue()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        title = ttk.Label(main, text="Day12 特征提取与可视化", font=("Microsoft YaHei UI", 16, "bold"))
        title.pack(anchor="w")
        subtitle = ttk.Label(
            main,
            text="把 Day11 采集到的 QMI8658A 六轴数据，转换成可训练、可解释、可视化的特征表。",
            foreground="#555555",
        )
        subtitle.pack(anchor="w", pady=(2, 10))

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self.source_tab = ttk.Frame(self.notebook, padding=12)
        self.param_tab = ttk.Frame(self.notebook, padding=12)
        self.run_tab = ttk.Frame(self.notebook, padding=12)
        self.preview_tab = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.source_tab, text="1. 数据源与标签")
        self.notebook.add(self.param_tab, text="2. 特征参数")
        self.notebook.add(self.run_tab, text="3. 运行与日志")
        self.notebook.add(self.preview_tab, text="4. 可视化预览")

        self._build_source_tab()
        self._build_param_tab()
        self._build_run_tab()
        self._build_preview_tab()

    def _build_source_tab(self) -> None:
        self.source_tab.columnconfigure(1, weight=1)
        mode_box = ttk.LabelFrame(self.source_tab, text="数据模式", padding=10)
        mode_box.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        ttk.Radiobutton(mode_box, text="使用 Day11 真实采集数据", value="real", variable=self.mode_var).pack(side="left", padx=(0, 22))
        ttk.Radiobutton(mode_box, text="使用 demo 示例数据", value="demo", variable=self.mode_var).pack(side="left")

        ttk.Label(self.source_tab, text="输入路径").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(self.source_tab, textvariable=self.input_var).grid(row=1, column=1, sticky="ew", padx=8)
        path_buttons = ttk.Frame(self.source_tab)
        path_buttons.grid(row=1, column=2, sticky="e")
        ttk.Button(path_buttons, text="选择文件夹", command=self._choose_input_dir).pack(side="left", padx=(0, 4))
        ttk.Button(path_buttons, text="选择 CSV", command=self._choose_input_file).pack(side="left")

        ttk.Label(self.source_tab, text="输出目录").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(self.source_tab, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Button(self.source_tab, text="选择输出目录", command=self._choose_output_dir).grid(row=2, column=2, sticky="e")

        label_box = ttk.LabelFrame(self.source_tab, text="要参与特征提取的动作标签", padding=10)
        label_box.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 10))
        for label in LABEL_ORDER:
            ttk.Checkbutton(label_box, text=LABEL_DISPLAY[label], variable=self.label_vars[label]).pack(side="left", padx=(0, 22))

        files_box = ttk.LabelFrame(self.source_tab, text="扫描到的 Day11 清洗数据文件", padding=10)
        files_box.grid(row=4, column=0, columnspan=3, sticky="nsew")
        self.source_tab.rowconfigure(4, weight=1)
        files_box.columnconfigure(0, weight=1)
        files_box.rowconfigure(0, weight=1)
        self.files_listbox = tk.Listbox(files_box, height=12)
        self.files_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(files_box, orient="vertical", command=self.files_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        ttk.Button(files_box, text="重新扫描", command=self._scan_input_files).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.scan_status_var = tk.StringVar(value="")
        ttk.Label(files_box, textvariable=self.scan_status_var, foreground="#555555").grid(row=1, column=0, sticky="e", pady=(8, 0))

    def _build_param_tab(self) -> None:
        self.param_tab.columnconfigure(1, weight=1)
        rows = [
            ("采样率 Hz", self.sample_rate_var, "Day11 默认 50Hz，必须和实际采集频率一致。"),
            ("窗口大小 samples", self.window_size_var, "64 个点约等于 1.28 秒，用来覆盖一个较完整的动作片段。"),
            ("窗口步长 samples", self.step_size_var, "32 个点表示 50% 重叠，能增加训练样本数量。"),
            ("低频段起点 Hz", self.low_lo_var, "人体动作节律一般集中在低频。"),
            ("低频段终点 Hz", self.low_hi_var, "默认 0.3 到 3Hz。"),
            ("中频段起点 Hz", self.mid_lo_var, "用于观察更快的身体晃动。"),
            ("中频段终点 Hz", self.mid_hi_var, "默认 3 到 8Hz。"),
            ("高频段起点 Hz", self.high_lo_var, "用于观察冲击、振动、噪声等成分。"),
            ("高频段终点 Hz", self.high_hi_var, "默认到奈奎斯特频率 25Hz。"),
            ("谐波容差 Hz", self.harmonic_tol_var, "查找 2 倍频、3 倍频附近能量时使用。"),
        ]
        for row, (name, var, hint) in enumerate(rows):
            ttk.Label(self.param_tab, text=name).grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(self.param_tab, textvariable=var, width=18).grid(row=row, column=1, sticky="w", padx=(8, 14), pady=5)
            ttk.Label(self.param_tab, text=hint, foreground="#666666").grid(row=row, column=2, sticky="w", pady=5)
        ttk.Checkbutton(
            self.param_tab,
            text="丢弃包含 invalid 样本的窗口",
            variable=self.drop_invalid_var,
        ).grid(row=len(rows), column=0, columnspan=3, sticky="w", pady=(12, 0))

    def _build_run_tab(self) -> None:
        button_row = ttk.Frame(self.run_tab)
        button_row.pack(fill="x")
        self.run_button = ttk.Button(button_row, text="开始特征提取", command=self._start_processing)
        self.run_button.pack(side="left")
        ttk.Button(button_row, text="打开输出目录", command=self._open_output_dir).pack(side="left", padx=8)
        ttk.Button(button_row, text="清空日志", command=self._clear_log).pack(side="left")

        self.progress = ttk.Progressbar(self.run_tab, mode="indeterminate")
        self.progress.pack(fill="x", pady=(12, 8))
        self.summary_var = tk.StringVar(value="等待运行。")
        ttk.Label(self.run_tab, textvariable=self.summary_var, foreground="#444444").pack(anchor="w")

        log_frame = ttk.Frame(self.run_tab)
        log_frame.pack(fill="both", expand=True, pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=22, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _build_preview_tab(self) -> None:
        self.preview_tab.columnconfigure(1, weight=1)
        self.preview_tab.rowconfigure(0, weight=1)
        left = ttk.Frame(self.preview_tab)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        ttk.Button(left, text="刷新图片列表", command=self._refresh_preview_list).pack(fill="x", pady=(0, 8))
        self.plot_listbox = tk.Listbox(left, width=36, height=22)
        self.plot_listbox.pack(fill="both", expand=True)
        self.plot_listbox.bind("<<ListboxSelect>>", lambda _event: self._show_selected_plot())

        right = ttk.Frame(self.preview_tab)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self.preview_label = ttk.Label(right, text="运行完成后，可在这里预览 plots 目录下的图片。", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")

    def _choose_input_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self.input_var.get() or str(COURSE_DIR))
        if path:
            self.input_var.set(path)
            self.mode_var.set("real")
            self._scan_input_files()

    def _choose_input_file(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=self.input_var.get() or str(COURSE_DIR),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.input_var.set(path)
            self.mode_var.set("real")
            self._scan_input_files()

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self.output_var.get() or str(DAY12_DIR))
        if path:
            self.output_var.set(path)

    def _scan_input_files(self) -> None:
        self.files_listbox.delete(0, tk.END)
        path = Path(self.input_var.get().strip()) if self.input_var.get().strip() else DEFAULT_DAY11_DATA_DIR
        files = discover_clean_csvs(path)
        if not files:
            self.scan_status_var.set("未找到 *_clean.csv；可选择 demo 模式先验证流程。")
            return
        for file in files:
            label = infer_label_from_path(file)
            self.files_listbox.insert(tk.END, f"[{label}] {file}")
        self.scan_status_var.set(f"共找到 {len(files)} 个清洗数据文件。")

    def _selected_labels(self) -> list[str]:
        return [label for label, var in self.label_vars.items() if var.get()]

    def _read_config(self) -> WindowConfig:
        sample_rate = float(self.sample_rate_var.get())
        window_size = int(float(self.window_size_var.get()))
        step_size = int(float(self.step_size_var.get()))
        low_band = (float(self.low_lo_var.get()), float(self.low_hi_var.get()))
        mid_band = (float(self.mid_lo_var.get()), float(self.mid_hi_var.get()))
        high_band = (float(self.high_lo_var.get()), float(self.high_hi_var.get()))
        harmonic_tolerance = float(self.harmonic_tol_var.get())
        if sample_rate <= 0:
            raise ValueError("采样率必须大于 0。")
        if window_size <= 1:
            raise ValueError("窗口大小必须大于 1。")
        if step_size <= 0:
            raise ValueError("窗口步长必须大于 0。")
        if not (0 <= low_band[0] < low_band[1] <= sample_rate / 2.0 + EPS):
            raise ValueError("低频段范围不合法。")
        if not (0 <= mid_band[0] < mid_band[1] <= sample_rate / 2.0 + EPS):
            raise ValueError("中频段范围不合法。")
        if not (0 <= high_band[0] < high_band[1] <= sample_rate / 2.0 + EPS):
            raise ValueError("高频段范围不合法。")
        return WindowConfig(
            sample_rate_hz=sample_rate,
            window_size=window_size,
            step_size=step_size,
            low_band=low_band,
            mid_band=mid_band,
            high_band=high_band,
            harmonic_tolerance_hz=harmonic_tolerance,
            drop_invalid=self.drop_invalid_var.get(),
        )

    def _start_processing(self) -> None:
        if self.running:
            return
        labels = self._selected_labels()
        if not labels:
            messagebox.showwarning("缺少标签", "请至少选择一个动作标签。")
            return
        try:
            cfg = self._read_config()
        except ValueError as exc:
            messagebox.showerror("参数错误", str(exc))
            return

        demo = self.mode_var.get() == "demo"
        input_path = None if demo else Path(self.input_var.get().strip())
        out_dir = Path(self.output_var.get().strip() or str(DEFAULT_OUTPUT_DIR))

        self.running = True
        self.run_button.configure(state="disabled")
        self.progress.start(12)
        self.summary_var.set("正在运行，请稍候...")
        self.notebook.select(self.run_tab)
        self._append_log("")
        self._append_log("========== Day12 特征提取开始 ==========")
        self._append_log(f"数据模式: {'demo 示例数据' if demo else 'Day11 真实数据'}")
        if input_path is not None:
            self._append_log(f"输入路径: {input_path}")
        self._append_log(f"输出目录: {out_dir}")
        self._append_log(f"标签选择: {', '.join(labels)}")

        thread = threading.Thread(
            target=self._worker,
            args=(input_path, demo, out_dir, cfg, labels),
            daemon=True,
        )
        thread.start()

    def _worker(self, input_path: Path | None, demo: bool, out_dir: Path, cfg: WindowConfig, labels: list[str]) -> None:
        try:
            result = run_feature_pipeline(
                input_path=input_path,
                demo=demo,
                out_dir=out_dir,
                cfg=cfg,
                labels=labels,
                log=lambda message: self.queue.put(("log", message)),
            )
            self.queue.put(("done", result))
        except Exception as exc:
            self.queue.put(("error", exc))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "done":
                    self._finish_success(payload)  # type: ignore[arg-type]
                elif kind == "error":
                    self._finish_error(payload)  # type: ignore[arg-type]
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _append_log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)

    def _finish_success(self, result: dict[str, object]) -> None:
        self.running = False
        self.progress.stop()
        self.run_button.configure(state="normal")
        out_dir = Path(result["out_dir"])  # type: ignore[arg-type]
        self.output_var.set(str(out_dir))
        self.summary_var.set(
            f"完成：{result['raw_rows']} 行数据，{result['windows']} 个窗口，{result['columns']} 列特征。输出目录：{out_dir}"
        )
        self._append_log(f"features_all.csv: {result['feature_path']}")
        self._append_log(f"plots: {result['plots_dir']}")
        self._refresh_preview_list()
        messagebox.showinfo("完成", "Day12 特征提取与可视化已经完成。")

    def _finish_error(self, exc: BaseException) -> None:
        self.running = False
        self.progress.stop()
        self.run_button.configure(state="normal")
        self.summary_var.set("运行失败，请查看日志。")
        self._append_log(f"错误: {exc}")
        messagebox.showerror("运行失败", str(exc))

    def _open_output_dir(self) -> None:
        path = Path(self.output_var.get().strip() or str(DEFAULT_OUTPUT_DIR)).resolve()
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            webbrowser.open(path.as_uri())

    def _refresh_preview_list(self) -> None:
        self.plot_listbox.delete(0, tk.END)
        plots_dir = Path(self.output_var.get().strip() or str(DEFAULT_OUTPUT_DIR)) / "plots"
        files = sorted(plots_dir.glob("*.png")) if plots_dir.exists() else []
        for file in files:
            self.plot_listbox.insert(tk.END, file.name)
        if files:
            self.plot_listbox.selection_set(0)
            self._show_selected_plot()
        else:
            self.preview_label.configure(text="还没有找到可预览的 PNG 图片。", image="")
            self.preview_photo = None

    def _show_selected_plot(self) -> None:
        selection = self.plot_listbox.curselection()
        if not selection:
            return
        name = self.plot_listbox.get(selection[0])
        path = Path(self.output_var.get().strip() or str(DEFAULT_OUTPUT_DIR)) / "plots" / name
        if not path.exists():
            return
        try:
            from PIL import Image, ImageTk  # type: ignore

            image = Image.open(path)
            image.thumbnail((720, 520))
            self.preview_photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=self.preview_photo, text="")
        except Exception:
            self.preview_label.configure(text=f"图片已生成：{path}", image="")
            self.preview_photo = None


def run_gui() -> int:
    root = tk.Tk()
    Day12FeatureExtractionApp(root)
    root.mainloop()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Day12 feature extraction and visualization for Day11 IMU data.")
    parser.add_argument("--gui", action="store_true", help="Open the Day12 upper-computer GUI tool.")
    parser.add_argument("--input", type=Path, help="Day11 dataset folder or a single *_clean.csv file.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory.")
    parser.add_argument("--demo", action="store_true", help="Generate synthetic idle/walk/stairs data and process it.")
    parser.add_argument("--labels", nargs="+", choices=LABEL_ORDER, help="Labels to process. Default: all labels.")
    parser.add_argument("--sample-rate", type=float, default=SAMPLE_RATE_HZ, help="Sampling rate in Hz. Day11 default is 50.")
    parser.add_argument("--window-size", type=int, default=DEFAULT_WINDOW_SIZE, help="Window size in samples.")
    parser.add_argument("--step-size", type=int, default=DEFAULT_STEP_SIZE, help="Step size in samples.")
    parser.add_argument("--low-band", type=float, nargs=2, default=(0.3, 3.0), metavar=("LO", "HI"))
    parser.add_argument("--mid-band", type=float, nargs=2, default=(3.0, 8.0), metavar=("LO", "HI"))
    parser.add_argument("--high-band", type=float, nargs=2, default=None, metavar=("LO", "HI"))
    parser.add_argument("--harmonic-tolerance", type=float, default=0.4, help="Tolerance around harmonic frequencies in Hz.")
    parser.add_argument("--keep-invalid", action="store_true", help="Keep windows that contain valid=0 samples.")
    return parser.parse_args()


def main() -> int:
    if len(sys.argv) == 1:
        return run_gui()
    args = parse_args()
    if args.gui:
        return run_gui()
    cfg = WindowConfig(
        sample_rate_hz=args.sample_rate,
        window_size=args.window_size,
        step_size=args.step_size,
        low_band=tuple(args.low_band),
        mid_band=tuple(args.mid_band),
        high_band=tuple(args.high_band) if args.high_band else None,
        harmonic_tolerance_hz=args.harmonic_tolerance,
        drop_invalid=not args.keep_invalid,
    )
    result = run_feature_pipeline(args.input, args.demo, args.out, cfg, labels=args.labels)

    print("Day12 feature extraction completed.")
    print(f"input rows: {result['raw_rows']}")
    print(f"windows: {result['windows']}")
    print(f"features: {result['columns']} columns")
    print(f"output: {result['out_dir']}")
    print(f"main csv: {result['feature_path']}")
    print(f"plots: {result['plots_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
