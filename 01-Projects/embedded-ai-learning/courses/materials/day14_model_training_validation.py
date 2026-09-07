#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Day14: 模型训练与验证实战脚本

本脚本面向零 AI 基础或 AI 基础薄弱的嵌入式工程师，完成一个完整的动作识别
模型训练与验证闭环：

1. 优先读取 Day12 生成的 features_all.csv。
2. 如果找不到 Day12 数据，可以自动生成一份示例特征表，保证课程能跑通。
3. 默认优先使用 TensorFlow/Keras 训练 Day13 设计的 MLP：
   Dense(32) + Dense(16) + Softmax。
4. 如果当前电脑暂时没有 TensorFlow，脚本会切换到 NumPy 兜底后端，
   用来帮助理解训练原理，不作为课程主线。
5. 输出训练曲线、混淆矩阵、分类报告、Keras 模型文件、模型权重、
   归一化参数和标签映射。

为什么保留 NumPy 兜底：
    本节课的课程主线是 TensorFlow/Keras，目的是承接 Day13 的模型设计。
    NumPy 兜底后端只是为了在环境不完整时仍然能够演示 Dense、ReLU、
    Softmax、loss、验证集和测试集这些训练概念。

为什么没有强依赖 sklearn：
    数据划分、归一化和指标计算在脚本中展开实现，便于零基础学员逐行理解。
    这不改变训练主线：模型训练仍然优先使用 TensorFlow/Keras。

运行示例：
    python day14_model_training_validation.py

指定输入：
    python day14_model_training_validation.py --input D:/xxx/features_all.csv

指定输出目录：
    python day14_model_training_validation.py --out D:/xxx/day14_training_output
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RANDOM_SEED = 42

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


LABEL_NAME_CN = {
    "idle": "静止",
    "walk": "走路",
    "stairs": "上楼梯",
}


NON_FEATURE_COLUMNS = {
    "window_id",
    "label",
    "label_cn",
    "label_id",
    "start_ms",
    "end_ms",
    "n_samples",
    "duration_s",
}


@dataclass
class DatasetBundle:
    """训练脚本内部使用的数据包。"""

    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    feature_columns: List[str]
    label_to_id: Dict[str, int]
    id_to_label: Dict[int, str]
    scaler_mean: np.ndarray
    scaler_std: np.ndarray
    test_info: pd.DataFrame


class TinyMLP:
    """一个非常小的三分类 MLP。

    网络结构：
        输入特征 -> Dense(hidden1) -> ReLU -> Dense(hidden2) -> ReLU
        -> Dense(num_classes) -> Softmax

    这里的代码特意写得直白一些，便于课堂逐行讲解。
    """

    def __init__(
        self,
        input_dim: int,
        hidden1: int,
        hidden2: int,
        num_classes: int,
        seed: int = RANDOM_SEED,
    ) -> None:
        rng = np.random.default_rng(seed)
        self.params = {
            "w1": rng.normal(0, math.sqrt(2.0 / input_dim), size=(input_dim, hidden1)),
            "b1": np.zeros((1, hidden1)),
            "w2": rng.normal(0, math.sqrt(2.0 / hidden1), size=(hidden1, hidden2)),
            "b2": np.zeros((1, hidden2)),
            "w3": rng.normal(0, math.sqrt(2.0 / hidden2), size=(hidden2, num_classes)),
            "b3": np.zeros((1, num_classes)),
        }
        self.adam_m = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.adam_v = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.adam_t = 0

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        z1 = x @ self.params["w1"] + self.params["b1"]
        a1 = np.maximum(z1, 0)
        z2 = a1 @ self.params["w2"] + self.params["b2"]
        a2 = np.maximum(z2, 0)
        logits = a2 @ self.params["w3"] + self.params["b3"]
        probs = softmax(logits)
        cache = {"x": x, "z1": z1, "a1": a1, "z2": z2, "a2": a2, "probs": probs}
        return probs, cache

    def loss_and_grads(
        self,
        x: np.ndarray,
        y: np.ndarray,
        l2: float = 1e-4,
    ) -> Tuple[float, Dict[str, np.ndarray]]:
        probs, cache = self.forward(x)
        n = x.shape[0]
        y_onehot = one_hot(y, probs.shape[1])

        # 交叉熵损失：真实类别概率越小，loss 越大。
        ce_loss = -np.sum(y_onehot * np.log(probs + 1e-12)) / n
        l2_loss = 0.5 * l2 * (
            np.sum(self.params["w1"] ** 2)
            + np.sum(self.params["w2"] ** 2)
            + np.sum(self.params["w3"] ** 2)
        )
        loss = ce_loss + l2_loss

        dlogits = (probs - y_onehot) / n
        grads: Dict[str, np.ndarray] = {}
        grads["w3"] = cache["a2"].T @ dlogits + l2 * self.params["w3"]
        grads["b3"] = np.sum(dlogits, axis=0, keepdims=True)

        da2 = dlogits @ self.params["w3"].T
        dz2 = da2 * (cache["z2"] > 0)
        grads["w2"] = cache["a1"].T @ dz2 + l2 * self.params["w2"]
        grads["b2"] = np.sum(dz2, axis=0, keepdims=True)

        da1 = dz2 @ self.params["w2"].T
        dz1 = da1 * (cache["z1"] > 0)
        grads["w1"] = cache["x"].T @ dz1 + l2 * self.params["w1"]
        grads["b1"] = np.sum(dz1, axis=0, keepdims=True)
        return loss, grads

    def update_adam(
        self,
        grads: Dict[str, np.ndarray],
        learning_rate: float,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
    ) -> None:
        self.adam_t += 1
        for name, grad in grads.items():
            self.adam_m[name] = beta1 * self.adam_m[name] + (1 - beta1) * grad
            self.adam_v[name] = beta2 * self.adam_v[name] + (1 - beta2) * (grad * grad)
            m_hat = self.adam_m[name] / (1 - beta1**self.adam_t)
            v_hat = self.adam_v[name] / (1 - beta2**self.adam_t)
            self.params[name] -= learning_rate * m_hat / (np.sqrt(v_hat) + eps)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        probs, _ = self.forward(x)
        return probs

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(x), axis=1)


