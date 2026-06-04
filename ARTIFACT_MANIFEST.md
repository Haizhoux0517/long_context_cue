# Artifact Manifest and Reproducibility Map

This manifest maps paper claims and tables to concrete repository artifacts.

A reviewer should be able to start from this file, locate the corresponding result artifact, and verify which script/config generated or summarized it.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| `Released` | Expected to exist in the repository snapshot. |
| `Generated` | Produced from released scripts or public datasets before rerunning inference. |
| `Summary-only` | Frozen summary/table artifacts are released, but full raw-response archives are not part of the current snapshot. |
| `External` | Must be obtained from the original provider subject to its license or terms. |
| `Historical` | Development artifact not used for the current paper's final claims. |

---

## 2. Canonical paper-release directories

The following directories and packaged artifacts are canonical for the current paper. They differ in evidence level: core ONCU runs include per-sample metrics and protocol manifests; several auxiliary audits are released as summary-level or generated-input artifacts.

| Paper component | Canonical repository directory | Status |
|---|---|---:|
| Final 3-model 200-sample core matrix | `experiment_backups/sci200_final_3model_20260525/` | Released |
| 2WikiMultiHopQA-ONCU-500 validation | `experiment_backups/twowiki_500_validation_20260527/` | Released |
| HotpotQA-500 robustness and valid-group audit | `experiment_backups/hotpotqa_500_robustness_20260525/` | Released |
| BABILong-200 external validation | `experiment_backups/babilong_200_external_20260526/` | Released |
| Model-family extension | `experiment_backups/model_family_extension_20260601/`; `model_family_extension_for_paper.tar.gz` | Released |
| Matched dense/hybrid ONCU sensitivity | `experiment_backups/retriever_family_oncu_sensitivity_20260602/` | Released |
| Retrieval-only retriever-family audit | `experiment_backups/retriever_family_ablation_20260527/` | Released |
| Reader-facing retriever-family summaries | `experiment_backups/reader_facing_retriever_family_20260530/`; `reader_facing_summary_for_paper.tar.gz` | Summary-only |
| Controlled length-position scaling | `experiment_backups/controlled_scaling_20260527/summary/` | Summary-only |
| RULER-lite external validation | `experiment_backups/ruler_lite_external_20260530_final/` | Summary-only |
| Failure taxonomy and human validation | `experiment_backups/failure_taxonomy_human_validation_20260530/` | Released |
| Alternative-metric comparison | `experiment_backups/metric_comparison_20260530/` | Released |
| Statistical modeling support | `experiment_backups/statistical_modeling_20260530/` | Released |

Older directories such as `experiment_backups/core_2x2_qwen25_qwen3_20260524/`, `experiment_backups/sci200_partial_qwen25_20260525/`, and `experiment_backups/sci200_qwen_family_20260525/`, if present, are historical intermediate backups and are not the source for final paper tables.

---

## 3. Core executable code

| Purpose | Repository path | Status | Notes |
|---|---|---:|---|
| Experiment runner | `longcue/run_experiment.py` | Released | Executes fixed YAML configs and writes per-sample outputs. |
| Protocol definition | `longcue/protocol.py` | Released | Defines core diagnostic conditions and auxiliary probes. |
| Protocol validation | `scripts/validate_diagnostic_protocol.py` | Released | Checks fixed protocol version and required config fields. |
| ONCU recomputation | `scripts/recompute_oncu.py` | Released | Recomputes raw/clipped ONCU tables from per-sample metrics. |
| 2Wiki table recomputation | `scripts/recompute_twowiki500_tables.py` | Released | Recomputes the 2Wiki paper-facing summaries from frozen per-sample metrics. |
| Answer metrics | `longcue/evaluation/answer_metrics.py` | Released | Strict and relaxed answer scoring. |
| Evidence metrics | `longcue/evaluation/evidence_metrics.py` | Released | Evidence precision/recall/F1 when oracle evidence exists. |
| ONCU implementation | `longcue/evaluation/oncu.py` and `longcue/evaluation/cue.py` | Released | ONCU/CUE-compatible computation. |
| Failure diagnosis | `longcue/evaluation/failure_diagnosis.py` | Released | Rule-based diagnostic failure categories. |
| Retrieval condition | `longcue/methods/retrieve_then_read.py` | Released | Deterministic lexical retrieve-then-read condition. |
| Ollama wrapper | `longcue/models/ollama.py` | Released | Local Ollama model calls. |
| Release checker | `scripts/check_release_artifacts.py` | Released | Verifies files declared by this manifest. |

