"""Reproduce the complete Day12-to-Day16 model pipeline."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(r"D:\Codex_s\course\Day16-模型部署与推理\数据"),
    )
    parser.add_argument(
        "--day11-root",
        type=Path,
        default=Path(r"D:\Day11_code"),
    )
    parser.add_argument(
        "--validation-root",
        type=Path,
        default=Path(
            r"D:\Codex_s\course\Day16-模型部署与推理\02_验证V2"
        ),
    )
    return parser.parse_args()


def run_step(
    name: str,
    command: list[str],
    log_dir: Path,
) -> None:
    log_path = log_dir / f"{name}.log"
    print(f"[RUN] {name}")
    completed = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log_path.write_text(completed.stdout, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit code {completed.returncode}. "
            f"See {log_path}"
        )
    print(f"[OK ] {name}")


def main() -> None:
    args = parse_args()
    root = args.validation_root.resolve()
    delivery = root / "01_交付文件"
    process = root / "02_过程与中间文件"
    scripts = delivery / "Python脚本"
    snapshot = process / "00_输入数据快照"
    audit = process / "01_数据审计"
    features = process / "02_窗口与特征"
    training = process / "03_模型训练"
    validation = process / "04_模型验证"
    conversion = process / "05_量化与转换"
    staging = process / "06_端到端复核" / "交付暂存"
    logs = process / "07_运行日志"
    for path in (
        delivery,
        process,
        snapshot,
        audit,
        features,
        training,
        validation,
        conversion,
        staging,
        logs,
    ):
        path.mkdir(parents=True, exist_ok=True)

    snapshot_data = snapshot / "数据"
    shutil.copytree(
        args.data_root.resolve(),
        snapshot_data,
        dirs_exist_ok=True,
    )

    python = sys.executable
    run_step(
        "01_audit_dataset",
        [
            python,
            str(scripts / "01_audit_dataset.py"),
            "--data-root",
            str(args.data_root.resolve()),
            "--snapshot-root",
            str(snapshot),
            "--output-dir",
            str(audit),
            "--sample-rate",
            "40",
        ],
        logs,
    )
    run_step(
        "01b_analyze_stairs_tail",
        [
            python,
            str(scripts / "01b_analyze_stairs_tail.py"),
            "--data-root",
            str(args.data_root.resolve()),
            "--output-dir",
            str(audit),
        ],
        logs,
    )
    run_step(
        "02_build_features",
        [
            python,
            str(scripts / "02_build_features.py"),
            "--data-root",
            str(args.data_root.resolve()),
            "--output-dir",
            str(features),
            "--stairs-cutoff-json",
            str(audit / "stairs_tail_cutoff.json"),
            "--sample-rate",
            "40",
            "--window-samples",
            "64",
            "--hop-samples",
            "16",
        ],
        logs,
    )
    run_step(
        "03_train_models",
        [
            python,
            str(scripts / "03_train_models.py"),
            "--feature-dir",
            str(features),
            "--output-dir",
            str(training),
            "--delivery-dir",
            str(staging),
            "--epochs",
            "250",
            "--batch-size",
            "32",
        ],
        logs,
    )
    run_step(
        "04_convert_validate_tflite",
        [
            python,
            str(scripts / "04_convert_validate_tflite.py"),
            "--training-dir",
            str(training),
            "--output-dir",
            str(conversion),
            "--delivery-dir",
            str(staging),
        ],
        logs,
    )
    run_step(
        "05_robustness_validation",
        [
            python,
            str(scripts / "05_robustness_validation.py"),
            "--data-root",
            str(args.data_root.resolve()),
            "--cutoff-json",
            str(audit / "stairs_tail_cutoff.json"),
            "--feature-dir",
            str(features),
            "--training-dir",
            str(training),
            "--output-dir",
            str(validation),
        ],
        logs,
    )
    run_step(
        "06_build_deployment_package",
        [
            python,
            str(scripts / "06_build_deployment_package.py"),
            "--day11-root",
            str(args.day11_root.resolve()),
            "--audit-dir",
            str(audit),
            "--feature-dir",
            str(features),
            "--training-dir",
            str(training),
            "--validation-dir",
            str(validation),
            "--conversion-dir",
            str(conversion),
            "--delivery-root",
            str(delivery),
        ],
        logs,
    )
    print(f"Pipeline completed: {root}")


if __name__ == "__main__":
    main()
