# Model-Family Extension Results

This directory contains the frozen artifacts for the Llama3.1-8B and Mistral-Small3.1-24B ONCU-compatible model-family extension.

Included artifacts:
- resolved_config.json and protocol_manifest.json for each run
- aggregate_metrics.csv
- cue_metrics.csv
- per_sample_metrics.csv
- robustness_drop.csv
- markdown tables
- experiment logs

Raw model response JSONL files are not tracked here to avoid large Git objects. The corresponding configs are stored under configs/model_family_extension/.