class KerasModelAdapter:
    """Wrap a Keras model so the rest of the script can reuse one evaluation path."""

    def __init__(self, model) -> None:
        self.model = model
        self.params = {f"weight_{idx}": value for idx, value in enumerate(model.get_weights())}

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        return self.model.predict(x, verbose=0)

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(x), axis=1)

    def save_model(self, out_dir: Path) -> None:
        self.model.save(out_dir / "model.keras")


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - np.max(logits, axis=1, keepdims=True)
    exp_values = np.exp(logits)
    return exp_values / np.sum(exp_values, axis=1, keepdims=True)


def one_hot(y: np.ndarray, num_classes: int) -> np.ndarray:
    out = np.zeros((len(y), num_classes), dtype=float)
    out[np.arange(len(y)), y] = 1.0
    return out


def find_course_root() -> Path:
    """从脚本位置向上寻找 course 目录。"""

    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if parent.name.lower() == "course":
            return parent
        if any(p.name.startswith("Day12") for p in parent.iterdir() if p.is_dir()):
            return parent
    return here.parent


def import_keras_backend(seed: int = RANDOM_SEED):
    """Import TensorFlow/Keras after preparing a writable temp directory.

    Some Windows Python environments fail to import TensorFlow when the default
    TEMP directory is not writable. The course script therefore creates a local
    temp folder under the course root before importing TensorFlow.
    """

    tmp_dir = find_course_root() / ".tmp_day14_tensorflow"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = str(tmp_dir)
    os.environ["TMP"] = str(tmp_dir)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

    import tensorflow as tf  # type: ignore
    from tensorflow import keras  # type: ignore

    try:
        tf.keras.utils.set_random_seed(seed)
    except Exception:
        pass
    return tf, keras


def discover_day12_features() -> Path | None:
    """自动寻找 Day12 生成的 features_all.csv。"""

    course_root = find_course_root()
    candidates: List[Path] = []
    for day12_dir in course_root.iterdir():
        if day12_dir.is_dir() and day12_dir.name.startswith("Day12"):
            preferred = [
                day12_dir / "Course_Outputs" / "day12_feature_outputs" / "features_all.csv",
                day12_dir / "Course_Outputs" / "11" / "features_all.csv",
            ]
            candidates.extend(preferred)
            candidates.extend(day12_dir.rglob("features_all.csv"))

    seen = set()
    unique_candidates = []
    for path in candidates:
        if path not in seen:
            unique_candidates.append(path)
            seen.add(path)

    for path in unique_candidates:
        if path.exists() and path.stat().st_size > 0:
            return path
    return None


