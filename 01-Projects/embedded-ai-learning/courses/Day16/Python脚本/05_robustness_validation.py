"""Run V2 rotation, perturbation, session, and relabeled-tail checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

from pipeline_common import (
    BASE_CHANNELS,
    CLASS_NAMES,
    PipelineConfig,
    classification_metrics,
    extract_feature_table,
    extract_frequency_features,
    extract_time_features,
    feature_columns,
    iter_windows,
    load_all_clean_data,
    resample_clean_frame,
    split_frame_by_time,
    write_json,
)


MODEL_KEYS = ("time_only", "time_frequency")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--cutoff-json", type=Path, required=True)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--training-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def random_rotation(rng: np.random.Generator) -> np.ndarray:
    matrix = rng.normal(size=(3, 3))
    q, r = np.linalg.qr(matrix)
    q = q @ np.diag(np.sign(np.diag(r)))
    if np.linalg.det(q) < 0:
        q[:, 0] *= -1
    return q


def rotate_window(window: pd.DataFrame, rotation: np.ndarray) -> pd.DataFrame:
    result = window.copy()
    linear = result[["lin_x", "lin_y", "lin_z"]].to_numpy(dtype=np.float64)
    gyro = result[["gyro_x", "gyro_y", "gyro_z"]].to_numpy(dtype=np.float64)
    linear_rotated = linear @ rotation.T
    gyro_rotated = gyro @ rotation.T
    result[["lin_x", "lin_y", "lin_z"]] = linear_rotated
    result[["gyro_x", "gyro_y", "gyro_z"]] = gyro_rotated
    result["lin_norm"] = np.linalg.norm(linear_rotated, axis=1)
    result["gyro_norm"] = np.linalg.norm(gyro_rotated, axis=1)
    # Delta norms already include the sample immediately before this window.
    # A rigid rotation cannot change those norms, so retain the original values.
    return result


def full_feature_vector(
    window: pd.DataFrame,
    include_frequency: bool,
    sample_rate_hz: float,
) -> tuple[list[str], np.ndarray]:
    names, values = extract_time_features(window)
    if include_frequency:
        frequency_names, frequency_values = extract_frequency_features(
            window,
            sample_rate_hz,
        )
        names.extend(frequency_names)
        values = np.concatenate((values, frequency_values))
    return names, values


def apply_preprocessing(
    table: pd.DataFrame,
    preprocessing: dict[str, object],
) -> np.ndarray:
    names = list(preprocessing["selected_feature_names"])
    matrix = table[names].to_numpy(dtype=np.float64)
    low = np.asarray(preprocessing["clip_low_selected"], dtype=np.float64)
    high = np.asarray(preprocessing["clip_high_selected"], dtype=np.float64)
    mean = np.asarray(preprocessing["normalization_mean"], dtype=np.float64)
    std = np.asarray(preprocessing["normalization_std"], dtype=np.float64)
    return ((np.clip(matrix, low, high) - mean) / std).astype(np.float32)


def noise_validation(
    model: tf.keras.Model,
    x_test: np.ndarray,
    y_test: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, object]:
    baseline = np.argmax(model.predict(x_test, verbose=0), axis=1)
    output: dict[str, object] = {}
    for sigma in (0.02, 0.05, 0.10):
        accuracies: list[float] = []
        agreements: list[float] = []
        for _ in range(20):
            perturbed = x_test + rng.normal(0.0, sigma, size=x_test.shape)
            prediction = np.argmax(model.predict(perturbed, verbose=0), axis=1)
            accuracies.append(float(np.mean(prediction == y_test)))
            agreements.append(float(np.mean(prediction == baseline)))
        output[str(sigma)] = {
            "mean_accuracy": float(np.mean(accuracies)),
            "minimum_accuracy": float(np.min(accuracies)),
            "mean_prediction_agreement_with_baseline": float(
                np.mean(agreements)
            ),
            "minimum_prediction_agreement_with_baseline": float(
                np.min(agreements)
            ),
        }
    return output


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = PipelineConfig()
    frames = load_all_clean_data(args.data_root.resolve())
    cutoff = json.loads(args.cutoff_json.read_text(encoding="utf-8"))
    transition_start_ms = float(cutoff["transition_start_ms"])
    transition_end_ms = float(cutoff["transition_end_ms"])

    rng = np.random.default_rng(config.random_seed)
    rotation_errors: dict[str, list[float]] = {
        "time_only": [],
        "time_frequency": [],
    }
    for class_name in CLASS_NAMES:
        frame = resample_clean_frame(frames[class_name], config)
        if class_name == "stairs":
            frame = frame[
                frame["t_ms"] < transition_start_ms
            ].reset_index(drop=True)
        windows = list(iter_windows(frame, config))
        indices = np.linspace(
            0,
            len(windows) - 1,
            min(20, len(windows)),
            dtype=int,
        )
        for index in indices:
            window = windows[index][1]
            rotated = rotate_window(window, random_rotation(rng))
            for model_key, include_frequency in (
                ("time_only", False),
                ("time_frequency", True),
            ):
                names, original = full_feature_vector(
                    window,
                    include_frequency,
                    config.target_sample_rate_hz,
                )
                rotated_names, transformed = full_feature_vector(
                    rotated,
                    include_frequency,
                    config.target_sample_rate_hz,
                )
                if names != rotated_names:
                    raise RuntimeError("Rotation test changed feature order")
                denominator = np.maximum(1.0, np.abs(original))
                rotation_errors[model_key].append(
                    float(np.max(np.abs(original - transformed) / denominator))
                )

    full_stairs = resample_clean_frame(frames["stairs"], config)
    tail = full_stairs[
        full_stairs["t_ms"] >= transition_end_ms
    ].copy()
    tail["label_id"] = 1
    tail["label"] = "walk"
    tail = tail.reset_index(drop=True)
    transition = full_stairs[
        (full_stairs["t_ms"] >= transition_start_ms)
        & (full_stairs["t_ms"] < transition_end_ms)
    ].reset_index(drop=True)
    if len(tail) < config.window_samples:
        raise ValueError("Known walking tail is too short for validation")

    results: dict[str, object] = {}
    for model_key in MODEL_KEYS:
        training_model_dir = args.training_dir / model_key
        model = tf.keras.models.load_model(
            training_model_dir / "model_float32.keras"
        )
        preprocessing = json.loads(
            (training_model_dir / "preprocessing.json").read_text(
                encoding="utf-8"
            )
        )
        dataset = np.load(
            training_model_dir / "normalized_selected_dataset.npz",
            allow_pickle=False,
        )
        x_test = dataset["x_test"].astype(np.float32)
        y_test = dataset["y_test"].astype(np.int64)
        source_class_test = dataset["source_class_test"].astype(str)

        include_frequency = model_key == "time_frequency"
        tail_features = extract_feature_table(
            tail,
            config,
            include_frequency=include_frequency,
            split_name="known_mislabeled_tail",
            source_class="stairs_tail_confirmed_walk",
        )
        tail_input = apply_preprocessing(tail_features, preprocessing)
        tail_probabilities = model.predict(tail_input, verbose=0)
        tail_prediction = np.argmax(tail_probabilities, axis=1)
        tail_output = tail_features[
            ["window_index", "start_ms", "end_ms"]
        ].copy()
        for class_id, class_name in enumerate(CLASS_NAMES):
            tail_output[f"probability_{class_name}"] = tail_probabilities[
                :,
                class_id,
            ]
        tail_output["predicted_id"] = tail_prediction
        tail_output["predicted_label"] = [
            CLASS_NAMES[index] for index in tail_prediction
        ]
        tail_output.to_csv(
            output_dir / f"{model_key}_known_walk_tail_predictions.csv",
            index=False,
            encoding="utf-8-sig",
        )
        tail_distribution = {
            class_name: int(np.sum(tail_prediction == class_id))
            for class_id, class_name in enumerate(CLASS_NAMES)
        }
        tail_distribution_fraction = {
            class_name: count / len(tail_prediction)
            for class_name, count in tail_distribution.items()
        }

        baseline_prediction = np.argmax(
            model.predict(x_test, verbose=0),
            axis=1,
        )
        test_metrics_by_session: dict[str, object] = {}
        for session_name in np.unique(source_class_test):
            session_mask = source_class_test == session_name
            test_metrics_by_session[session_name] = classification_metrics(
                y_test[session_mask],
                baseline_prediction[session_mask],
            )

        transition_result: dict[str, object] = {
            "window_count": 0,
            "note": "Transition is excluded from supervised scoring.",
        }
        if len(transition) >= config.window_samples:
            transition_features = extract_feature_table(
                transition,
                config,
                include_frequency=include_frequency,
                split_name="transition_excluded",
                source_class="stairs_to_walk_transition",
            )
            transition_input = apply_preprocessing(
                transition_features,
                preprocessing,
            )
            transition_probabilities = model.predict(
                transition_input,
                verbose=0,
            )
            transition_prediction = np.argmax(
                transition_probabilities,
                axis=1,
            )
            transition_result = {
                "window_count": int(len(transition_prediction)),
                "predicted_counts": {
                    class_name: int(
                        np.sum(transition_prediction == class_id)
                    )
                    for class_id, class_name in enumerate(CLASS_NAMES)
                },
                "mean_probabilities": {
                    class_name: float(
                        np.mean(transition_probabilities[:, class_id])
                    )
                    for class_id, class_name in enumerate(CLASS_NAMES)
                },
                "note": (
                    "These mixed-action windows were excluded from training "
                    "and are reported diagnostically without an expected label."
                ),
            }
        results[model_key] = {
            "baseline_test_metrics": classification_metrics(
                y_test,
                baseline_prediction,
            ),
            "test_metrics_by_recording_session": test_metrics_by_session,
            "rotation_invariance": {
                "tested_windows": len(rotation_errors[model_key]),
                "maximum_relative_feature_error": float(
                    np.max(rotation_errors[model_key])
                ),
                "mean_relative_feature_error": float(
                    np.mean(rotation_errors[model_key])
                ),
                "acceptance_limit": 1e-5,
                "passed": bool(np.max(rotation_errors[model_key]) < 1e-5),
            },
            "normalized_input_noise": noise_validation(
                model,
                x_test,
                y_test,
                rng,
            ),
            "confirmed_walk_tail_after_transition": {
                "window_count": int(len(tail_prediction)),
                "predicted_counts": tail_distribution,
                "predicted_fractions": tail_distribution_fraction,
                "mean_probabilities": {
                    class_name: float(np.mean(tail_probabilities[:, class_id]))
                    for class_id, class_name in enumerate(CLASS_NAMES)
                },
                "expected_dominant_prediction": "walk",
                "caution": (
                    "This short user-confirmed hard segment is training-only "
                    "in V2. Its score verifies coverage, not independent "
                    "generalization. Generalization is assessed on untouched "
                    "walk_main and stairs_core test windows."
                ),
            },
            "excluded_transition_diagnostics": transition_result,
        }

    write_json(output_dir / "robustness_validation.json", results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
