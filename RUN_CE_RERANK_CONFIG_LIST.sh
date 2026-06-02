#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 CONFIG_LIST"
  exit 1
fi

cd /workspace/long_context_cue

export PYTHONUNBUFFERED=1
export OLLAMA_NUM_PARALLEL=1

LIST="$1"
LOG_DIR="outputs/rerank_sensitivity_20260602/logs"
mkdir -p "$LOG_DIR"

while IFS= read -r cfg; do
  [ -z "$cfg" ] && continue
  name="$(basename "$cfg" .yaml)"
  echo "================================================================"
  echo "Running $name"
  echo "Config: $cfg"
  echo "================================================================"

  python scripts/run_retriever_family_ablation.py \
    --config "$cfg" \
    --run-reader \
    2>&1 | tee "$LOG_DIR/${name}.log"
done < "$LIST"