def generate_demo_features(out_csv: Path, samples_per_class: int = 180, seed: int = RANDOM_SEED) -> Path:
    """生成一份类似 Day12 输出结构的示例特征表。

    这份数据不是传感器真实采集结果，只用于课堂兜底演示。
    它故意让 idle / walk / stairs 在动作强度、主频、能量分布上有差异。
    """

    rng = np.random.default_rng(seed)
    rows = []
    axes = ["lin_acc_mag_mps2", "gyro_mag_radps", "lin_ax_mps2", "lin_ay_mps2", "lin_az_mps2"]
    time_features = ["mean", "std", "rms", "peak_to_peak", "variance", "change_rate"]
    freq_features = ["dominant_freq_hz", "spectral_centroid_hz", "low_band_energy", "mid_band_energy", "high_band_energy"]

    class_profile = {
        "idle": {"amp": 0.25, "freq": 0.4, "gyro": 0.08},
        "walk": {"amp": 1.30, "freq": 1.7, "gyro": 0.45},
        "stairs": {"amp": 1.85, "freq": 2.2, "gyro": 0.70},
    }

    window_id = 0
    for label_id, label in enumerate(["idle", "walk", "stairs"]):
        profile = class_profile[label]
        for i in range(samples_per_class):
            row = {
                "window_id": window_id,
                "label": label,
                "label_cn": LABEL_NAME_CN[label],
                "label_id": label_id,
                "start_ms": i * 640,
                "end_ms": i * 640 + 1260,
                "n_samples": 64,
                "duration_s": 1.26,
            }
            for axis in axes:
                axis_scale = profile["gyro"] if axis.startswith("gyro") else profile["amp"]
                jitter = rng.normal(0.0, 0.10)
                for feat in time_features:
                    if feat == "mean":
                        value = rng.normal(0.0, 0.08 + axis_scale * 0.03)
                    elif feat == "variance":
                        value = max(1e-4, (axis_scale + jitter) ** 2 * rng.uniform(0.15, 0.30))
                    elif feat == "std":
                        value = max(1e-4, axis_scale * rng.uniform(0.35, 0.55))
                    elif feat == "rms":
                        value = max(1e-4, axis_scale * rng.uniform(0.75, 1.10))
                    elif feat == "peak_to_peak":
                        value = max(1e-4, axis_scale * rng.uniform(1.6, 2.4))
                    else:
                        value = max(1e-4, axis_scale * rng.uniform(1.8, 3.4))
                    row[f"{axis}__time__{feat}"] = float(value)

                for feat in freq_features:
                    if feat == "dominant_freq_hz":
                        value = rng.normal(profile["freq"], 0.18)
                    elif feat == "spectral_centroid_hz":
                        value = rng.normal(profile["freq"] * 1.25, 0.22)
                    elif feat == "low_band_energy":
                        value = axis_scale * rng.uniform(0.55, 0.85) if label == "idle" else axis_scale * rng.uniform(0.15, 0.35)
                    elif feat == "mid_band_energy":
                        value = axis_scale * rng.uniform(0.20, 0.35) if label == "idle" else axis_scale * rng.uniform(0.45, 0.75)
                    else:
                        value = axis_scale * rng.uniform(0.02, 0.10) if label != "stairs" else axis_scale * rng.uniform(0.25, 0.55)
                    row[f"{axis}__freq__{feat}"] = float(max(1e-4, value))
            rows.append(row)
            window_id += 1

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")
    return out_csv


def select_feature_columns(df: pd.DataFrame) -> List[str]:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c not in NON_FEATURE_COLUMNS]
    if not feature_cols:
        raise ValueError("没有找到可训练的数值特征列。请检查 features_all.csv。")
    return feature_cols


