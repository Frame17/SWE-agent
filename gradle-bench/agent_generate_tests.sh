MODEL_NAME="${1:-claude-sonnet-4-6}"
DATASET_FILE="${2:-gradle-bench/data/gradle_dataset_verified.json}"

# Resolve {arch} placeholders by probing Docker for the actual image architecture
# Normalize: Linux ARM reports "aarch64" but Docker image tags use "arm64"
HOST_ARCH="$(uname -m)"
case "$HOST_ARCH" in aarch64) HOST_ARCH="arm64" ;; esac
python -c "
import json, subprocess
host_arch = '$HOST_ARCH'
candidates = [host_arch, 'x86_64'] if host_arch != 'x86_64' else [host_arch, 'arm64']
with open('$DATASET_FILE') as f:
    data = json.load(f)
changed = False
for inst in data:
    if '{arch}' not in inst.get('image_name', ''):
        continue
    resolved = False
    for arch in candidates:
        candidate = inst['image_name'].replace('{arch}', arch)
        if subprocess.run(['docker', 'inspect', candidate], capture_output=True).returncode == 0:
            inst['image_name'] = candidate
            print(f'  {inst[\"instance_id\"]:50s} -> {arch}')
            resolved = True
            changed = True
            break
    if not resolved:
        inst['image_name'] = inst['image_name'].replace('{arch}', host_arch)
        print(f'  {inst[\"instance_id\"]:50s} -> {host_arch} (no image found)')
        changed = True
if changed:
    with open('$DATASET_FILE', 'w') as f:
        json.dump(data, f, indent=2)
"

# Select config based on model provider
case "$MODEL_NAME" in
  gemini/*) CONFIG="config/gradle_test_generation_gemini.yaml" ;;
  *)        CONFIG="config/gradle_test_generation.yaml" ;;
esac

# If any instance uses an x86_64 image, set platform to linux/amd64 so Docker
# uses QEMU emulation for those while still running arm64 images natively.
if grep -q 'x86_64' "$DATASET_FILE"; then
  PLATFORM="linux/amd64"
else
  case "$(uname -m)" in
    arm64|aarch64) PLATFORM="linux/arm64/v8" ;;
    *)             PLATFORM="linux/amd64" ;;
  esac
fi

python -m sweagent.run.run_batch \
  --config "$CONFIG" \
  --instances.type file \
  --instances.path "$DATASET_FILE" \
  --instances.deployment.platform "$PLATFORM" \
  --agent.model.name "$MODEL_NAME" \
  --num_workers 5
