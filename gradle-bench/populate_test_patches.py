#!/usr/bin/env python3
"""Populate test_patch fields from model_patch in preds.json
and write only the entries with a non-empty test_patch to a new output file.

Usage:
    python populate_test_patches.py [dataset_file]

If no file is specified, defaults to 'data/gradle_dataset_verified.json'.
The preds.json is resolved automatically from the trajectories/ directory by
matching the dataset stem; the most recently modified match is used.
"""

import json
import sys
from pathlib import Path


def find_preds_file(dataset_stem: str, trajectories_dir: Path) -> Path:
    """Find the most recently modified preds.json whose parent directory name
    contains the dataset stem."""
    matches = [
        p for p in trajectories_dir.rglob("preds.json")
        if dataset_stem in p.parent.name
    ]
    if not matches:
        raise FileNotFoundError(
            f"No preds.json found under '{trajectories_dir}' "
            f"matching dataset stem '{dataset_stem}'"
        )
    return max(matches, key=lambda p: p.stat().st_mtime)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    trajectories_dir = script_dir.parent / "trajectories"

    dataset_file = sys.argv[1] if len(sys.argv) > 1 else "data/gradle_dataset_verified.json"
    dataset_path = Path(dataset_file)
    dataset_stem = dataset_path.stem

    output_file = dataset_path.parent / (dataset_stem + "_with_test_patch.json")

    preds_path = find_preds_file(dataset_stem, trajectories_dir)
    print(f"Using preds: {preds_path}")

    with open(dataset_path) as f:
        data = json.load(f)

    with open(preds_path) as f:
        preds = json.load(f)

    patches = {entry["instance_id"]: entry["model_patch"] for entry in preds.values()}

    updated = 0
    missing = 0

    for entry in data:
        instance_id = entry["instance_id"]
        if instance_id in patches and patches[instance_id]:
            entry["test_patch"] = patches[instance_id]
            updated += 1
        else:
            missing += 1

    with_tests = [entry for entry in data if entry.get("test_patch", "")]

    with open(output_file, "w") as f:
        json.dump(with_tests, f, indent=2)

    print(f"Done. Updated: {updated}, Missing: {missing}, Written to output: {len(with_tests)}")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    main()
