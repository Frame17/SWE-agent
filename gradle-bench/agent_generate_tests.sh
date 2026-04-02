MODEL_NAME="${1:-claude-sonnet-4-6}"
DATASET_FILE="${2:-gradle-bench/data/gradle_dataset_verified.json}"

# Resolve {arch} placeholders in image_name fields to the current machine architecture
ARCH="$(uname -m)"
python -c "
import json, sys
with open('$DATASET_FILE') as f: data = json.load(f)
changed = False
for inst in data:
    if '{arch}' in inst.get('image_name', ''):
        inst['image_name'] = inst['image_name'].replace('{arch}', '$ARCH')
        changed = True
if changed:
    with open('$DATASET_FILE', 'w') as f: json.dump(data, f, indent=2)
    print(f'Resolved image architecture to $ARCH for {len(data)} instances')
"

python -m sweagent.run.run_batch \
  --config config/gradle_test_generation.yaml \
  --instances.type file \
  --instances.path "$DATASET_FILE" \
  --agent.model.name "$MODEL_NAME" \
  --num_workers 5
