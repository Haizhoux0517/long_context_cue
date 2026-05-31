#!/usr/bin/env bash
set -euo pipefail
for cfg in configs/ablations/reader_facing_retfam_*.yaml; do
  echo "Running $cfg"
  PYTHONUNBUFFERED=1 python scripts/run_retriever_family_ablation.py --config "$cfg" --run-reader
done
python scripts/summarize_reader_facing_retriever_results.py \
  --run-dirs outputs/reader_facing_retfam_* \
  --output-dir experiment_backups/reader_facing_retriever_family_20260530
