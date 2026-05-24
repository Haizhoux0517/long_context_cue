#!/usr/bin/env bash
set -euo pipefail

python scripts/generate_demo_data.py
python -m longcue.run_experiment --config configs/demo.yaml
