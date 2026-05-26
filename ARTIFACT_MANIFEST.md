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
| HotpotQA-500 robustness and valid-group audit | `experiment_backups/hotpotqa_500_robustness_20260525/` | Released |
| BABILong-200 external validation | `experiment_backups/babilong_200_external_20260526/` | Released |

Older directories such as `experiment_backups/core_2x2_qwen25_qwen3_20260524/`, `experiment_backups/sci200_partial_qwen25_20260525/`, and `experiment_backups/sci200_qwen_family_20260525/`, if present, are historical intermediate backups and are not the source for final paper tables.

---

## 3. Core executable code

| Purpose | Repository path | Status | Notes |
|---|---|---:|---|
| Experiment runner | `longcue/run_experiment.py` | Released | Executes fixed YAML configs and writes per-sample outputs. |
| Protocol definition | `longcue/protocol.py` | Released | Defines core diagnostic conditions and auxiliary probes. |
| Protocol validation | `scripts/validate_diagnostic_protocol.py` | Released | Checks fixed protocol version and required config fields. |
| ONCU recomputation | `scripts/recompute_oncu.py` | Released | Recomputes raw/clipped ONCU tables from per-sample metrics. |
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
| Controlled generator | `longcue/data/controlled_generator.py` | Released | Synthetic context/evidence generation. |
| HotpotQA builder | `scripts/build_hotpotqa_cue.py` | Released | Builds HotpotQA-derived examples. |
| HotpotQA adapter | `longcue/data/hotpotqa_adapter.py` | Released | Maps supporting facts to passage identifiers. |
| BABILong builder | `scripts/build_babilong_cue.py` | Released | Builds BABILong external-validation examples. |
| BABILong adapter | `longcue/data/babilong_adapter.py` | Released | Converts BABILong and marks it not ONCU-compatible. |
| HotpotQA source dataset | Original HotpotQA provider | External | Required only for regeneration. |
| BABILong source dataset | Original BABILong provider | External | Required only for regeneration. |

---

## 5. Processed runtime inputs

| Input file | Used by | Status |
|---|---|---:|
| `data/processed/controlled_oncu_200_safe16k.jsonl` | Controlled-safe16K-200 final matrix | Released or Generated |
| `data/processed/hotpotqa_cue_200.jsonl` | HotpotQA-200 final matrix and top-k ablations | Released or Generated |
| `data/processed/hotpotqa_cue_500.jsonl` | HotpotQA-500 robustness | Released or Generated |
| `data/processed/babilong_cue_200_external.jsonl` | BABILong-200 external validation | Released or Generated |

A full reviewer-facing release should include these four files so that:

```bash
python scripts/check_release_artifacts.py --strict-data
```

passes. If a source-control snapshot excludes processed data, regenerate them with the builder scripts before rerunning inference.

---

## 6. Fixed configurations

| Experiment family | Config paths | Status |
|---|---|---:|
| Controlled-safe16K-200 final matrix | `configs/controlled_safe16k_*_200_core_final.yaml` | Released |
| HotpotQA-200 final matrix | `configs/hotpotqa_*_200_core_final.yaml` | Released |
| HotpotQA-500 robustness | `configs/hotpotqa_*_500_core_robust.yaml` | Released |
| HotpotQA top-k ablation | `configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml`, `configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml`, `configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml`, `configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml` | Released |
| BABILong-200 external validation | `configs/babilong_*_200_external.yaml` | Released |

---

## 7. Paper table to artifact map

| Paper result/table | Repository artifact(s) | Status |
|---|---|---:|
| Final 200-sample answer/evidence results | `experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv` | Released |
| Final 200-sample ONCU results | `experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv` | Released |
| Final 200-sample metric bootstrap CIs | `experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv` | Released |
| Final 200-sample ONCU bootstrap CIs | `experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv`, `experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv` | Released |
| Final failure-type breakdown | `experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv` | Released |
| Per-run protocol audit | `experiment_backups/sci200_final_3model_20260525/*/protocol_manifest.json`, `experiment_backups/sci200_final_3model_20260525/*/resolved_config.json` | Released |
| HotpotQA-500 robustness table | `experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_200_vs_500_robustness_summary.csv`, `experiment_backups/hotpotqa_500_robustness_20260525/final_tables/hotpotqa_200_vs_500_with_ci.csv` | Released |
| HotpotQA-500 metric CIs | `experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_metric_bootstrap_ci.csv` | Released |
| HotpotQA-500 ONCU CIs | `experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_oncu_bootstrap_ci.csv` | Released |
| BABILong-200 summary | `experiment_backups/babilong_200_external_20260526/babilong_200_external_summary.csv` | Released |
| BABILong-200 bootstrap CIs | `experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv` | Released |
| BABILong-200 compact paper table | `experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv` | Released |

---

## 8. Reproducibility scripts

| Task | Script | Status |
|---|---|---:|
| Validate configs | `scripts/validate_diagnostic_protocol.py` | Released |
| Recompute ONCU | `scripts/recompute_oncu.py` | Released |
| Final 200-sample bootstrap CIs | `scripts/bootstrap_sci200_final_ci.py` | Released |
| HotpotQA-500 bootstrap CIs | `scripts/bootstrap_hotpotqa500_robustness_ci.py` | Released |
| BABILong-200 bootstrap CIs | `scripts/bootstrap_babilong200_external_ci.py` | Released |
| Failure breakdown | `scripts/summarize_sci200_failure_breakdown.py` | Released |
| Release artifact audit | `scripts/check_release_artifacts.py` | Released |

---

## 9. Release audit commands

Default audit:

```bash
python scripts/check_release_artifacts.py
```

Strict data audit:

```bash
python scripts/check_release_artifacts.py --strict-data
```

Strict clean audit, which also fails on stale root-level duplicate documents:

```bash
python scripts/check_release_artifacts.py --strict-clean
```

Recommended final audit:

```bash
python -m pytest -q
python scripts/check_release_artifacts.py --strict-data --strict-clean
```
