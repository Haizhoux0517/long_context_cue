# Long-Context ONCU Diagnostic Framework

This repository contains the code, fixed configurations, processed inputs, and frozen result artifacts for the paper:

> **Oracle-Normalized Evidence Utilization: A Diagnostic Framework for Long-Context and Retrieval-Augmented Language Models**

The project evaluates whether long-context and retrieval-augmented language models recover the evidence-derived advantage made available by a context. The main contribution is a matched four-condition diagnostic protocol: no evidence, full context, retrieved evidence, and an oracle-evidence reference. **Oracle-Normalized Context Utilization (ONCU)** is the protocol-bound estimator that normalizes a contextual condition between the no-evidence baseline and the oracle-evidence reference.

For full reproduction commands, use [`README_REPRODUCE.md`](README_REPRODUCE.md). For the mapping from paper tables to repository files, use [`ARTIFACT_MANIFEST.md`](ARTIFACT_MANIFEST.md).

---

## Repository layout

```text
longcue/                         Core Python package
scripts/                         Dataset builders, validators, bootstrap, and summary scripts
configs/                         Fixed YAML configs for reported runs
data/processed/                  Processed JSONL inputs used by the paper experiments
experiment_backups/              Frozen result summaries, protocol manifests, CIs, and final tables
README_REPRODUCE.md              Full reproduction guide
ARTIFACT_MANIFEST.md             Paper-table-to-repository artifact map
requirements.txt                 Runtime dependencies
pyproject.toml                   Package metadata
```

The materialized processed inputs expected for the paper release are:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
data/processed/hotpotqa_cue_200.jsonl
data/processed/hotpotqa_cue_500.jsonl
data/processed/twowiki_cue_500.jsonl
data/processed/babilong_cue_200_external.jsonl
```

The 2Wiki input is intentionally listed here because the submitted manuscript reports 2WikiMultiHopQA-ONCU-500 results. If it is absent in a lightweight checkout, regenerate it with `scripts/build_2wiki_cue.py` as described in `README_REPRODUCE.md`.

Two auxiliary inputs are generated from released builders rather than shipped as materialized JSONL in the current package:

```text
data/processed/controlled_scaling_3200.jsonl  # built by scripts/build_controlled_scaling_cue.py
data/processed/ruler_lite_240.jsonl           # built by scripts/build_ruler_lite.py
```

The frozen artifacts for these auxiliary audits are summary-level unless otherwise stated in `ARTIFACT_MANIFEST.md`.

---

## Quick reviewer check

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/check_release_artifacts.py
python scripts/check_release_artifacts.py --strict-data --strict-clean
```

A complete paper-release checkout should report:

```text
missing required: 0
result: PASS
```

The `--strict-data` mode checks that the materialized JSONL inputs referenced by the reported paper experiments are present. If the 2Wiki JSONL is not tracked in a lightweight branch, regenerate it first or add it from the released artifact bundle.

---

## Main and auxiliary experiment families

### Final 200-sample core matrix

```text
3 models × 2 datasets × 200 samples × 4 conditions = 4800 predictions
```

Models:

```text
qwen2.5:14b
qwen3:14b
gemma3:12b
```

Datasets:

```text
Controlled-ONCU-safe16K-200
HotpotQA-ONCU-200
```

Canonical frozen artifacts:

```text
experiment_backups/sci200_final_3model_20260525/
```

### 2WikiMultiHopQA-ONCU-500 validation

```text
3 models × 500 samples × 4 conditions = 6000 predictions
```

Canonical frozen artifacts:

```text
experiment_backups/twowiki_500_validation_20260527/
```

### HotpotQA-500 robustness

Larger HotpotQA-500 runs check whether the HotpotQA full-context-over-retrieved pattern remains stable at larger sample size.

Canonical frozen artifacts:

```text
experiment_backups/hotpotqa_500_robustness_20260525/
```

### BABILong-200 external validation

BABILong-200 is reported as **external answer-performance validation**, not as an ONCU benchmark, because the current BABILong adapter does not provide oracle-evidence annotations compatible with ONCU.

Canonical frozen artifacts:

```text
experiment_backups/babilong_200_external_20260526/
```

### Model-family extension

