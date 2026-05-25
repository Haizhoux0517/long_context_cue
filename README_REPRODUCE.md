# Reproducing ONCU Experiments

This document describes how to reproduce the final ONCU diagnostic experiments for long-context evidence utilization.

The project evaluates whether long-context language models can use evidence embedded in long contexts, using **Oracle-Normalized Context Utilization (ONCU)** and a fixed four-condition diagnostic protocol.

---

## 1. Main Experimental Matrix

The final SCI-scale matrix evaluates three open-weight local models:

- `qwen2.5:14b`
- `qwen3:14b`
- `gemma3:12b`

on two 200-sample benchmark settings:

- `Controlled-ONCU-safe16K-200`
- `HotpotQA-ONCU-200`

under four fixed diagnostic conditions:

- `no_evidence`
- `direct` / full-context input
- `retrieve_then_read`
- `oracle` / oracle-evidence reference

Total predictions in the final main matrix:

```text
3 models × 2 datasets × 200 samples × 4 conditions = 4800 predictions
```

The main result configs are stored under:

```text
configs/*_200_core_final.yaml
```

---

## 2. Environment

The experiments were run with local Ollama inference and deterministic decoding.

Recommended environment:

```bash
python --version
# Python 3.11+ recommended

pip install -r requirements.txt
```

Ollama models used:

```bash
ollama pull qwen2.5:14b
ollama pull qwen3:14b
ollama pull gemma3:12b
```

Confirm models:

```bash
ollama list
```

The main inference settings are:

```text
temperature = 0.0
num_ctx = 32768
max_tokens = 1024
retrieval.top_k = 3 for the main matrix
chunk_size = 220
overlap = 40
```

---

## 3. Data Files

The final 200-sample datasets are expected at:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
data/processed/hotpotqa_cue_200.jsonl
```

The controlled dataset uses the safe 16K subset to reduce truncation-related confounds near backend context limits.

The HotpotQA-derived dataset aligns supporting facts to passage-level oracle evidence and is used for realistic multi-hop evaluation.

---

## 4. Main Final Configs

The final main experiment configs are:

```text
configs/controlled_safe16k_qwen25_14b_200_core_final.yaml
configs/hotpotqa_qwen25_14b_200_core_final.yaml

configs/controlled_safe16k_qwen3_14b_200_core_final.yaml
configs/hotpotqa_qwen3_14b_200_core_final.yaml

configs/controlled_safe16k_gemma3_12b_200_core_final.yaml
configs/hotpotqa_gemma3_12b_200_core_final.yaml
```

Validate the configs:

```bash
python scripts/validate_diagnostic_protocol.py \
  configs/controlled_safe16k_qwen25_14b_200_core_final.yaml \
  configs/hotpotqa_qwen25_14b_200_core_final.yaml \
  configs/controlled_safe16k_qwen3_14b_200_core_final.yaml \
  configs/hotpotqa_qwen3_14b_200_core_final.yaml \
  configs/controlled_safe16k_gemma3_12b_200_core_final.yaml \
  configs/hotpotqa_gemma3_12b_200_core_final.yaml \
  --require-core
```

Expected protocol version:

```text
diagnostic_v1_fixed
```

---

## 5. Running the Final Main Experiments

Example command:

```bash
python -m longcue.run_experiment \
  --config configs/controlled_safe16k_qwen25_14b_200_core_final.yaml
```

Run all six main configs:

```bash
python -m longcue.run_experiment \
  --config configs/controlled_safe16k_qwen25_14b_200_core_final.yaml

python -m longcue.run_experiment \
  --config configs/hotpotqa_qwen25_14b_200_core_final.yaml

python -m longcue.run_experiment \
  --config configs/controlled_safe16k_qwen3_14b_200_core_final.yaml

python -m longcue.run_experiment \
  --config configs/hotpotqa_qwen3_14b_200_core_final.yaml

python -m longcue.run_experiment \
  --config configs/controlled_safe16k_gemma3_12b_200_core_final.yaml

python -m longcue.run_experiment \
  --config configs/hotpotqa_gemma3_12b_200_core_final.yaml
```

Each run writes outputs under:

```text
outputs/<RUN_NAME>/
```

Each completed run should contain:

```text
outputs/<RUN_NAME>/results/per_sample_metrics.csv
outputs/<RUN_NAME>/results/oncu_metrics_multiscore.csv
outputs/<RUN_NAME>/results/oncu_metrics_multiscore_summary.csv
outputs/<RUN_NAME>/tables/oncu_metrics_multiscore_summary.md
```

---

## 6. Recomputing ONCU After Each Run

After each experiment run, recompute ONCU:

```bash
python scripts/recompute_oncu.py \
  --metrics outputs/<RUN_NAME>/results/per_sample_metrics.csv \
  --output outputs/<RUN_NAME>/results/oncu_metrics_multiscore.csv \
  --aggregate outputs/<RUN_NAME>/results/oncu_metrics_multiscore_summary.csv \
  --markdown outputs/<RUN_NAME>/tables/oncu_metrics_multiscore_summary.md
