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


ARCH_TO_PLATFORM = {
    "arm64": "linux/arm64/v8",
    "x86_64": "linux/amd64",
}


def _extract_arch(image_name: str) -> str:
    """Extract the architecture from a resolved image name like 'sweb.eval.arm64.foo:latest'."""
    parts = image_name.split(".")
    # Format: sweb.eval.<arch>.<instance_id>:latest
    if len(parts) >= 3:
        return parts[2]
    return "unknown"


def group_by_arch(json_path: Path) -> dict[str, list[dict]]:
    """Read the dataset and group instances by the arch in their image_name."""
    with open(json_path) as f:
        instances = json.load(f)
    groups: dict[str, list[dict]] = {}
    for instance in instances:
        arch = _extract_arch(instance.get("image_name", ""))
        groups.setdefault(arch, []).append(instance)
    return groups


def run_generate(
    model_name: str,
    dataset_path: Path,
    platform: str,
    project_root: Path,
) -> None:
    """Run agent_generate_tests.sh for a single arch group."""
    dataset_rel = str(dataset_path.relative_to(project_root))
    result = subprocess.run(
        ["bash", "gradle-bench/agent_generate_tests.sh", model_name, dataset_rel, platform],
        cwd=project_root,
    )
    # Don't exit on failure -- SWE-agent writes partial results for instances that succeeded
    if result.returncode != 0:
        print(f"  Warning: batch exited with code {result.returncode} (partial results may exist)")


def merge_preds(
    arch_groups: dict[str, list[dict]],
    tmp_files: dict[str, Path],
    original_stem: str,
    trajectories_dir: Path,
) -> None:
    """Find preds.json from each arch batch and merge into one file
    under a trajectory directory named after the original dataset stem."""
    merged: dict = {}
    for arch, tmp_path in tmp_files.items():
        stem = tmp_path.stem
        matches = [p for p in trajectories_dir.rglob("preds.json") if stem in p.parent.name]
        if not matches:
            print(f"  Warning: no preds.json found for {arch} batch")
            continue
        preds_path = max(matches, key=lambda p: p.stat().st_mtime)
        with open(preds_path) as f:
            merged.update(json.load(f))

    # Write merged preds into a directory the collect step can find by original stem
    merged_dir = trajectories_dir / f"merged___{original_stem}"
    merged_dir.mkdir(parents=True, exist_ok=True)
    with open(merged_dir / "preds.json", "w") as f:
        json.dump(merged, f, indent=4)
    print(f"  Merged predictions from {len(tmp_files)} batches ({len(merged)} instances)")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    dataset_file = f"data/{sys.argv[1]}" if len(sys.argv) > 1 else "data/gradle_dataset_verified.json"
    model_name = sys.argv[2] if len(sys.argv) > 2 else "claude-sonnet-4-6"
    dataset_path = script_dir / dataset_file

    print("=== Step 1: Preprocessing dataset ===")
    run(
        [sys.executable, "preprocess_dataset.py", dataset_file],
        cwd=script_dir,
    )

    print("\n=== Step 1b: Resolving image architecture ===")
    resolve_arch(dataset_path)

    print("\n=== Step 2: Generating test patches with SWE-agent ===")
    arch_groups = group_by_arch(dataset_path)

    if len(arch_groups) == 1:
        # Single-arch fast path: no temp files, no merge
        arch = next(iter(arch_groups))
        platform = ARCH_TO_PLATFORM.get(arch, "linux/amd64")
        run_generate(model_name, dataset_path, platform, project_root)
    else:
        # Multi-arch: split, run per group, merge
        counts = ", ".join(f"{len(insts)} {arch}" for arch, insts in arch_groups.items())
        print(f"Mixed architectures detected: {counts}")

        tmp_files: dict[str, Path] = {}
        for arch, instances in arch_groups.items():
            platform = ARCH_TO_PLATFORM.get(arch, "linux/amd64")
            tmp_path = dataset_path.parent / f".tmp_{arch}.json"
            with open(tmp_path, "w") as f:
                json.dump(instances, f, indent=2)
            tmp_files[arch] = tmp_path

            print(f"\nRunning {arch} batch ({platform})...")
            run_generate(model_name, tmp_path, platform, project_root)

        print("\nMerging predictions...")
        trajectories_dir = project_root / "trajectories"
        merge_preds(arch_groups, tmp_files, dataset_path.stem, trajectories_dir)

        # Cleanup temp files
        for tmp_path in tmp_files.values():
            tmp_path.unlink(missing_ok=True)

    print("\n=== Step 3: Populating dataset with test patches ===")
    run(
        [sys.executable, "populate_test_patches.py", dataset_file],
        cwd=script_dir,
    )

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()
