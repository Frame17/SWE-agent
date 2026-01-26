# Gradle Test Generation Configuration

## Overview

This configuration (`gradle_test_generation.yaml`) is designed to generate Gradle Test Kit tests that verify build script changes in SWE-bench instances.

## Purpose

The agent receives a repository with a gradle configuration change (gold patch) and generates test code that:
- **FAILS** when run against the original (broken) build script
- **PASSES** when run against the modified (fixed) build script

## How It Works

1. **Input**: An SWE-bench instance containing:
   - A repository with gradle configuration files
   - A gold patch showing the fix to the build script
   - A problem statement describing the issue

2. **Agent Behavior**: The agent will:
   - Analyze the diff to understand what changed
   - Determine the appropriate verification strategy
   - Generate a `BuildScriptTest.java` test class using Gradle Test Kit
   - Ensure minimal test setup (only settings.gradle.kts and build file copy)
   - Output a test patch

3. **Output**: A test patch containing the generated test file

## Usage

```bash
python -m sweagent.run.run_single \
  --config config/gradle_test_generation.yaml \
  --instance_filter <instance_id> \
  --model <model_name>
```

Or for batch processing:

```bash
python -m sweagent.run.run_batch \
  --config config/gradle_test_generation.yaml \
  --dataset <dataset_path> \
  --model <model_name>
```

## Key Features

### Tools Included
- **registry**: Environment and file management
- **edit_anthropic**: Advanced file editing capabilities
- **search**: File and content search tools
- **submit**: For finalizing the test patch

### Special Constraints

The configuration enforces minimal test setup to avoid:
- Creating unnecessary source directories
- Adding Android-specific files
- Creating gradle.properties or other config files
- Setting up complex project structures

The agent focuses solely on generating the test logic that verifies the specific gradle configuration change.

## Test Structure

Generated tests follow this pattern:

```java
public class BuildScriptTest {
    @TempDir
    Path tempDir;

    @Test
    public void testSpecificChange() throws IOException {
        // 1. Load build file from system property
        // 2. Setup minimal project (settings.gradle.kts only)
        // 3. Copy build file
        // 4. Run GradleRunner with appropriate arguments
        // 5. Assert on specific outputs
    }
}
```

## Environment Variables

The configuration sets several environment variables to ensure clean output:
- `PAGER=cat`, `MANPAGER=cat`: No interactive pagers
- `LESS=-R`: Raw output
- `PIP_PROGRESS_BAR=off`, `TQDM_DISABLE=1`: Disable progress bars
- `GIT_PAGER=cat`: Git output without paging

## Template Variables

The instance template uses these SWE-agent template variables:
- `{{working_dir}}`: The repository directory
- `{{problem_statement}}`: The issue description / task

## History Processing

The configuration uses cache control for the last 2 messages to optimize LLM context usage.

## Related Files

- `config/gradle_test_generation.txt`: Original prompt template with detailed examples
- `config/default.yaml`: Reference configuration showing standard SWE-agent setup
