# Artifact Manifest and Reproducibility Map

This manifest maps the paper's main tables, robustness checks, and reproducibility claims to concrete repository artifacts.

The repository snapshot contains executable code, fixed configs, and frozen result summaries. Some processed runtime input files under `data/processed/` may need to be regenerated from public datasets using the builder scripts before rerunning inference.

---

## A. Repository status legend

| Status | Meaning |
|---|---|
| `Released` | File or directory is expected to exist in the repository snapshot. |
| `Generated` | File is referenced by configs but may need to be regenerated locally. |
| `External` | Original public dataset or external model must be obtained from its provider. |

---

## B. Core code artifacts

| Purpose | Repository path | Status | Notes |
|---|---|---:|---|
| Experiment runner | `longcue/run_experiment.py` | Released | Executes fixed diagnostic configs and writes per-sample outputs. |
| Protocol definition | `longcue/protocol.py` | Released | Defines fixed protocol metadata and condition structure. |
| Protocol validator | `scripts/validate_diagnostic_protocol.py` | Released | Checks config consistency and required core fields. |
| ONCU recomputation | `scripts/recompute_oncu.py` | Released | Recomputes raw and clipped ONCU summaries from `per_sample_metrics.csv`. |
| Answer metrics | `longcue/evaluation/answer_metrics.py` | Released | Computes strict and relaxed answer metrics. |
| Evidence metrics | `longcue/evaluation/evidence_metrics.py` | Released | Computes evidence precision/recall/F1 where oracle evidence exists. |
| ONCU implementation | `longcue/evaluation/oncu.py` and `longcue/evaluation/cue.py` | Released | Implements ONCU/CUE-compatible scoring. |
| Failure diagnosis | `longcue/evaluation/failure_diagnosis.py` | Released | Implements diagnostic failure labels. |
| Retrieval method | `longcue/methods/retrieve_then_read.py` | Released | Implements deterministic lexical retrieve-then-read condition. |
| Model wrapper | `longcue/models/ollama.py` | Released | Calls local Ollama models. |
| Release checker | `scripts/check_release_artifacts.py` | Released | Verifies repository files referenced by this manifest. |

---

## C. Dataset builders and adapters

| Dataset / component | Repository path | Status | Notes |
|---|---|---:|---|
| Controlled builder | `scripts/build_controlled_cue.py` | Released | Builds controlled CUE/ONCU-style samples. |
| Controlled generator | `longcue/data/controlled_generator.py` | Released | Generates controlled samples with metadata dimensions. |
| HotpotQA builder | `scripts/build_hotpotqa_cue.py` | Released | Converts public HotpotQA data to passage-identified samples. |
| HotpotQA adapter | `longcue/data/hotpotqa_adapter.py` | Released | Aligns supporting facts to evidence passages. |
| BABILong builder | `scripts/build_babilong_cue.py` | Released | Builds BABILong external validation samples. |
| BABILong adapter | `longcue/data/babilong_adapter.py` | Released | Marks BABILong as not ONCU-compatible because oracle evidence is unavailable. |
| LongBench adapter | `longcue/data/longbench_adapter.py` and `scripts/build_longbench_cue.py` | Released | Included as adapter code; not part of current reported experiments. |

---

## D. Processed runtime inputs

| Processed input | Consumed by configs | Status | How to obtain |
|---|---|---:|---|
| `data/processed/controlled_oncu_200_safe16k.jsonl` | Controlled-safe16K-200 final configs | Generated | Restore from experiment environment or generate/materialize from controlled builder. |
| `data/processed/hotpotqa_cue_200.jsonl` | HotpotQA-ONCU-200 final configs and top-k ablations | Generated | `python scripts/build_hotpotqa_cue.py --output data/processed/hotpotqa_cue_200.jsonl --split validation --limit 200 --context-lengths 4000 8000 16000 --seed 42` |
| `data/processed/hotpotqa_cue_500.jsonl` | HotpotQA-500 robustness configs | Generated | `python scripts/build_hotpotqa_cue.py --output data/processed/hotpotqa_cue_500.jsonl --split validation --limit 500 --context-lengths 4000 8000 16000 --seed 42` |
| `data/processed/babilong_cue_200_external.jsonl` | BABILong-200 external configs | Generated | `python scripts/build_babilong_cue.py --output data/processed/babilong_cue_200_external.jsonl --configs 0k 1k 2k 4k --tasks qa1 qa2 qa3 qa6 qa7 --limit-per-task 10` |
| HotpotQA original data | HotpotQA builder | External | Loaded from public Hugging Face dataset by the builder script. |
| BABILong original data | BABILong builder | External | Loaded from public Hugging Face dataset by the builder script. |

