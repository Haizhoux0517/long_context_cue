# Reproducing the ONCU Diagnostic Experiments

This document describes how to audit and reproduce the final experiments reported in the paper:

> **A Controlled Diagnostic Framework for Evidence Utilization in Long-Context Language Models**

The goal of the repository is to make the reported claims auditable from fixed configuration files, deterministic inference settings, frozen result summaries, bootstrap confidence intervals, and table-level artifact mappings.

---

## 1. What is included in this release

The repository contains the code and frozen result artifacts needed to audit the reported experiments:

```text
longcue/                         Python package: data adapters, methods, models, metrics, ONCU, failure diagnosis
scripts/                         Dataset builders, protocol validators, summary/CI scripts
configs/                         Fixed YAML configs used for reported runs
experiment_backups/              Frozen result summaries, CI files, protocol manifests, and LaTeX/CSV tables
README_REPRODUCE.md              Reproduction instructions
ARTIFACT_MANIFEST.md             Paper-table-to-repository artifact map
requirements.txt                 Python dependencies
pyproject.toml                   Package metadata
```

Important note on processed inputs:

```text
data/processed/*.jsonl
```

are runtime evaluation inputs referenced by the configs. They may not be tracked in every repository snapshot because they are generated from the builder scripts and/or public datasets. If these files are absent, regenerate them using Section 4 before rerunning inference. The released `experiment_backups/` folders are the frozen artifacts used to audit the paper tables.

---

## 2. Environment

The experiments were run with local Ollama inference and deterministic decoding.

Recommended Python setup:

```bash
python --version
# Python 3.10+ supported; Python 3.11+ recommended

python -m pip install -r requirements.txt
python -m pip install -e .
```

Ollama models used in the reported experiments:

```bash
ollama pull qwen2.5:14b
ollama pull qwen3:14b
ollama pull gemma3:12b
ollama list
```

Core inference settings used by the fixed configs:

```text
temperature = 0.0
num_ctx = 32768
max_tokens = 1024
retrieval.top_k = 3 for the main matrix and robustness runs
retrieval.chunk_size = 220
retrieval.overlap = 40
protocol.version = diagnostic_v1_fixed
```

---

## 3. Validate release artifacts before running experiments

Run the release checker first:

```bash
python scripts/check_release_artifacts.py
```

This verifies that the repository contains the key scripts, configs, and frozen result artifacts referenced by the paper and by `ARTIFACT_MANIFEST.md`.

If you also want to require local processed JSONL input files, run:

```bash
python scripts/check_release_artifacts.py --strict-data
```

Use `--strict-data` only after generating or restoring `data/processed/*.jsonl`.

---

## 4. Build or restore processed evaluation inputs

The configs expect these processed files:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
data/processed/hotpotqa_cue_200.jsonl
data/processed/hotpotqa_cue_500.jsonl
data/processed/babilong_cue_200_external.jsonl
```

### 4.1 Controlled-safe16K-200

The controlled builder is:

```bash
python scripts/build_controlled_cue.py --help
```

The final paper run used the safe 16K controlled subset at:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
```

If this exact processed file is not present, regenerate the controlled data with the repository builder and then materialize/filter the safe16K 200-sample file according to the fixed configs and backup manifests. At minimum, inspect the builder output with:

```bash
python scripts/build_controlled_cue.py \
  --output data/processed/controlled_cue.jsonl \
  --num-per-cell 5 \
  --seed 42
```

Then ensure the final file expected by the configs exists:

```bash
ls -lh data/processed/controlled_oncu_200_safe16k.jsonl
```

### 4.2 HotpotQA-ONCU-200 and HotpotQA-500

The HotpotQA builder downloads and converts public HotpotQA data from Hugging Face:

```bash
python scripts/build_hotpotqa_cue.py \
  --output data/processed/hotpotqa_cue_200.jsonl \
  --split validation \
  --limit 200 \
  --context-lengths 4000 8000 16000 \
  --seed 42

python scripts/build_hotpotqa_cue.py \
  --output data/processed/hotpotqa_cue_500.jsonl \
  --split validation \
  --limit 500 \
  --context-lengths 4000 8000 16000 \
  --seed 42
```

Each command also writes skipped-sample statistics next to the output file.

