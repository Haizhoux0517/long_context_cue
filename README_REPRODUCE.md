# Reproducing the ONCU Diagnostic Experiments

This document describes how to audit and reproduce the final experiments reported in:

> **A Controlled Diagnostic Framework for Evidence Utilization in Long-Context Language Models**

The release is designed around four layers:

1. fixed YAML configurations;
2. processed JSONL evaluation inputs;
3. deterministic local inference settings;
4. frozen result artifacts and table-level summaries.

For a paper-table-to-file mapping, see [`ARTIFACT_MANIFEST.md`](ARTIFACT_MANIFEST.md).

---

## 1. Release sanity check

Run the release checker first:

```bash
python scripts/check_release_artifacts.py
```

For a complete release that includes processed JSONL inputs, run:

```bash
python scripts/check_release_artifacts.py --strict-data
```

Expected result:

```text
missing required: 0
result: PASS
```

If the default check passes but `--strict-data` fails, the code/config/result release is present but the processed runtime inputs under `data/processed/` are missing from the local checkout. Restore them from the release or regenerate them using the dataset builders below.

Run unit tests:

```bash
python -m pytest -q
```

---

## 2. Environment

Recommended setup:

```bash
python --version
# Python 3.10+ supported; Python 3.11+ recommended

python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Local Ollama models used in the reported experiments:

```bash
ollama pull qwen2.5:14b
ollama pull qwen3:14b
ollama pull gemma3:12b
ollama list
```

Core inference settings recorded in the fixed configs:

```text
temperature = 0.0
num_ctx = 32768
max_tokens = 1024
retrieval.top_k = 3 for the main matrix and HotpotQA-500 robustness runs
retrieval.chunk_size = 220
retrieval.overlap = 40
protocol.version = diagnostic_v1_fixed
```

---

## 3. Processed input files

The paper release uses four processed JSONL inputs:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
data/processed/hotpotqa_cue_200.jsonl
data/processed/hotpotqa_cue_500.jsonl
data/processed/babilong_cue_200_external.jsonl
```

These files are materialized evaluation inputs referenced by the fixed configs. They contain sample IDs, questions, passage-annotated contexts, gold answers, and metadata. ONCU-compatible datasets also contain oracle-evidence identifiers. BABILong-200 is used only for answer-performance validation because the current adapter does not expose oracle evidence compatible with ONCU.

If the files are absent, regenerate them before rerunning inference. Example builder commands are:

```bash
mkdir -p data/processed

python scripts/build_controlled_cue.py   --output data/processed/controlled_oncu_200_safe16k.jsonl   --limit 200   --context-lengths 4000 8000 16000   --seed 42

python scripts/build_hotpotqa_cue.py   --output data/processed/hotpotqa_cue_200.jsonl   --limit 200   --seed 42

python scripts/build_hotpotqa_cue.py   --output data/processed/hotpotqa_cue_500.jsonl   --limit 500   --seed 42

python scripts/build_babilong_cue.py   --output data/processed/babilong_cue_200_external.jsonl   --configs 0k 1k 2k 4k   --tasks qa1 qa2 qa3 qa6 qa7   --limit-per-task 10
```

If builder CLI options change in a future branch, inspect the current help messages:

```bash
python scripts/build_controlled_cue.py --help
python scripts/build_hotpotqa_cue.py --help
python scripts/build_babilong_cue.py --help
```

Original public datasets, including HotpotQA and BABILong, should be obtained from their official sources subject to their licenses and terms of use.

---

## 4. Final 200-sample core matrix

The main matrix evaluates three models on two datasets under four fixed diagnostic conditions:

```text
3 models × 2 datasets × 200 samples × 4 conditions = 4800 predictions
```

Final configs:

```text
configs/controlled_safe16k_qwen25_14b_200_core_final.yaml
configs/controlled_safe16k_qwen3_14b_200_core_final.yaml
configs/controlled_safe16k_gemma3_12b_200_core_final.yaml
configs/hotpotqa_qwen25_14b_200_core_final.yaml
configs/hotpotqa_qwen3_14b_200_core_final.yaml
configs/hotpotqa_gemma3_12b_200_core_final.yaml
```

