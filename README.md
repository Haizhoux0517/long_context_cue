# Long-Context ONCU Diagnostic Framework

This repository contains the code, fixed configurations, processed inputs, and frozen result artifacts for the paper:

> **Oracle-Normalized Evidence Utilization: A Diagnostic Framework for Long-Context and Retrieval-Augmented Language Models**

The project evaluates whether long-context and retrieval-augmented language models recover the evidence-derived advantage made available by a context. The main diagnostic metric is **Oracle-Normalized Context Utilization (ONCU)**, which normalizes a contextual condition between a no-evidence baseline and an oracle-evidence reference.

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

The processed inputs expected for the paper release are:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
data/processed/hotpotqa_cue_200.jsonl
data/processed/hotpotqa_cue_500.jsonl
data/processed/twowiki_cue_500.jsonl
data/processed/babilong_cue_200_external.jsonl
```

The 2Wiki input is intentionally listed here because the submitted manuscript reports 2WikiMultiHopQA-ONCU-500 results. If it is absent in a lightweight checkout, regenerate it with `scripts/build_2wiki_cue.py` as described in `README_REPRODUCE.md`.

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

## Main experiment families

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

---

## Notes on historical artifacts

Only these release directories are used for the current paper claims:

```text
experiment_backups/sci200_final_3model_20260525/
experiment_backups/twowiki_500_validation_20260527/
experiment_backups/hotpotqa_500_robustness_20260525/
experiment_backups/babilong_200_external_20260526/
```

Older backup folders, if present, are historical intermediate backups and are not used for the submitted paper tables.

### Retriever-family ablation

The repository includes a reviewer-facing retriever-family ablation to test
whether retrieved-evidence failures are specific to the default lexical retriever.
See `configs/ablations/retriever_family_hotpotqa_qwen25.yaml`,
`configs/ablations/retriever_family_twowiki_qwen25.yaml`, and
`scripts/run_retriever_family_ablation.py`.
