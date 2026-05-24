# Diagnostic Refactor Summary

This refactor moves the project away from a prompt-engineering interpretation and toward a fixed diagnostic evaluation framework.

## Core changes

1. Added `longcue/protocol.py` with fixed method roles:
   - Core diagnostic conditions: `no_evidence`, `direct`, `retrieve_then_read`, `oracle`.
   - Auxiliary probes: `cot`, `evidence_first`, `evidence_first_verify`.
2. `run_experiment.py` now writes `protocol_manifest.json` for each run and adds method metadata to raw and per-sample outputs:
   - `method_display_name`
   - `method_family`
   - `method_role`
   - `core_diagnostic`
   - `prompt_protocol_version`
   - `prompt_hash`
3. Added `scripts/validate_diagnostic_protocol.py` to reject config-level prompt/template overrides and check deterministic diagnostic settings.
4. Added `scripts/recompute_oncu.py` and `longcue/evaluation/oncu.py` as ONCU terminology-safe wrappers around the legacy CUE implementation.
5. Updated Ollama configs to include explicit `num_ctx: 32768` and `timeout: 600` where applicable.
6. Added core-only config variants:
   - `configs/controlled_qwen7b_100_core.yaml`
   - `configs/hotpotqa_qwen7b_100_core.yaml`
7. Updated README language from prompt/method optimization toward fixed diagnostic conditions and auxiliary probes.
8. Added tests for diagnostic protocol classification and config validation.

## Interpretation rule

The auxiliary evidence-selection variants are retained for failure diagnosis only. They should not be described as the primary contribution or as optimized prompting methods.