Validate configs:

```bash
python scripts/validate_diagnostic_protocol.py   configs/controlled_safe16k_qwen25_14b_200_core_final.yaml   configs/controlled_safe16k_qwen3_14b_200_core_final.yaml   configs/controlled_safe16k_gemma3_12b_200_core_final.yaml   configs/hotpotqa_qwen25_14b_200_core_final.yaml   configs/hotpotqa_qwen3_14b_200_core_final.yaml   configs/hotpotqa_gemma3_12b_200_core_final.yaml   --require-core
```

Run a config:

```bash
python -m longcue.run_experiment   --config configs/controlled_safe16k_qwen25_14b_200_core_final.yaml
```

Recompute ONCU for a completed run:

```bash
python scripts/recompute_oncu.py   --metrics outputs/controlled_safe16k_qwen25_14b_200_core_final/results/per_sample_metrics.csv   --output outputs/controlled_safe16k_qwen25_14b_200_core_final/results/oncu_metrics_multiscore.csv   --aggregate outputs/controlled_safe16k_qwen25_14b_200_core_final/results/oncu_metrics_multiscore_summary.csv   --markdown outputs/controlled_safe16k_qwen25_14b_200_core_final/tables/oncu_metrics_multiscore_summary.md
```

Frozen artifacts used by the paper:

```text
experiment_backups/sci200_final_3model_20260525/
```

Important summary files:

```text
experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv
experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv
```

---

## 5. HotpotQA retrieval-budget ablation

Ablation configs:

```text
configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml
```

These vary lexical retrieval `top_k` while keeping the dataset, decoding policy, output contract, chunk size, overlap, and evaluation pipeline fixed.

---

## 6. HotpotQA-500 robustness

HotpotQA-500 configs:

```text
configs/hotpotqa_qwen25_14b_500_core_robust.yaml
configs/hotpotqa_qwen3_14b_500_core_robust.yaml
configs/hotpotqa_gemma3_12b_500_core_robust.yaml
```

Frozen artifacts:

```text
experiment_backups/hotpotqa_500_robustness_20260525/
```

Main files:

```text
experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_200_vs_500_robustness_summary.csv
experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_metric_bootstrap_ci.csv
experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_oncu_bootstrap_ci.csv
experiment_backups/hotpotqa_500_robustness_20260525/final_tables/hotpotqa_200_vs_500_with_ci.csv
```

---

## 7. BABILong-200 external validation

BABILong-200 is not treated as an ONCU benchmark in this release. It is used as external answer-performance validation because the current BABILong adapter does not provide oracle-evidence annotations compatible with ONCU.

Configs:

```text
configs/babilong_qwen25_14b_200_external.yaml
configs/babilong_qwen3_14b_200_external.yaml
configs/babilong_gemma3_12b_200_external.yaml
```

Frozen artifacts:

```text
experiment_backups/babilong_200_external_20260526/
```

Main files:

```text
experiment_backups/babilong_200_external_20260526/babilong_200_external_summary.csv
experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv
experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv
```

---

## 8. Regenerating confidence intervals and summaries

Final 200-sample bootstrap CIs:

```bash
python scripts/bootstrap_sci200_final_ci.py
```

HotpotQA-500 bootstrap CIs:

```bash
python scripts/bootstrap_hotpotqa500_robustness_ci.py
```

BABILong-200 bootstrap CIs:

```bash
python scripts/bootstrap_babilong200_external_ci.py
```

Failure breakdown:

```bash
python scripts/summarize_sci200_failure_breakdown.py
```

---

## 9. Canonical release directories

Only these directories are used as canonical evidence for the current paper:

```text
experiment_backups/sci200_final_3model_20260525/
experiment_backups/hotpotqa_500_robustness_20260525/
experiment_backups/babilong_200_external_20260526/
```

If older backup folders are present, treat them as historical development artifacts, not as the source for the final paper tables.

---

## 10. Final release checklist

Before submission or archival release:

```bash
python -m pytest -q
python scripts/check_release_artifacts.py
python scripts/check_release_artifacts.py --strict-data
git status
```

Expected release-audit result:

```text
missing required: 0
result: PASS
```
