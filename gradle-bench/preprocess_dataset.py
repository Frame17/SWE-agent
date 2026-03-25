#!/usr/bin/env python3
"""
Script to preprocess SWE-bench format JSON dataset instances.

This script reads a JSON file containing SWE-bench instances and performs
preprocessing steps:
1. Adds an 'image_name' field to each instance based on the instance_id
2. Appends a newline character to the 'patch' field

The image names follow the standard SWE-bench Docker image naming convention.

Usage:
    python preprocess_dataset.py [json_file]

If no file is specified, defaults to 'gradle_prs_swe_bench_trimmed.json'
"""

import json
import sys
from pathlib import Path


def preprocess_dataset(json_path='gradle_prs_swe_bench_trimmed.json'):
    """Preprocess SWE-bench dataset instances.
    
    Adds image_name and repo_name fields and appends newlines to patch fields.
    
    Args:
        json_path: Path to the JSON file containing instances
    """
    json_path = Path(json_path)
    
    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    
    # Load the JSON file
    print(f"Loading instances from: {json_path}")
    with open(json_path, 'r') as f:
        instances = json.load(f)
    
    print(f"Processing {len(instances)} instances...\n")
    
    # Preprocess each instance
    for i, instance in enumerate(instances, 1):
        instance_id = instance['instance_id']

        # Standard SWE-bench image naming convention
        image_name = f'sweb.eval.x86_64.{instance_id.lower()}:latest'
        instance['image_name'] = image_name
        
        # Add repo_name field
        instance['repo_name'] = 'testbed'
        
        # Add newline to patch field
        if 'patch' in instance and instance['patch']:
            if not instance['patch'].endswith('\n'):
                instance['patch'] += '\n'
        
        print(f"  [{i:2d}] {instance_id:50s} → {image_name}")
    
    # Save updated JSON in-place
    with open(json_path, 'w') as f:
        json.dump(instances, f, indent=2)
    
    print(f"\n✓ Updated JSON saved to: {json_path}")
    print(f"\n{len(instances)} instances preprocessed successfully!")


if __name__ == '__main__':
    # Get JSON file path from command line argument or use default
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'gradle_prs_swe_bench_with_tests.json'
    preprocess_dataset(json_file)
