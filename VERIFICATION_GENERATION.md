# Verification Generation Documentation

This document describes the steps required to generate verification trajectories for the Gradle SWE-bench dataset.

## Files

### 1. preprocess_dataset.py

Preprocesses SWE-bench format JSON dataset instances to prepare them for use with SWE-agent

#### Functionality

The script performs preprocessing operations on each instance in the dataset:

1. **Adds `image_name` field**: Generates a Docker image name for each instance following the standard SWE-bench naming convention:
   ```
   sweb.eval.x86_64.{instance_id.lower()}:latest
   ```

2. **Appends newline to patches**: Ensures each `patch` field ends with a newline character (`\n`) for proper formatting
3. **Adds static repo name for the agent**: Sets `repo_name` to `testbed` for all instances

#### Usage

```bash
# Process the default file (gradle_prs_swe_bench_trimmed.json)
python preprocess_dataset.py

# Process a specific file
python preprocess_dataset.py path/to/your/dataset.json
```

## Workflow

1. **Preprocess the dataset** (if not already done):
   ```bash
   python preprocess_dataset.py
   ```

2. **Run SWE-agent** on the preprocessed instances:
   ```bash
   bin/bash test_swe_bench.sh
   ```

3. **Review results** in the `trajectories/` directory

---

## Dependencies

### For preprocess_dataset.py
- Python 3.6+
- Standard library only (no external dependencies)

### For using the dataset
- SWE-agent framework
- Docker (for running test environments)
- Access to Claude Sonnet 4.5 API (or other supported LLM)

----