---

## 4. Dataset builders and adapters

| Dataset/component | Repository path | Status | Notes |
|---|---|---:|---|
| Controlled builder | `scripts/build_controlled_cue.py` | Released | Builds controlled ONCU-compatible examples. |
| Controlled scaling builder | `scripts/build_controlled_scaling_cue.py` | Released | Builds decile-position controlled scaling examples. |
| Controlled generator | `longcue/data/controlled_generator.py` | Released | Synthetic context/evidence generation, including optional decile-position placement. |
| HotpotQA builder | `scripts/build_hotpotqa_cue.py` | Released | Builds HotpotQA-derived examples. |
| HotpotQA adapter | `longcue/data/hotpotqa_adapter.py` | Released | Maps supporting facts to passage identifiers. |
| 2Wiki builder | `scripts/build_2wiki_cue.py` | Released | Builds 2WikiMultiHopQA-derived examples. |
| 2Wiki adapter | `longcue/data/twowiki_adapter.py` | Released | Converts multi-hop evidence paths into ONCU-compatible oracle evidence IDs. |
| BABILong builder | `scripts/build_babilong_cue.py` | Released | Builds BABILong external-validation examples. |
| BABILong adapter | `longcue/data/babilong_adapter.py` | Released | Converts BABILong and marks it not ONCU-compatible. |
| RULER-lite builder | `scripts/build_ruler_lite.py` | Released | Builds deterministic RULER-lite external-validation examples. |
| RULER-lite runner and summarizer | `scripts/run_ruler_lite_external.py`; `scripts/summarize_ruler_lite_external.py` | Released | Runs and summarizes answer-only RULER-lite validation, not ONCU. |
| HotpotQA source dataset | Original HotpotQA provider | External | Required only for regeneration. |
| 2WikiMultiHopQA source dataset | Original 2WikiMultiHopQA provider | External | Required only for regeneration. |
| BABILong source dataset | Original BABILong provider | External | Required only for regeneration. |

---

## 5. Processed runtime inputs

| Input file | Used by | Status |
|---|---|---:|
| `data/processed/controlled_oncu_200_safe16k.jsonl` | Final controlled 200-sample matrix | Released |
| `data/processed/hotpotqa_cue_200.jsonl` | Final HotpotQA-ONCU-200 matrix and top-k ablations | Released |
| `data/processed/hotpotqa_cue_500.jsonl` | HotpotQA-500 robustness | Released |
| `data/processed/twowiki_cue_500.jsonl` | 2WikiMultiHopQA-ONCU-500 validation | Released or Generated |
| `data/processed/babilong_cue_200_external.jsonl` | BABILong-200 external validation | Released |
| `data/processed/controlled_scaling_3200.jsonl` | Controlled length-position scaling | Generated |
| `data/processed/ruler_lite_240.jsonl` | RULER-lite external validation | Generated |

The 2Wiki file is byte-level reproducible with seed 42. The expected SHA256 checksum is:

```text
081189b8766d7924661b218579ad808fb1fc293adffa41f3863b70d55ae5917a
```

Materialized release-input and packaged-asset integrity checks:

| Path | Bytes | SHA256 |
|---|---:|---|
| `data/processed/controlled_oncu_200_safe16k.jsonl` | 22,962,214 | `8da5eb3feabad98f4278496c4d463b20b322471cb383b0c4c988c609815daa23` |
| `data/processed/hotpotqa_cue_200.jsonl` | 14,440,502 | `3d1a5750b955f2f4eb552c41519916de621e08bc1090bc12f035075d233fff1b` |
| `data/processed/hotpotqa_cue_500.jsonl` | 35,800,527 | `4bfaf9cfb5b76ae3c5167cb217e7bf164e43cb9798d02249541709e8496b723e` |
| `data/processed/twowiki_cue_500.jsonl` | 31,954,698 | `081189b8766d7924661b218579ad808fb1fc293adffa41f3863b70d55ae5917a` |
| `data/processed/babilong_cue_200_external.jsonl` | 2,581,368 | `e4d3ae6f2f40600211177590ad07ca0cfc993c0e3bfd2f093368b48031b492b5` |
| `model_family_extension_for_paper.tar.gz` | 1,177,501 | `a9d9b985398bbb3293bed9141206e0c2641a32fdb6d624b6ca728592b644eb7e` |
| `reader_facing_summary_for_paper.tar.gz` | 4,480 | `f153fbedd90d29101e6b7ceda41b5bb11c6147ca8941e11229e142a26858b308` |

