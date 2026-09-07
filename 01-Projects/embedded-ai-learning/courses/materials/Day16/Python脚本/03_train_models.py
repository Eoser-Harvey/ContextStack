"""Train and select two compact feature-based action classifiers."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from pipeline_common import (
    CLASS_NAMES,
    classification_metrics,
    set_global_determinism,
    write_json,
)


MODEL_SPECS = {
    "time_only": {
        "dataset": "dataset_time_only.npz",
        "selected_feature_count": 40,
        "minimum_frequency_features": 0,
        "display_name": "Model A - time-domain features only",
    },
    "time_frequency": {
        "dataset": "dataset_time_frequency.npz",
        "selected_feature_count": 56,
        "minimum_frequency_features": 16,
        "display_name": "Model B - time and frequency features",
    },
}

CANDIDATE_ARCHITECTURES = (
    (24, 12),
    (32, 16),
    (48, 24),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--delivery-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


def fisher_scores(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    overall_mean = np.mean(x, axis=0)
    between = np.zeros(x.shape[1], dtype=np.float64)
    within = np.zeros(x.shape[1], dtype=np.float64)
    for class_id in range(len(CLASS_NAMES)):
        subset = x[y == class_id]
        class_mean = np.mean(subset, axis=0)
        between += len(subset) * (class_mean - overall_mean) ** 2
        within += np.sum((subset - class_mean) ** 2, axis=0)
    return between / (within + 1e-12)


def select_features(
    names: list[str],
    scores: np.ndarray,
    count: int,
    minimum_frequency: int,
    time_feature_count: int,
) -> np.ndarray:
    order = np.argsort(scores)[::-1]
    if minimum_frequency == 0:
        return np.sort(order[:count])

    frequency_indices = np.arange(time_feature_count, len(names), dtype=int)
    frequency_order = frequency_indices[
        np.argsort(scores[frequency_indices])[::-1]
    ]
    selected = list(frequency_order[:minimum_frequency])
    for index in order:
        if int(index) not in selected:
            selected.append(int(index))
        if len(selected) >= count:
            break
    return np.asarray(sorted(selected), dtype=int)


def calculate_class_weights(y: np.ndarray) -> dict[int, float]:
    total = len(y)
    weights: dict[int, float] = {}
    for class_id in range(len(CLASS_NAMES)):
        count = int(np.sum(y == class_id))
        weights[class_id] = total / (len(CLASS_NAMES) * max(1, count))
    return weights


def build_model(
    input_dim: int,
    hidden_units: tuple[int, int],
    seed: int,
) -> tf.keras.Model:
    regularizer = tf.keras.regularizers.l2(1e-4)
    inputs = tf.keras.Input(shape=(input_dim,), name="normalized_features")
    x = tf.keras.layers.Dense(
        hidden_units[0],
        activation="relu",
        kernel_regularizer=regularizer,
        name="dense_1",
    )(inputs)
    x = tf.keras.layers.Dropout(0.10, seed=seed, name="dropout_1")(x)
    x = tf.keras.layers.Dense(
        hidden_units[1],
        activation="relu",
        kernel_regularizer=regularizer,
        name="dense_2",
    )(x)
    outputs = tf.keras.layers.Dense(
        len(CLASS_NAMES),
        activation="softmax",
        name="class_probabilities",
    )(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def plot_history(history: dict[str, list[float]], output_path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(history["loss"], label="train")
    axes[0].plot(history["val_loss"], label="validation")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].grid(alpha=0.2)
    axes[0].legend()
    axes[1].plot(history["accuracy"], label="train")
    axes[1].plot(history["val_accuracy"], label="validation")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].grid(alpha=0.2)
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def plot_confusion(matrix: list[list[int]], output_path: Path, title: str) -> None:
    array = np.asarray(matrix, dtype=int)
    plt.figure(figsize=(6, 5))
    plt.imshow(array, cmap="Blues")
    plt.colorbar()
    for row in range(array.shape[0]):
        for column in range(array.shape[1]):
            plt.text(
                column,
                row,
                str(array[row, column]),
                ha="center",
                va="center",
                color="white" if array[row, column] > array.max() * 0.5 else "black",
            )
    plt.xticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    plt.yticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    plt.xlabel("Predicted")
    plt.ylabel("Expected")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def prepare_data(
    dataset_path: Path,
    minimum_frequency: int,
    selected_count: int,
    time_feature_count: int,
) -> tuple[dict[str, np.ndarray], dict[str, object], pd.DataFrame]:
    archive = np.load(dataset_path, allow_pickle=False)
    names = archive["feature_names"].astype(str).tolist()
    raw = {
        split: archive[f"x_{split}"].astype(np.float64)
        for split in ("train", "validation", "test")
    }
    labels = {
        split: archive[f"y_{split}"].astype(np.int64)
        for split in ("train", "validation", "test")
    }
    sources = {
        split: archive[f"source_class_{split}"].astype(str)
        for split in ("train", "validation", "test")
    }
    for split, matrix in raw.items():
        if not np.isfinite(matrix).all():
            raise ValueError(f"{dataset_path} has non-finite values in {split}")

    clip_low = np.percentile(raw["train"], 0.5, axis=0)
    clip_high = np.percentile(raw["train"], 99.5, axis=0)
    clipped = {
        split: np.clip(matrix, clip_low, clip_high)
        for split, matrix in raw.items()
    }
    score = fisher_scores(clipped["train"], labels["train"])
    selected_indices = select_features(
        names,
        score,
        selected_count,
        minimum_frequency,
        time_feature_count,
    )
    selected_names = [names[index] for index in selected_indices]

    train_selected = clipped["train"][:, selected_indices]
    mean = np.mean(train_selected, axis=0)
    std = np.std(train_selected, axis=0)
    std[std < 1e-6] = 1.0
    prepared: dict[str, np.ndarray] = {}
    for split in ("train", "validation", "test"):
        prepared[f"x_{split}"] = (
            clipped[split][:, selected_indices] - mean
        ) / std
        prepared[f"y_{split}"] = labels[split]
        prepared[f"source_class_{split}"] = sources[split]

    preprocessing = {
        "all_feature_count": len(names),
        "selected_feature_count": len(selected_names),
        "selected_indices": selected_indices.tolist(),
        "selected_feature_names": selected_names,
        "clip_low_selected": clip_low[selected_indices].tolist(),
        "clip_high_selected": clip_high[selected_indices].tolist(),
        "normalization_mean": mean.tolist(),
        "normalization_std": std.tolist(),
        "input_formula": (
            "normalized[i] = "
            "(clip(raw_feature[i], clip_low[i], clip_high[i]) - mean[i]) "
            "/ std[i]"
        ),
    }
    score_table = pd.DataFrame(
        {
            "feature_index": np.arange(len(names)),
            "feature_name": names,
            "fisher_score_train_only": score,
            "selected": [
                int(index in set(selected_indices.tolist()))
                for index in range(len(names))
            ],
        }
    ).sort_values("fisher_score_train_only", ascending=False)
    return prepared, preprocessing, score_table


def train_one_model(
    model_key: str,
    spec: dict[str, object],
    args: argparse.Namespace,
    time_feature_count: int,
) -> dict[str, object]:
    model_dir = args.output_dir / model_key
    model_dir.mkdir(parents=True, exist_ok=True)
    delivery_model_dir = args.delivery_dir / model_key
    delivery_model_dir.mkdir(parents=True, exist_ok=True)

    data, preprocessing, score_table = prepare_data(
        args.feature_dir / str(spec["dataset"]),
        int(spec["minimum_frequency_features"]),
        int(spec["selected_feature_count"]),
        time_feature_count,
    )
    score_table.to_csv(
        model_dir / "feature_selection_scores.csv",
        index=False,
        encoding="utf-8-sig",
    )
    write_json(model_dir / "preprocessing.json", preprocessing)

    class_weights = calculate_class_weights(data["y_train"])
    trial_records: list[dict[str, object]] = []
    best: dict[str, object] | None = None

    for candidate_index, architecture in enumerate(CANDIDATE_ARCHITECTURES):
        seed = 20260723 + candidate_index
        set_global_determinism(seed)
        tf.keras.backend.clear_session()
        model = build_model(
            data["x_train"].shape[1],
            architecture,
            seed,
        )
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=25,
                min_delta=1e-4,
                restore_best_weights=True,
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=10,
                min_lr=1e-5,
            ),
        ]
        history = model.fit(
            data["x_train"],
            data["y_train"],
            validation_data=(data["x_validation"], data["y_validation"]),
            epochs=args.epochs,
            batch_size=args.batch_size,
            class_weight=class_weights,
            callbacks=callbacks,
            verbose=0,
            shuffle=True,
        )
        validation_probabilities = model.predict(
            data["x_validation"],
            verbose=0,
        )
        validation_prediction = np.argmax(validation_probabilities, axis=1)
        validation_metrics = classification_metrics(
            data["y_validation"],
            validation_prediction,
        )
        record = {
            "candidate_index": candidate_index,
            "hidden_units": list(architecture),
            "seed": seed,
            "epochs_ran": len(history.history["loss"]),
            "parameter_count": int(model.count_params()),
            "validation_accuracy": validation_metrics["accuracy"],
            "validation_macro_f1": validation_metrics["macro_f1"],
            "minimum_validation_loss": float(min(history.history["val_loss"])),
        }
        trial_records.append(record)
        ranking = (
            float(validation_metrics["macro_f1"]),
            float(validation_metrics["accuracy"]),
            -int(model.count_params()),
        )
        if best is None or ranking > best["ranking"]:
            best = {
                "ranking": ranking,
                "model": model,
                "history": history.history,
                "record": record,
            }

    if best is None:
        raise RuntimeError("No candidate model was trained")
    selected_model = best["model"]
    history = best["history"]

    test_probabilities = selected_model.predict(data["x_test"], verbose=0)
    test_prediction = np.argmax(test_probabilities, axis=1)
    test_metrics = classification_metrics(data["y_test"], test_prediction)
    validation_probabilities = selected_model.predict(
        data["x_validation"],
        verbose=0,
    )
    validation_prediction = np.argmax(validation_probabilities, axis=1)
    validation_metrics = classification_metrics(
        data["y_validation"],
        validation_prediction,
    )

    selected_model.save(model_dir / "model_float32.keras")
    shutil.copy2(
        model_dir / "model_float32.keras",
        delivery_model_dir / "model_float32.keras",
    )
    write_json(delivery_model_dir / "preprocessing.json", preprocessing)
    pd.DataFrame(trial_records).to_csv(
        model_dir / "architecture_trials.csv",
        index=False,
        encoding="utf-8-sig",
    )
    np.savez_compressed(
        model_dir / "normalized_selected_dataset.npz",
        x_train=data["x_train"].astype(np.float32),
        y_train=data["y_train"],
        source_class_train=data["source_class_train"],
        x_validation=data["x_validation"].astype(np.float32),
        y_validation=data["y_validation"],
        source_class_validation=data["source_class_validation"],
        x_test=data["x_test"].astype(np.float32),
        y_test=data["y_test"],
        source_class_test=data["source_class_test"],
        class_names=np.asarray(CLASS_NAMES),
        selected_feature_names=np.asarray(
            preprocessing["selected_feature_names"]
        ),
    )
    plot_history(history, model_dir / "training_history.png")
    plot_confusion(
        test_metrics["confusion_matrix"],
        model_dir / "test_confusion_matrix.png",
        f"{spec['display_name']} - chronological test",
    )
    with contextlib.redirect_stdout(io.StringIO()) as capture:
        selected_model.summary()
    (model_dir / "model_summary.txt").write_text(
        capture.getvalue(),
        encoding="utf-8",
    )

    result = {
        "model_key": model_key,
        "display_name": spec["display_name"],
        "selected_architecture": best["record"],
        "class_weights": class_weights,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "preprocessing": preprocessing,
    }
    write_json(model_dir / "training_result.json", result)
    write_json(delivery_model_dir / "training_result.json", result)
    return result


def main() -> None:
    args = parse_args()
    args.feature_dir = args.feature_dir.resolve()
    args.output_dir = args.output_dir.resolve()
    args.delivery_dir = args.delivery_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.delivery_dir.mkdir(parents=True, exist_ok=True)

    time_archive = np.load(
        args.feature_dir / "dataset_time_only.npz",
        allow_pickle=False,
    )
    time_feature_count = len(time_archive["feature_names"])
    results = {}
    for model_key, spec in MODEL_SPECS.items():
        results[model_key] = train_one_model(
            model_key,
            spec,
            args,
            time_feature_count,
        )
    write_json(args.output_dir / "training_comparison.json", results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
