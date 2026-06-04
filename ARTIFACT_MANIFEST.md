# Artifact Manifest and Reproducibility Map

This manifest maps paper claims and tables to concrete repository artifacts.

A reviewer should be able to start from this file, locate the corresponding result artifact, and verify which script/config generated or summarized it.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| `Released` | Expected to exist in the repository snapshot. |
| `Generated` | Produced from released scripts or public datasets before rerunning inference. |
| `External` | Must be obtained from the original provider subject to its license or terms. |
| `Historical` | Development artifact not used for the current paper's final claims. |

---

## 2. Canonical paper-release directories

Only these release directories are canonical for the current paper:

| Paper component | Canonical repository directory | Status |
|---|---|---:|
| Final 3-model 200-sample core matrix | `experiment_backups/sci200_final_3model_20260525/` | Released |
| 2WikiMultiHopQA-ONCU-500 validation | `experiment_backups/twowiki_500_validation_20260527/` | Released |
| HotpotQA-500 robustness and valid-group audit | `experiment_backups/hotpotqa_500_robustness_20260525/` | Released |
| BABILong-200 external validation | `experiment_backups/babilong_200_external_20260526/` | Released |

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
| Runtime/model environment record | `scripts/export_runtime_record.py`; `RUNTIME_REPRODUCIBILITY_RECORD.md` | Released | Captures Ollama version, model tags/digests and quantization metadata exposed by Ollama, package versions, GPU/VRAM information, context length, deterministic decoding controls, and runtime logging policy. |

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

The 2Wiki file is byte-level reproducible with seed 42. The expected SHA256 checksum is:

```text
081189b8766d7924661b218579ad808fb1fc293adffa41f3863b70d55ae5917a
```

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
| BABILong-200 external validation | `configs/babilong_*_200_external.yaml` | Released |
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

## Retriever-family ablation scaffold

- `scripts/run_retriever_family_ablation.py`
  - Runs retrieval-only and optional reader-facing ablations across lexical,
    dense, hybrid, deterministic iterative, and oracle retriever families.
- `longcue/methods/retrievers.py`
  - Shared deterministic retriever implementations and retrieval diagnostics.
- `configs/ablations/retriever_family_hotpotqa_qwen25.yaml`
  - HotpotQA-ONCU-200 retriever-family ablation for Qwen2.5-14B.
- `configs/ablations/retriever_family_twowiki_qwen25.yaml`
  - 2WikiMultiHopQA-ONCU-500 retriever-family ablation for Qwen2.5-14B.


## Controlled scaling extension scaffold

The controlled scaling extension is released as a scaffold until the long-running
model outputs are materialized. It adds:

- `scripts/build_controlled_scaling_cue.py`
  - Generates 4K/8K/16K/32K controlled examples with ten position deciles.
- `scripts/summarize_controlled_scaling.py`
  - Summarizes completed scaling runs into ONCU, failure-heatmap, and regression CSVs.
- `configs/scaling/controlled_scaling_*_3200.yaml`
  - Fixed three-model configs for the 3200-sample scaling input.

Once completed runs are copied to `experiment_backups/controlled_scaling_20260527/`,
this manifest should be updated to mark the frozen scaling results as released.


## Statistical modeling support artifacts

| Artifact | Purpose |
|---|---|
| `scripts/statistical_modeling.py` | Generates paired effect-size summaries, multiple-comparison-adjusted p-values, and regression-style diagnostics. |
| `experiment_backups/statistical_modeling_20260530/statistical_effects_summary.csv` | Machine-readable paired contrasts for core conditions, controlled scaling, and retriever ablations. |
| `experiment_backups/statistical_modeling_20260530/statistical_effects_table.tex` | Compact LaTeX table for the main statistical support section. |
| `experiment_backups/statistical_modeling_20260530/statistical_regression_summary.csv` | Regression-style diagnostics over length-position cells and retrieval-family summary cells. |
| `experiment_backups/statistical_modeling_20260530/statistical_regression_table.tex` | Compact LaTeX table for regression-style robustness checks. |