The generated-only auxiliary inputs `data/processed/controlled_scaling_3200.jsonl` and `data/processed/ruler_lite_240.jsonl` are intentionally excluded from this checksum table because they are regenerated by released builders before rerunning those auxiliary audits.

---

## 6. Fixed configurations

| Experiment family | Config paths | Status |
|---|---|---:|
| Controlled-safe16K-200 final matrix | `configs/controlled_safe16k_*_200_core_final.yaml` | Released |
| Controlled scaling extension | `configs/scaling/controlled_scaling_*_3200.yaml` | Released |
| HotpotQA-200 final matrix | `configs/hotpotqa_*_200_core_final.yaml` | Released |
| 2WikiMultiHopQA-500 validation | `configs/twowiki_*_500_core.yaml` | Released |
| HotpotQA-500 robustness | `configs/hotpotqa_*_500_core_robust.yaml` | Released |
| HotpotQA top-k ablation | `configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml`, `configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml`, `configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml`, `configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml` | Released |
| Model-family extension | `configs/model_family_extension/*.yaml` | Released |
| Retrieval-only and reader-facing retriever-family audits | `configs/ablations/retriever_family_*.yaml`, `configs/ablations/reader_facing_retfam_*.yaml` | Released |
| Matched dense/hybrid ONCU sensitivity | `configs/retriever_family_oncu_sensitivity/*.yaml` | Released |
| BABILong-200 external validation | `configs/babilong_*_200_external.yaml` | Released |
| RULER-lite external validation | `scripts/run_ruler_lite_external.py` CLI arguments; generated input from `scripts/build_ruler_lite.py` | Released |
| LongBench exploratory configs | `configs/longbench_*_300_external.yaml` | Released | Exploratory only; not used for current paper claims. |

---

## 7. Paper table to artifact map