---

## E. Fixed configs

| Experiment family | Config paths | Status |
|---|---|---:|
| Final 200-sample controlled configs | `configs/controlled_safe16k_qwen25_14b_200_core_final.yaml`; `configs/controlled_safe16k_qwen3_14b_200_core_final.yaml`; `configs/controlled_safe16k_gemma3_12b_200_core_final.yaml` | Released |
| Final 200-sample HotpotQA configs | `configs/hotpotqa_qwen25_14b_200_core_final.yaml`; `configs/hotpotqa_qwen3_14b_200_core_final.yaml`; `configs/hotpotqa_gemma3_12b_200_core_final.yaml` | Released |
| HotpotQA top-k ablations | `configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml`; `configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml`; `configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml`; `configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml` | Released |
| HotpotQA-500 robustness | `configs/hotpotqa_qwen25_14b_500_core_robust.yaml`; `configs/hotpotqa_qwen3_14b_500_core_robust.yaml`; `configs/hotpotqa_gemma3_12b_500_core_robust.yaml` | Released |
| BABILong-200 external validation | `configs/babilong_qwen25_14b_200_external.yaml`; `configs/babilong_qwen3_14b_200_external.yaml`; `configs/babilong_gemma3_12b_200_external.yaml` | Released |

---

## F. Paper table to repository artifact map

| Paper result / table | Primary artifact(s) | Supporting artifact(s) | Status |
|---|---|---|---:|
| Final 200-sample answer/evidence results | `experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv` | `experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.tex` | Released |
| Final 200-sample ONCU results | `experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv` | `experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv` | Released |
| Final 200-sample bootstrap CIs | `experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv`; `experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv` | `scripts/bootstrap_sci200_final_ci.py` | Released |
| Failure-type breakdown | `experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv` | `experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_long.csv`; `scripts/summarize_sci200_failure_breakdown.py` | Released |
| HotpotQA top-k retrieval-budget sensitivity | Top-k configs under `configs/`; recomputed ONCU outputs under `outputs/` after rerun | Frozen paper values are summarized in the manuscript; rerun configs are released. | Released/Rerunnable |
| HotpotQA-500 robustness and valid-group audit | `experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_200_vs_500_robustness_summary.csv`; `experiment_backups/hotpotqa_500_robustness_20260525/final_tables/hotpotqa_200_vs_500_with_ci.csv` | `experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_metric_bootstrap_ci.csv`; `experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_oncu_bootstrap_ci.csv` | Released |
| BABILong-200 external validation | `experiment_backups/babilong_200_external_20260526/babilong_200_external_summary.csv`; `experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv` | `experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv`; `scripts/bootstrap_babilong200_external_ci.py` | Released |
| Protocol manifests / resolved configs for final matrix | `experiment_backups/sci200_final_3model_20260525/*/protocol_manifest.json`; `experiment_backups/sci200_final_3model_20260525/*/resolved_config.json` | Backup configs under `experiment_backups/sci200_final_3model_20260525/configs/` | Released |

---

## G. Expected release audit command

```bash
python scripts/check_release_artifacts.py
```

Optional strict check after processed data have been generated/restored:

```bash
python scripts/check_release_artifacts.py --strict-data
```

---

## H. Notes for reviewers

- The main ONCU claims are supported by the two ONCU-compatible components: Controlled-safe16K-200 and HotpotQA-ONCU-200.
- HotpotQA-500 is a robustness and valid-group audit, not a replacement for the balanced main matrix.
- BABILong-200 is external answer-performance validation only; it is not an ONCU benchmark in the current implementation.
- `data/processed/*.jsonl` files are runtime inputs referenced by configs. If absent, regenerate them before rerunning inference.
- Frozen paper-level results are auditable from `experiment_backups/` without rerunning long model inference.
