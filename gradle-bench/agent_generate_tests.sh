MODEL_NAME="${1:-claude-sonnet-4-6}"
DATASET_FILE="${2:-gradle-bench/data/gradle_dataset_verified.json}"
PLATFORM="${3:-linux/amd64}"

# Select config based on model provider
case "$MODEL_NAME" in
  gemini/*) CONFIG="config/gradle_test_generation_gemini.yaml" ;;
  *)        CONFIG="config/gradle_test_generation.yaml" ;;
esac

${PYTHON:-python3} -m sweagent.run.run_batch \
  --config "$CONFIG" \
  --instances.type file \
  --instances.path "$DATASET_FILE" \
  --instances.deployment.platform "$PLATFORM" \
  --agent.model.name "$MODEL_NAME" \
  --num_workers 5