### 4.3 BABILong-200 external validation

The BABILong external validation input is generated from four BABILong context configurations and five task types:

```bash
python scripts/build_babilong_cue.py \
  --output data/processed/babilong_cue_200_external.jsonl \
  --configs 0k 1k 2k 4k \
  --tasks qa1 qa2 qa3 qa6 qa7 \
  --limit-per-task 10
```

This produces:

```text
4 configs × 5 tasks × 10 examples = 200 examples
```

The current BABILong adapter does not provide ONCU-compatible oracle evidence. Therefore BABILong is used only for external answer-performance validation, not for ONCU computation.

---

## 5. Final main 200-sample ONCU matrix

The final core matrix evaluates three models:

```text
qwen2.5:14b
qwen3:14b
gemma3:12b
```

on two 200-sample ONCU-compatible settings:

```text
Controlled-ONCU-safe16K-200
HotpotQA-ONCU-200
```

under four fixed diagnostic conditions:

```text
no_evidence
direct                 # full-context input
retrieve_then_read
oracle                 # oracle-evidence reference
```

Total predictions:

```text
3 models × 2 datasets × 200 samples × 4 conditions = 4800 predictions
```

Final configs:

```text
configs/controlled_safe16k_qwen25_14b_200_core_final.yaml
configs/hotpotqa_qwen25_14b_200_core_final.yaml
configs/controlled_safe16k_qwen3_14b_200_core_final.yaml
configs/hotpotqa_qwen3_14b_200_core_final.yaml
configs/controlled_safe16k_gemma3_12b_200_core_final.yaml
configs/hotpotqa_gemma3_12b_200_core_final.yaml
```

Validate them:

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

Run one config:

```bash
python -m longcue.run_experiment \
  --config configs/controlled_safe16k_qwen25_14b_200_core_final.yaml
```

Run all six configs by repeating the same command for each config listed above.

After each run, recompute ONCU:

```bash
python scripts/recompute_oncu.py \
  --metrics outputs/<RUN_NAME>/results/per_sample_metrics.csv \
  --output outputs/<RUN_NAME>/results/oncu_metrics_multiscore.csv \
  --aggregate outputs/<RUN_NAME>/results/oncu_metrics_multiscore_summary.csv \
  --markdown outputs/<RUN_NAME>/tables/oncu_metrics_multiscore_summary.md
```

Frozen artifacts for the final 200-sample matrix are stored in:

```text
experiment_backups/sci200_final_3model_20260525/
```

Key audit files:

```text
experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv
experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv
experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv
```

---

## 6. Bootstrap confidence intervals for the main matrix

Run:

```bash
python scripts/bootstrap_sci200_final_ci.py
```

This generates sample-level confidence intervals for answer/evidence metrics and group-level confidence intervals for ONCU using 5,000 bootstrap replicates.

Expected output directory:

```text
experiment_backups/sci200_final_3model_20260525/ci/
```

---

## 7. Failure-type breakdown

Run:

```bash
python scripts/summarize_sci200_failure_breakdown.py
```

Key output used in the paper:

```text
experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv
```

Failure labels:

```text
Loc.   evidence localization failure
Sel.   evidence selection failure
Int.   evidence integration failure
Conv.  answer conversion failure
Succ.  categorical success
Parse  structured-output parsing failure
```

The categorical success label is stricter than relaxed answer F1 and should be interpreted only as a diagnostic category.

---

## 8. HotpotQA retrieval-budget sensitivity

The top-k ablation tests whether larger lexical retrieval budgets reduce the retrieved-evidence bottleneck on HotpotQA-ONCU-200.

Configs:

```text
configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml
```

Example:

```bash
python -m longcue.run_experiment \
  --config configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml

python scripts/recompute_oncu.py \
  --metrics outputs/hotpotqa_qwen25_14b_200_topk8_ablation/results/per_sample_metrics.csv \
  --output outputs/hotpotqa_qwen25_14b_200_topk8_ablation/results/oncu_metrics_multiscore.csv \
  --aggregate outputs/hotpotqa_qwen25_14b_200_topk8_ablation/results/oncu_metrics_multiscore_summary.csv \
  --markdown outputs/hotpotqa_qwen25_14b_200_topk8_ablation/tables/oncu_metrics_multiscore_summary.md
```

