# Retriever-Family ONCU Sensitivity Artifacts

This directory contains frozen artifacts for the matched retriever-family ONCU sensitivity experiment reported in the paper.

Scope:
- HotpotQA-ONCU-200 and 2WikiMultiHopQA-ONCU-500
- Qwen2.5-14B, Qwen3-14B, and Gemma3-12B
- Dense@16 and Hybrid@16 retrieved-evidence variants
- Four matched conditions: no evidence, full context, retrieved evidence, and oracle-evidence reference

Included:
- per_sample_metrics.csv
- aggregate_metrics.csv
- cue_metrics.csv
- robustness_drop.csv
- resolved_config.json
- protocol_manifest.json
- run logs
- YAML configs
- code files required to regenerate the configs and retriever behavior

Raw model response JSONL files are not tracked here to avoid large Git objects. The experiment can be regenerated from the configs and scripts in this repository.