def prepare_dataset(csv_path: Path, seed: int = RANDOM_SEED) -> DatasetBundle:
    df = pd.read_csv(csv_path)
    if "label" not in df.columns:
        raise ValueError("features_all.csv 中必须包含 label 列。")

    feature_columns = select_feature_columns(df)
    existing_labels = [str(x) for x in df["label"].dropna().unique()]
    preferred_order = ["idle", "walk", "stairs"]
    labels = [name for name in preferred_order if name in existing_labels]
    labels.extend(sorted(name for name in existing_labels if name not in labels))
    label_to_id = {name: idx for idx, name in enumerate(labels)}
    id_to_label = {idx: name for name, idx in label_to_id.items()}

    x_df = df[feature_columns].copy()
    x_df = x_df.replace([np.inf, -np.inf], np.nan)
    x_df = x_df.fillna(x_df.median(numeric_only=True))
    x = x_df.to_numpy(dtype=float)
    y = df["label"].map(label_to_id).to_numpy(dtype=int)

    train_idx, val_idx, test_idx = stratified_split(y, seed=seed)

    x_train_raw = x[train_idx]
    scaler_mean = x_train_raw.mean(axis=0)
    scaler_std = x_train_raw.std(axis=0)
    scaler_std[scaler_std < 1e-8] = 1.0

    x_scaled = (x - scaler_mean) / scaler_std
    test_info = df.iloc[test_idx][["window_id", "label", "label_cn"] if "label_cn" in df.columns else ["window_id", "label"]].copy()

    return DatasetBundle(
        x_train=x_scaled[train_idx],
        y_train=y[train_idx],
        x_val=x_scaled[val_idx],
        y_val=y[val_idx],
        x_test=x_scaled[test_idx],
        y_test=y[test_idx],
        feature_columns=feature_columns,
        label_to_id=label_to_id,
        id_to_label=id_to_label,
        scaler_mean=scaler_mean,
        scaler_std=scaler_std,
        test_info=test_info.reset_index(drop=True),
    )


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


