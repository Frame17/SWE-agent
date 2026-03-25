MODEL_NAME="${1:-claude-sonnet-4-6}"
DATASET_FILE="${2:-gradle-bench/data/gradle_dataset_verified.json}"

python -m sweagent.run.run_batch \
  --config config/gradle_test_generation.yaml \
  --instances.type file \
  --instances.path "$DATASET_FILE" \
  --agent.model.name "$MODEL_NAME" \
  --num_workers 5
