# Gradle Bench

This directory contains scripts for preparing the Gradle SWE-bench dataset.

## Test Generation Workflow

1. Start with a raw dataset for which Docker images have been built.
2. Run the preprocessing script to prepare the dataset for the agent:
   ```bash
   python gradle-bench/preprocess_dataset.py [json_file]
   ```
3. Run the agent to generate tests:
   ```bash
   bash test_swe_bench.sh
   ```
4. Merge the generated test patches back into the dataset:
   ```bash
   python gradle-bench/populate_test_patches.py
   ```

## Scripts

### `preprocess_dataset.py`

Prepares a raw dataset file for use with SWE-agent by enriching each entry with metadata required by the agent. Backs up the original file before making changes.

```bash
python preprocess_dataset.py [json_file]
```

### `populate_test_patches.py`

Takes model-generated test patches produced by a SWE-agent run and merges them into the dataset. 
Produces a new dataset file that contains the entries for which a test patch was generated.

```bash
python populate_test_patches.py
```