def iterate_minibatches(
    x: np.ndarray,
    y: np.ndarray,
    batch_size: int,
    seed: int,
) -> Iterable[Tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(seed)
    indices = np.arange(len(x))
    rng.shuffle(indices)
    for start in range(0, len(indices), batch_size):
        batch_idx = indices[start : start + batch_size]
        yield x[batch_idx], y[batch_idx]


def accuracy(model: TinyMLP, x: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(model.predict(x) == y))


def cross_entropy(model: TinyMLP, x: np.ndarray, y: np.ndarray) -> float:
    probs = model.predict_proba(x)
    return float(-np.mean(np.log(probs[np.arange(len(y)), y] + 1e-12)))


def train_model(
    data: DatasetBundle,
    hidden1: int,
    hidden2: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
) -> Tuple[TinyMLP, Dict[str, List[float]]]:
    model = TinyMLP(
        input_dim=data.x_train.shape[1],
        hidden1=hidden1,
        hidden2=hidden2,
        num_classes=len(data.label_to_id),
        seed=seed,
    )
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_val_loss = float("inf")
    best_params = {k: v.copy() for k, v in model.params.items()}
    patience = 20
    patience_left = patience

    for epoch in range(1, epochs + 1):
        for xb, yb in iterate_minibatches(data.x_train, data.y_train, batch_size, seed + epoch):
            _, grads = model.loss_and_grads(xb, yb)
            model.update_adam(grads, learning_rate)

        train_loss = cross_entropy(model, data.x_train, data.y_train)
        val_loss = cross_entropy(model, data.x_val, data.y_val)
        train_acc = accuracy(model, data.x_train, data.y_train)
        val_acc = accuracy(model, data.x_val, data.y_val)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_params = {k: v.copy() for k, v in model.params.items()}
            patience_left = patience
        else:
            patience_left -= 1

        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            print(
                f"Epoch {epoch:03d}/{epochs} | "
                f"loss={train_loss:.4f} val_loss={val_loss:.4f} | "
                f"acc={train_acc:.3f} val_acc={val_acc:.3f}"
            )

        if patience_left <= 0:
            print(f"Early stopping: validation loss 连续 {patience} 轮没有改善。")
            break

    model.params = best_params
    return model, history


def train_model_keras(
    data: DatasetBundle,
    hidden1: int,
    hidden2: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    out_dir: Path,
) -> Tuple[KerasModelAdapter, Dict[str, List[float]]]:
    """Train the Day13 MLP design with TensorFlow/Keras."""

    _, keras = import_keras_backend(seed)
    model = keras.Sequential(
        [
            keras.layers.Input(shape=(data.x_train.shape[1],), name="feature_input"),
            keras.layers.Dense(hidden1, activation="relu", name="dense_32"),
            keras.layers.Dense(hidden2, activation="relu", name="dense_16"),
            keras.layers.Dense(len(data.label_to_id), activation="softmax", name="class_probability"),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=20,
            restore_best_weights=True,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(out_dir / "best_model.keras"),
            monitor="val_loss",
            save_best_only=True,
        ),
    ]
    print("使用 TensorFlow/Keras 后端训练，网络结构与 Day13 的 MLP 设计保持一致。")
    model.summary(print_fn=lambda line: print("  " + line))
    fit_history = model.fit(
        data.x_train,
        data.y_train,
        validation_data=(data.x_val, data.y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=2,
    )
    history = {
        "train_loss": [float(v) for v in fit_history.history["loss"]],
        "val_loss": [float(v) for v in fit_history.history["val_loss"]],
        "train_acc": [float(v) for v in fit_history.history["accuracy"]],
        "val_acc": [float(v) for v in fit_history.history["val_accuracy"]],
    }
    return KerasModelAdapter(model), history


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def classification_report(cm: np.ndarray, id_to_label: Dict[int, str]) -> List[Dict[str, float | str | int]]:
    rows: List[Dict[str, float | str | int]] = []
    for i in range(cm.shape[0]):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        rows.append(
            {
                "label": id_to_label[i],
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": int(support),
            }
        )
    return rows


def save_training_curves(history: Dict[str, List[float]], out_png: Path) -> None:
    epochs = np.arange(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=140)
    axes[0].plot(epochs, history["train_loss"], label="train_loss")
    axes[0].plot(epochs, history["val_loss"], label="val_loss")
    axes[0].set_title("Loss 曲线")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Cross Entropy")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend()

    axes[1].plot(epochs, history["train_acc"], label="train_acc")
    axes[1].plot(epochs, history["val_acc"], label="val_acc")
    axes[1].set_title("Accuracy 曲线")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_ylim(0, 1.05)
    axes[1].grid(True, alpha=0.25)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def save_confusion_matrix(cm: np.ndarray, id_to_label: Dict[int, str], out_png: Path) -> None:
    labels = [id_to_label[i] for i in range(len(id_to_label))]
    fig, ax = plt.subplots(figsize=(5.2, 4.6), dpi=150)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(np.arange(len(labels)), labels=labels, rotation=30, ha="right")
    ax.set_yticks(np.arange(len(labels)), labels=labels)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title("Confusion Matrix")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def save_outputs(
    out_dir: Path,
    input_csv: Path,
    data: DatasetBundle,
    model,
    history: Dict[str, List[float]],
    backend: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    y_pred = model.predict(data.x_test)
    probs = model.predict_proba(data.x_test)
    cm = confusion_matrix(data.y_test, y_pred, len(data.label_to_id))
    report_rows = classification_report(cm, data.id_to_label)
    test_acc = float(np.mean(y_pred == data.y_test))
    macro_f1 = float(np.mean([row["f1"] for row in report_rows]))

    np.savez(out_dir / "model_weights.npz", **model.params)
    if hasattr(model, "save_model"):
        model.save_model(out_dir)
    save_json(
        out_dir / "scaler.json",
        {"mean": data.scaler_mean.tolist(), "std": data.scaler_std.tolist()},
    )
    save_json(out_dir / "label_map.json", data.label_to_id)
    save_json(out_dir / "feature_columns.json", {"feature_columns": data.feature_columns})
    save_json(
        out_dir / "metrics.json",
        {
            "input_csv": str(input_csv),
            "num_features": len(data.feature_columns),
            "num_classes": len(data.label_to_id),
            "train_samples": int(len(data.y_train)),
            "val_samples": int(len(data.y_val)),
            "test_samples": int(len(data.y_test)),
            "test_accuracy": test_acc,
            "macro_f1": macro_f1,
            "backend": backend,
            "classification_report": report_rows,
        },
    )

    with (out_dir / "classification_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "precision", "recall", "f1", "support"])
        writer.writeheader()
        writer.writerows(report_rows)

    prediction_df = data.test_info.copy()
    prediction_df["true_id"] = data.y_test
    prediction_df["pred_id"] = y_pred
    prediction_df["pred_label"] = [data.id_to_label[int(i)] for i in y_pred]
    prediction_df["correct"] = prediction_df["true_id"] == prediction_df["pred_id"]
    for class_id, label in data.id_to_label.items():
        prediction_df[f"prob_{label}"] = probs[:, class_id]
    prediction_df.to_csv(out_dir / "predictions_test.csv", index=False, encoding="utf-8-sig")

    save_training_curves(history, out_dir / "training_curves.png")
    save_confusion_matrix(cm, data.id_to_label, out_dir / "confusion_matrix.png")

    summary_lines = [
        "Day14 模型训练与验证输出摘要",
        "=" * 36,
        f"输入特征表: {input_csv}",
        f"特征数量: {len(data.feature_columns)}",
        f"类别映射: {data.label_to_id}",
        f"训练/验证/测试样本数: {len(data.y_train)} / {len(data.y_val)} / {len(data.y_test)}",
        f"测试集 accuracy: {test_acc:.4f}",
        f"测试集 macro F1: {macro_f1:.4f}",
        f"训练后端: {backend}",
        "",
        "输出文件说明:",
        "model.keras                - Keras 模型文件，使用 Keras 后端时生成",
        "best_model.keras           - 验证集 loss 最优的 Keras 模型，使用 Keras 后端时生成",
        "model_weights.npz          - MLP 三层 Dense 的权重和偏置，便于查看参数",
        "scaler.json                - 训练集均值和标准差，部署端必须保持一致",
        "label_map.json             - idle/walk/stairs 与数字类别的对应关系",
        "feature_columns.json       - 模型输入特征列顺序，部署端必须保持一致",
        "training_curves.png        - loss 和 accuracy 曲线",
        "confusion_matrix.png       - 混淆矩阵",
        "classification_report.csv  - precision/recall/F1",
        "predictions_test.csv       - 测试集逐窗口预测结果",
    ]
    (out_dir / "run_summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    print("\n训练与验证完成。")
    print(f"测试集 accuracy: {test_acc:.4f}")
    print(f"测试集 macro F1: {macro_f1:.4f}")
    print(f"输出目录: {out_dir}")


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Day14 模型训练与验证实战脚本")
    parser.add_argument("--input", type=str, default="", help="features_all.csv 路径；不填则自动寻找 Day12 输出")
    parser.add_argument("--out", type=str, default="", help="输出目录；不填则使用脚本目录下的 day14_training_output")
    parser.add_argument("--epochs", type=int, default=100, help="最大训练轮数")
    parser.add_argument("--batch-size", type=int, default=32, help="每次参数更新使用的样本数")
    parser.add_argument("--learning-rate", type=float, default=0.003, help="Adam 学习率")
    parser.add_argument("--hidden1", type=int, default=32, help="第一层隐藏层神经元数量")
    parser.add_argument("--hidden2", type=int, default=16, help="第二层隐藏层神经元数量")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="随机种子，保证课堂演示可复现")
    parser.add_argument(
        "--backend",
        choices=["auto", "keras", "numpy"],
        default="auto",
        help="训练后端；auto 优先使用 Keras，失败后切换到 numpy 兜底",
    )
    parser.add_argument("--generate-demo-data", action="store_true", help="强制生成示例特征表，不读取 Day12 数据")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    out_dir = Path(args.out).resolve() if args.out else script_dir / "day14_training_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_demo_data:
        input_csv = generate_demo_features(out_dir / "demo_features_all.csv", seed=args.seed)
        print(f"已生成示例特征表: {input_csv}")
    elif args.input:
        input_csv = Path(args.input).resolve()
    else:
        found = discover_day12_features()
        if found is None:
            input_csv = generate_demo_features(out_dir / "demo_features_all.csv", seed=args.seed)
            print("没有找到 Day12 的 features_all.csv，已自动生成示例数据。")
        else:
            input_csv = found
            print(f"自动找到 Day12 特征表: {input_csv}")

    if not input_csv.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_csv}")

    print("开始准备数据...")
    data = prepare_dataset(input_csv, seed=args.seed)
    print(f"特征数量: {len(data.feature_columns)}")
    print(f"类别映射: {data.label_to_id}")
    print(f"训练/验证/测试样本数: {len(data.y_train)} / {len(data.y_val)} / {len(data.y_test)}")

    print("\n开始训练 MLP...")
    backend_used = args.backend
    model = None
    history = None

    if args.backend in ("auto", "keras"):
        try:
            model, history = train_model_keras(
                data=data,
                hidden1=args.hidden1,
                hidden2=args.hidden2,
                epochs=args.epochs,
                batch_size=args.batch_size,
                learning_rate=args.learning_rate,
                seed=args.seed,
                out_dir=out_dir,
            )
            backend_used = "keras"
        except Exception as exc:
            if args.backend == "keras":
                raise
            print(f"Keras 后端不可用，切换到 numpy 兜底训练。原因: {type(exc).__name__}: {exc}")

    if model is None or history is None:
        model, history = train_model(
            data=data,
            hidden1=args.hidden1,
            hidden2=args.hidden2,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            seed=args.seed,
        )
        backend_used = "numpy"

    save_outputs(out_dir, input_csv, data, model, history, backend_used)


if __name__ == "__main__":
    main()
