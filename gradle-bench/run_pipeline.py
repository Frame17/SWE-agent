#!/usr/bin/env python3
"""
Full pipeline for gradle-bench test generation:
  1. Preprocess the dataset (adds image_name, repo_name, normalises patch fields)
  2. Run the SWE-agent batch job to generate test patches
  3. Merge generated patches back into the dataset

Usage:
    python run_pipeline.py [json_file] [model_name]

If no file is specified, defaults to 'data/gradle_dataset_verified.json'.
If no model is specified, defaults to 'claude-sonnet-4-6'.
"""

import json
import platform
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def _docker_image_exists(image: str) -> bool:
    return (
        subprocess.run(
            ["docker", "inspect", image],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def resolve_arch(json_path: Path) -> None:
    """Replace {arch} placeholders by probing Docker for the actual image architecture."""
    host_arch = platform.machine()
    # Normalize: Linux ARM reports "aarch64" but Docker image tags use "arm64"
    if host_arch == "aarch64":
        host_arch = "arm64"
    candidates = [host_arch, "x86_64"] if host_arch != "x86_64" else [host_arch, "arm64"]

    with open(json_path) as f:
        instances = json.load(f)
    for instance in instances:
        if "{arch}" not in instance.get("image_name", ""):
            continue
        for arch in candidates:
            candidate = instance["image_name"].replace("{arch}", arch)
            if _docker_image_exists(candidate):
                instance["image_name"] = candidate
                print(f"  {instance['instance_id']:50s} → {arch}")
                break
        else:
            instance["image_name"] = instance["image_name"].replace("{arch}", host_arch)
            print(f"  {instance['instance_id']:50s} → {host_arch} (no image found)")
    with open(json_path, "w") as f:
        json.dump(instances, f, indent=2)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    dataset_file = f"data/{sys.argv[1]}" if len(sys.argv) > 1 else "data/gradle_dataset_verified.json"
    model_name = sys.argv[2] if len(sys.argv) > 2 else "claude-sonnet-4-6"

    print("=== Step 1: Preprocessing dataset ===")
    run(
        [sys.executable, "preprocess_dataset.py", dataset_file],
        cwd=script_dir,
    )

    print("\n=== Step 1b: Resolving image architecture ===")
    resolve_arch(script_dir / dataset_file)

    print("\n=== Step 2: Generating test patches with SWE-agent ===")
    run(
        ["bash", "gradle-bench/agent_generate_tests.sh", model_name, f"gradle-bench/{dataset_file}"],
        cwd=project_root,
    )

    print("\n=== Step 3: Populating dataset with test patches ===")
    run(
        [sys.executable, "populate_test_patches.py", dataset_file],
        cwd=script_dir,
    )

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()