The model-family extension adds `llama3.1:8b` and `mistral-small3.1:24b` on Controlled-ONCU, HotpotQA-ONCU, and 2WikiMultiHopQA-ONCU protocols. The directory contains fixed configs, protocol manifests, resolved configs, logs, per-sample metrics, and table summaries; the root archive `model_family_extension_for_paper.tar.gz` preserves the packaged extension artifact.

Canonical frozen artifacts:

```text
experiment_backups/model_family_extension_20260601/
model_family_extension_for_paper.tar.gz
```

### Retriever-family ONCU sensitivity

The matched dense@16 and hybrid@16 ONCU sensitivity reruns test whether the lexical@3 diagnostic intervention alone drives the retrieval-conditioned conclusions. These runs are not advertised as the best RAG configuration; they are matched sensitivity checks inside the four-condition protocol.

Canonical frozen artifacts:

```text
experiment_backups/retriever_family_oncu_sensitivity_20260602/
configs/retriever_family_oncu_sensitivity/
```

### Retriever-family ablation

The repository includes a reviewer-facing retriever-family ablation to test
whether retrieved-evidence failures are specific to the default lexical retriever.
See `configs/ablations/retriever_family_hotpotqa_qwen25.yaml`,
`configs/ablations/retriever_family_twowiki_qwen25.yaml`, and
`scripts/run_retriever_family_ablation.py`.

Reader-facing retriever-family summaries are archived under:

```text
experiment_backups/reader_facing_retriever_family_20260530/
reader_facing_summary_for_paper.tar.gz
```

### Controlled context-length and position scaling summary

The repository also includes a controlled scaling audit for ONCU as a
function of context length and fine-grained evidence position. This extension
uses ten evidence-position deciles (`pos_00` ... `pos_09`) across 4K, 8K, 16K,
and 32K contexts, while retaining the controlled distractor and reasoning-type
factors.

Key files:

```text
scripts/build_controlled_scaling_cue.py
scripts/summarize_controlled_scaling.py
configs/scaling/controlled_scaling_qwen25_14b_3200.yaml
configs/scaling/controlled_scaling_qwen3_14b_3200.yaml
configs/scaling/controlled_scaling_gemma3_12b_3200.yaml
```

The controlled-scaling input is generated by `scripts/build_controlled_scaling_cue.py`. The current release contains frozen summary artifacts rather than a full raw-response archive for this auxiliary audit:

```text
experiment_backups/controlled_scaling_20260527/summary/
```

### RULER-lite external validation

RULER-lite is reported as answer-only external validation, not as an ONCU benchmark. Its input is generated by `scripts/build_ruler_lite.py`, evaluated by `scripts/run_ruler_lite_external.py`, and summarized by `scripts/summarize_ruler_lite_external.py`.

Canonical frozen artifacts:

```text
experiment_backups/ruler_lite_external_20260530_final/
```

### Failure taxonomy and human validation

The failure-taxonomy audit includes the stratified sample, anonymous annotations, adjudicated labels, agreement summaries, confusion matrices, and LaTeX tables.

Canonical frozen artifacts:

```text
experiment_backups/failure_taxonomy_human_validation_20260530/
```

### Cross-encoder reranking audit

The five-model cross-encoder reranking audit is reported as a summary-only appendix sensitivity table in the manuscript. The current repository snapshot does not include a full reranking runner/config directory or raw reranking-output archive, so it is not a primary release-check target.

---

## Notes on historical artifacts

Older backup folders such as `experiment_backups/core_2x2_qwen25_qwen3_20260524/`, `experiment_backups/sci200_partial_qwen25_20260525/`, and `experiment_backups/sci200_qwen_family_20260525/`, if present, are historical intermediate backups and are not used for the submitted paper tables.


## Reviewer-facing statistical support

The release includes a statistical support layer in addition to the descriptive ONCU tables. Run:

```bash
python scripts/statistical_modeling.py
```

to regenerate paired effect-size summaries, bootstrap confidence intervals, Holm/FDR adjusted significance diagnostics, and compact LaTeX tables under `experiment_backups/statistical_modeling_20260530/`.

## License

The source code in this repository is licensed under the MIT License. See `LICENSE`.

The paper text, figures, tables, documentation, README files, and supplementary materials are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0), unless otherwise noted. See `LICENSE-DOCS`.

Third-party datasets and benchmark resources retain their original licenses and terms of use. This repository does not relicense third-party datasets. See `DATA_LICENSES.md`.
