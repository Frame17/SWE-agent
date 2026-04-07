# Gradle Bench

Scripts for building a Gradle SWE-bench dataset enriched with model-generated test patches.

## Overview

The pipeline takes a raw Gradle dataset and produces a refined dataset where every entry contains a model-generated test patch. It consists of three stages:

1. **Prepare** — enrich the raw dataset so the agent can run against it.
2. **Generate** — run the SWE-agent to produce test patches for each issue.
3. **Collect** — merge the generated patches back into the dataset, keeping only entries for which a patch was produced.

When the dataset contains images built for different architectures (e.g. arm64 and x86_64), the pipeline automatically splits them into per-arch batches, runs each with the correct Docker platform, and merges the results before stage 3.

Run the full pipeline with:

```bash
python run_pipeline.py [json_file] [model_name]
```

- `json_file` — dataset filename inside `data/` (default: `gradle_dataset_verified.json`)
- `model_name` — LLM model to use for test generation (default: `claude-sonnet-4-6`). Accepts any model supported by [litellm](https://docs.litellm.ai/docs/providers) (e.g. `claude-opus-4-6`, `gpt-4o`, `gemini/gemini-2.5-flash`). Requires the corresponding API key in the environment (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`).

Example:

```bash
python run_pipeline.py gradle_dataset_verified_sample.json claude-opus-4-6
```

---

## Pipeline Stages

### 1. Prepare — `preprocess_dataset.py`

**Input:** a raw JSON dataset (list of SWE-bench instances) in `data/`.
**Output:** the same file updated in-place.

Adds two fields that SWE-agent requires but are absent from the raw export:

| Field | Value |
|---|---|
| `image_name` | Docker image tag derived from `instance_id`, with `{arch}` placeholder |
| `repo_name` | Fixed to `testbed` (the in-container checkout path) |

Also ensures every `patch` value ends with a newline, as required by the patch-apply tooling.

The `image_name` uses a literal `{arch}` placeholder (e.g. `sweb.eval.{arch}.aliucord__aliucord-556:latest`) so the dataset remains portable across architectures. The placeholder is resolved at runtime by probing Docker for the actual image — the host architecture is tried first, then the alternative (`x86_64` on ARM hosts, `arm64` on x86 hosts). This handles repos that force a specific architecture (e.g. projects using older Kotlin/Native versions that only ship x86_64 binaries).

---

### 2. Generate — `agent_generate_tests.sh`

**Input:** the preprocessed dataset produced in stage 1.
**Output:** a `preds.json` file written to the trajectory directory under `trajectories/`.

**Arguments:** `<model_name> <dataset_file> <platform>`

- `model_name` -- LLM model (default: `claude-sonnet-4-6`)
- `dataset_file` -- path to the dataset JSON (default: `gradle-bench/data/gradle_dataset_verified.json`)
- `platform` -- Docker platform string (default: `linux/amd64`). Use `linux/arm64/v8` for native ARM images.

Runs `sweagent.run.run_batch` using the `gradle_test_generation` config (or `gradle_test_generation_gemini` for Gemini models). The agent is given each issue and asked to write a test that reproduces it. Results (one patch file per instance) are accumulated in a trajectory directory and summarised in `preds.json`.

When run via `run_pipeline.py`, the platform argument is set automatically based on each batch's architecture. When run standalone, it defaults to `linux/amd64`.

---

### 3. Collect — `populate_test_patches.py`

**Input:** the preprocessed dataset and the `preds.json` from stage 2.
**Output:** a new JSON file (`data/<stem>_with_test_patch.json`) containing only the instances for which the agent produced a non-empty test patch.

Reads the agent predictions, copies the `model_patch` value into the `test_patch` field of each matching dataset entry, and writes the filtered result to the output file. The `preds.json` is resolved automatically from `trajectories/` by matching the dataset filename stem; the most recently modified match is used.

---

## Running Individual Stages

Each stage can also be run independently from the project root:

```bash
# Stage 1
python gradle-bench/preprocess_dataset.py data/gradle_dataset_verified.json

# Stage 2 -- args: [model_name] [dataset_file] [platform]
bash gradle-bench/agent_generate_tests.sh claude-sonnet-4-6 gradle-bench/data/gradle_dataset_verified.json linux/arm64/v8

# Stage 3
python gradle-bench/populate_test_patches.py data/gradle_dataset_verified.json
```