```

Example:

```bash
python scripts/recompute_oncu.py \
  --metrics outputs/hotpotqa_qwen25_14b_200_core_final/results/per_sample_metrics.csv \
  --output outputs/hotpotqa_qwen25_14b_200_core_final/results/oncu_metrics_multiscore.csv \
  --aggregate outputs/hotpotqa_qwen25_14b_200_core_final/results/oncu_metrics_multiscore_summary.csv \
  --markdown outputs/hotpotqa_qwen25_14b_200_core_final/tables/oncu_metrics_multiscore_summary.md
```

---

## 7. Final Summary Outputs

The final backup directory is:

```text
experiment_backups/sci200_final_3model_20260525/
```

Important final summary files:

```text
experiment_backups/sci200_final_3model_20260525/summary/
experiment_backups/sci200_final_3model_20260525/ci/
experiment_backups/sci200_final_3model_20260525/failure_analysis/
```

Important CSV files:

```text
experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv

experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_long.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_raw_values.csv
```

---

## 8. Bootstrap Confidence Intervals

Bootstrap confidence intervals are generated by:

```bash
python scripts/bootstrap_sci200_final_ci.py
```

This computes:

- sample-level bootstrap confidence intervals for answer and evidence metrics;
- group-level bootstrap confidence intervals for ONCU.

The final 200-sample analysis uses:

```text
5000 bootstrap replicates
two-sided 95% percentile intervals
```

The script writes:

```text
experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.tex
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.tex
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.tex
```

---

## 9. Failure-Type Breakdown

The final 200-sample failure breakdown is generated by:

```bash
python scripts/summarize_sci200_failure_breakdown.py
```

This produces:

```text
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.tex
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_compact_all_conditions.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_long.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_raw_values.csv
```

The contextual compact table is the one used in the paper:

```text
sci200_failure_breakdown_contextual_compact.csv
```

Failure categories:

```text
Loc.   = evidence localization failure
Sel.   = evidence selection failure
Int.   = evidence integration failure
Conv.  = answer conversion failure
Succ.  = categorical success
Parse  = structured-output parsing failure
```

The categorical success label is stricter than relaxed answer F1 and should be interpreted as a diagnostic label, not as a replacement for continuous answer metrics.

---

## 10. HotpotQA Retrieval Top-k Ablation

The top-k ablation evaluates whether increasing lexical retrieval breadth improves retrieved-evidence utilization on HotpotQA-ONCU-200.

Ablation configs:

```text
configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml

configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml
```

Example:

```bash
python -m longcue.run_experiment \
  --config configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml

python scripts/recompute_oncu.py \
  --metrics outputs/hotpotqa_qwen25_14b_200_topk5_ablation/results/per_sample_metrics.csv \
  --output outputs/hotpotqa_qwen25_14b_200_topk5_ablation/results/oncu_metrics_multiscore.csv \
  --aggregate outputs/hotpotqa_qwen25_14b_200_topk5_ablation/results/oncu_metrics_multiscore_summary.csv \
  --markdown outputs/hotpotqa_qwen25_14b_200_topk5_ablation/tables/oncu_metrics_multiscore_summary.md
```

The Qwen2.5-14B and Qwen3-14B ablation results show that increasing top-k partially improves retrieved evidence coverage and ONCU, but does not fully close the gap to full-context performance.

---

## 11. Parse Error Policy

Structured-output parsing failures are retained and scored as incorrect.

They are **not removed** from the denominator.

Observed final main-matrix parse-error counts:

```text
Qwen2.5-14B Controlled-safe16K-200: 0/800
Qwen2.5-14B HotpotQA-ONCU-200:     0/800
Qwen3-14B Controlled-safe16K-200:   0/800
Qwen3-14B HotpotQA-ONCU-200:        1/800
Gemma3-12B Controlled-safe16K-200:  6/800
Gemma3-12B HotpotQA-ONCU-200:       0/800
```

This policy avoids selectively discarding difficult model outputs and preserves comparability across models.

---

## 12. Recommended Reproduction Order

For a complete reproduction, run in this order:

1. Validate configs.
2. Run the six final main configs.
3. Recompute ONCU for each run.
4. Run `scripts/bootstrap_sci200_final_ci.py`.
5. Run `scripts/summarize_sci200_failure_breakdown.py`.
6. Run the HotpotQA top-k ablation configs.
7. Compare generated summary CSV files against the paper tables.

---

## 13. Notes on Interpretation

ONCU should be interpreted jointly with:

- answer F1;
- evidence F1;
- no-evidence baseline;
- oracle-evidence reference;
- failure-type breakdown;
- dataset structure.

A low full-context ONCU can indicate failure to use available evidence embedded in the long input.

A low retrieved-evidence ONCU can indicate retrieval coverage, ranking, or multi-hop evidence-selection failures.

The oracle-evidence condition is an empirical reference, not necessarily a strict per-example upper bound, because retrieved chunks may contain oracle passages plus adjacent local context.

---

## 14. Paper Files

The main paper draft is stored under:

```text
paper/
```

Recommended files:

```text
paper/main_ieee_oncu_final_sci_3model_200_with_topk_qwen25_qwen3.tex
paper/references.bib
```