| Paper result/table | Repository artifact(s) | Status |
|---|---|---:|
| Final 200-sample answer/evidence results | `experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv` | Released |
| Final 200-sample ONCU results | `experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv` | Released |
| Final 200-sample metric bootstrap CIs | `experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv` | Released |
| Final 200-sample ONCU bootstrap CIs | `experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv`, `experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv` | Released |
| Final failure-type breakdown | `experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv` | Released |
| 2Wiki main answer/evidence results | `experiment_backups/twowiki_500_validation_20260527/summary/twowiki_condition_summary.csv` | Released |
| 2Wiki ONCU results and CIs | `experiment_backups/twowiki_500_validation_20260527/summary/twowiki_oncu_relaxed_f1_summary.csv`, `experiment_backups/twowiki_500_validation_20260527/ci/twowiki_oncu_relaxed_f1_bootstrap_ci.csv` | Released |
| 2Wiki failure breakdown | `experiment_backups/twowiki_500_validation_20260527/failure_analysis/twowiki_failure_breakdown_long.csv` | Released |
| 2Wiki paper-facing LaTeX tables | `experiment_backups/twowiki_500_validation_20260527/final_tables/` | Released |
| HotpotQA-500 robustness table | `experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_200_vs_500_robustness_summary.csv`, `experiment_backups/hotpotqa_500_robustness_20260525/final_tables/hotpotqa_200_vs_500_with_ci.csv` | Released |
| HotpotQA-500 metric CIs | `experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_metric_bootstrap_ci.csv` | Released |
| HotpotQA-500 ONCU CIs | `experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_oncu_bootstrap_ci.csv` | Released |
| BABILong-200 external validation table | `experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv` | Released |
| BABILong-200 external validation CIs | `experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv` | Released |
| Model-family extension results | `experiment_backups/model_family_extension_20260601/*/results/per_sample_metrics.csv`, `experiment_backups/model_family_extension_20260601/*/results/cue_metrics.csv`, `experiment_backups/model_family_extension_20260601/*/results/aggregate_metrics.csv` | Released |
| Model-family packaged artifact | `model_family_extension_for_paper.tar.gz` | Released |
| Matched dense/hybrid ONCU sensitivity | `experiment_backups/retriever_family_oncu_sensitivity_20260602/*/results/per_sample_metrics.csv`, `experiment_backups/retriever_family_oncu_sensitivity_20260602/*/results/cue_metrics.csv`, `experiment_backups/retriever_family_oncu_sensitivity_20260602/*/results/aggregate_metrics.csv` | Released |
| Retrieval-only retriever-family audit | `experiment_backups/retriever_family_ablation_20260527/*/retrieval_only_per_sample.csv`, `experiment_backups/retriever_family_ablation_20260527/*/retrieval_only_summary.csv` | Released |
| Reader-facing retriever-family summaries | `experiment_backups/reader_facing_retriever_family_20260530/reader_facing_joined_summary.csv`, `experiment_backups/reader_facing_retriever_family_20260530/reader_facing_retfam_results_table.tex`, `reader_facing_summary_for_paper.tar.gz` | Summary-only |
| Controlled length-position scaling | `experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_oncu_by_length_position.csv`, `experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_regression.csv`, `experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_summary_manifest.json` | Summary-only |
| RULER-lite external validation | `experiment_backups/ruler_lite_external_20260530_final/ruler_lite_condition_summary.csv`, `experiment_backups/ruler_lite_external_20260530_final/ruler_lite_model_summary.csv` | Summary-only |
| Failure taxonomy and human validation | `experiment_backups/failure_taxonomy_human_validation_20260530/failure_taxonomy_final_summary.csv`, `experiment_backups/failure_taxonomy_human_validation_20260530/failure_taxonomy_human_validation_table.tex`, `experiment_backups/failure_taxonomy_human_validation_20260530/failure_taxonomy_final_manifest.json` | Released |
| Alternative-metric comparison | `experiment_backups/metric_comparison_20260530/metric_comparison_condition_summary.csv`, `experiment_backups/metric_comparison_20260530/metric_comparison_manifest.json` | Released |
| Five-model cross-encoder reranking audit | Manuscript appendix table only | Summary-only; not a primary release-check target |

---

## 8. Reproduction scripts

| Task | Script | Status |
|---|---|---:|
| Validate configs | `scripts/validate_diagnostic_protocol.py` | Released |
| Recompute ONCU | `scripts/recompute_oncu.py` | Released |
| Final 200-sample bootstrap CIs | `scripts/bootstrap_sci200_final_ci.py` | Released |
| 2Wiki derived tables | `scripts/recompute_twowiki500_tables.py` | Released |
| HotpotQA-500 bootstrap CIs | `scripts/bootstrap_hotpotqa500_robustness_ci.py` | Released |
| BABILong-200 bootstrap CIs | `scripts/bootstrap_babilong200_external_ci.py` | Released |
| Failure breakdown | `scripts/summarize_sci200_failure_breakdown.py` | Released |
| Controlled scaling summaries | `scripts/summarize_controlled_scaling.py` | Released |
| RULER-lite external validation | `scripts/build_ruler_lite.py`, `scripts/run_ruler_lite_external.py`, `scripts/summarize_ruler_lite_external.py` | Released |
| Retriever-family ONCU sensitivity | `scripts/prepare_retriever_family_oncu_sensitivity.py` | Released |
| Retrieval-only and reader-facing retriever-family audits | `scripts/run_retriever_family_ablation.py`, `scripts/summarize_reader_facing_retriever_results.py` | Released |
| Failure-taxonomy human validation | `scripts/export_failure_taxonomy_audit.py`, `scripts/summarize_failure_taxonomy_audit.py` | Released |
| Alternative-metric comparison | `scripts/metric_comparison_summary.py` | Released |
| Release artifact audit | `scripts/check_release_artifacts.py` | Released |

---

## 9. Release audit commands

Default audit:

```bash
python scripts/check_release_artifacts.py
```

Strict data and cleanliness audit:

