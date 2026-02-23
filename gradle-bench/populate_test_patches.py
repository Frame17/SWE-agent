#!/usr/bin/env python3
"""Populate test_patch fields from model_patch in preds.json
and write only the entries with a non-empty test_patch to a new output file."""

import json

DATASET_FILE = "../gradle_prs_swe_bench_trimmed.json"
OUTPUT_FILE = "../gradle_prs_swe_bench_trimmed_with_test_patch.json"
PREDS_FILE = (
    "../trajectories/fedusov.serhii/"
    "gradle_test_generation__claude-sonnet-4-6__t-0.00__p-None__c-3.00___gradle_prs_swe_bench_with_tests"
    "/preds.json"
)

with open(DATASET_FILE) as f:
    data = json.load(f)

with open(PREDS_FILE) as f:
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

with open(OUTPUT_FILE, "w") as f:
    json.dump(with_tests, f, indent=2)

print(f"Done. Updated: {updated}, Missing: {missing}, Written to output: {len(with_tests)}")