---

## 9. HotpotQA-500 robustness runs

The HotpotQA-500 runs test whether the HotpotQA full-context-over-retrieved pattern remains stable with a larger sample size and more valid ONCU groups.

Configs:

```text
configs/hotpotqa_qwen25_14b_500_core_robust.yaml
configs/hotpotqa_qwen3_14b_500_core_robust.yaml
configs/hotpotqa_gemma3_12b_500_core_robust.yaml
```

Run:

```bash
python -m longcue.run_experiment \
  --config configs/hotpotqa_qwen25_14b_500_core_robust.yaml

python -m longcue.run_experiment \
  --config configs/hotpotqa_qwen3_14b_500_core_robust.yaml

python -m longcue.run_experiment \
  --config configs/hotpotqa_gemma3_12b_500_core_robust.yaml
```

After each run, recompute ONCU using `scripts/recompute_oncu.py` as in Section 5.

Generate the HotpotQA-500 bootstrap CI files:

```bash
python scripts/bootstrap_hotpotqa500_robustness_ci.py
```

Frozen artifacts:

```text
experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_200_vs_500_robustness_summary.csv
experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_metric_bootstrap_ci.csv
experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_oncu_bootstrap_ci.csv
experiment_backups/hotpotqa_500_robustness_20260525/final_tables/hotpotqa_200_vs_500_with_ci.csv
```

---

## 10. BABILong-200 external answer-performance validation

BABILong-200 is not used for ONCU because the current adapter does not provide oracle-evidence annotations compatible with ONCU.

Configs:

```text
configs/babilong_qwen25_14b_200_external.yaml
configs/babilong_qwen3_14b_200_external.yaml
configs/babilong_gemma3_12b_200_external.yaml
```

Run:

```bash
python -m longcue.run_experiment \
  --config configs/babilong_qwen25_14b_200_external.yaml

python -m longcue.run_experiment \
  --config configs/babilong_qwen3_14b_200_external.yaml

python -m longcue.run_experiment \
  --config configs/babilong_gemma3_12b_200_external.yaml
```

No ONCU recomputation is required for BABILong. `Computed 0 ONCU rows` is expected.

Generate BABILong bootstrap CIs:

```bash
python scripts/bootstrap_babilong200_external_ci.py
```

Frozen artifacts:

```text
experiment_backups/babilong_200_external_20260526/babilong_200_external_summary.csv
experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv
experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv
```

---

## 11. Paper-table artifact mapping

Use:

```text
ARTIFACT_MANIFEST.md
```

to map each paper table/claim to the corresponding repository files.

A quick release audit can be run with:

```bash
python scripts/check_release_artifacts.py
```

---

## 12. Recommended end-to-end reproduction order

For a full rerun from processed inputs:

1. Install dependencies and pull the three Ollama models.
2. Generate or restore `data/processed/*.jsonl` inputs.
3. Run `python scripts/check_release_artifacts.py --strict-data`.
4. Validate all final configs using `scripts/validate_diagnostic_protocol.py`.
5. Run the six 200-sample core configs.
6. Recompute ONCU for each ONCU-compatible run.
7. Run `scripts/bootstrap_sci200_final_ci.py`.
8. Run `scripts/summarize_sci200_failure_breakdown.py`.
9. Run the HotpotQA top-k ablations.
10. Run the three HotpotQA-500 robustness configs and `scripts/bootstrap_hotpotqa500_robustness_ci.py`.
11. Run the three BABILong-200 external configs and `scripts/bootstrap_babilong200_external_ci.py`.
12. Compare outputs against `ARTIFACT_MANIFEST.md` and the frozen files in `experiment_backups/`.

---

## 13. Interpretation notes

- ONCU is a within-model, within-dataset diagnostic ratio, not a universal model-ranking score.
- ONCU is valid only when the oracle-evidence reference exceeds the no-evidence baseline for the metadata group.
- The oracle-evidence condition is an empirical reference, not a strict upper bound.
- BABILong-200 is external answer-performance validation, not an ONCU benchmark in the current implementation.
- Parse failures are retained and scored as incorrect.
- The failure taxonomy is diagnostic and should be interpreted alongside answer F1, evidence F1, and ONCU.