```bash
python scripts/check_release_artifacts.py --strict-data --strict-clean
```

Expected result for a complete paper-release checkout:

```text
missing required: 0
result: PASS
```

## Retriever-family ablation and sensitivity artifacts

- `scripts/run_retriever_family_ablation.py`
  - Runs retrieval-only and optional reader-facing ablations across lexical,
    dense, hybrid, deterministic iterative, and oracle retriever families.
- `scripts/prepare_retriever_family_oncu_sensitivity.py`
  - Generates matched dense@16 and hybrid@16 ONCU sensitivity configs in which no-evidence, full-context, and oracle-evidence reference conditions remain fixed while the retrieved-evidence family changes.
- `longcue/methods/retrievers.py`
  - Shared deterministic retriever implementations and retrieval diagnostics.
- `configs/ablations/retriever_family_hotpotqa_qwen25.yaml`
  - HotpotQA-ONCU-200 retriever-family ablation for Qwen2.5-14B.
- `configs/ablations/retriever_family_twowiki_qwen25.yaml`
  - 2WikiMultiHopQA-ONCU-500 retriever-family ablation for Qwen2.5-14B.
- `configs/ablations/reader_facing_retfam_*.yaml`
  - Reader-facing retriever-family sweeps across lexical, dense, and hybrid retrieved contexts.
- `configs/retriever_family_oncu_sensitivity/*.yaml`
  - Matched dense/hybrid ONCU sensitivity configs used by the paper.
- `experiment_backups/retriever_family_ablation_20260527/`
  - Frozen retrieval-only per-sample diagnostics and summaries.
- `experiment_backups/reader_facing_retriever_family_20260530/`
  - Frozen reader-facing summary tables.
- `experiment_backups/retriever_family_oncu_sensitivity_20260602/`
  - Frozen matched dense/hybrid ONCU sensitivity runs.

The five-model cross-encoder reranking audit is intentionally not listed as a primary release-check target because the current snapshot contains the manuscript summary table but not a full reranking runner/config/raw-output archive.

## Controlled scaling and RULER-lite auxiliary artifacts

The controlled scaling extension is released with deterministic builders, fixed configs, and frozen summary artifacts:

- `scripts/build_controlled_scaling_cue.py`
  - Generates 4K/8K/16K/32K controlled examples with ten position deciles.
- `scripts/summarize_controlled_scaling.py`
  - Summarizes completed scaling runs into ONCU, failure-heatmap, and regression CSVs.
- `configs/scaling/controlled_scaling_*_3200.yaml`
  - Fixed three-model configs for the 3200-sample scaling input.
- `experiment_backups/controlled_scaling_20260527/summary/`
  - Frozen summary-level controlled-scaling artifacts used in the manuscript.

The generated input `data/processed/controlled_scaling_3200.jsonl` is not required to exist in the release root; it is produced by the builder before rerunning inference.

RULER-lite is likewise an answer-only external validation, not an ONCU benchmark:

- `scripts/build_ruler_lite.py`
  - Generates `data/processed/ruler_lite_240.jsonl`.
- `scripts/run_ruler_lite_external.py`
  - Runs full-context and retrieved-context answer validation.
- `scripts/summarize_ruler_lite_external.py`
  - Summarizes completed RULER-lite outputs.
- `experiment_backups/ruler_lite_external_20260530_final/`
  - Frozen summary-level RULER-lite artifacts used in the manuscript.


## Statistical modeling support artifacts

| Artifact | Purpose |
|---|---|
| `scripts/statistical_modeling.py` | Generates paired effect-size summaries, multiple-comparison-adjusted p-values, and regression-style diagnostics. |
| `experiment_backups/statistical_modeling_20260530/statistical_effects_summary.csv` | Machine-readable paired contrasts for core conditions, controlled scaling, and retriever ablations. |
| `experiment_backups/statistical_modeling_20260530/statistical_effects_table.tex` | Compact LaTeX table for the main statistical support section. |
| `experiment_backups/statistical_modeling_20260530/statistical_regression_summary.csv` | Regression-style diagnostics over length-position cells and retrieval-family summary cells. |
| `experiment_backups/statistical_modeling_20260530/statistical_regression_table.tex` | Compact LaTeX table for regression-style robustness checks. |
