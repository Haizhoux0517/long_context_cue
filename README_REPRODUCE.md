# Reproducing the ONCU Diagnostic Experiments

This document describes how to audit and reproduce the experiments reported in:

> **Oracle-Normalized Evidence Utilization: A Diagnostic Framework for Long-Context and Retrieval-Augmented Language Models**

The release is organized around four layers:

1. fixed YAML configurations;
2. materialized or generated processed JSONL evaluation inputs;
3. deterministic local inference settings;
4. frozen result artifacts and table-level summaries.

For a paper-table-to-file mapping, see [`ARTIFACT_MANIFEST.md`](ARTIFACT_MANIFEST.md).

---

## 1. Release sanity check

Run the release checker first:

```bash
python scripts/check_release_artifacts.py
```

For a complete release that includes processed JSONL inputs and enforces root cleanliness, run:

```bash
python scripts/check_release_artifacts.py --strict-data --strict-clean
```

Expected result:

```text
missing required: 0
result: PASS
```

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


## Runtime/model metadata record

Before final archival release, generate the host-specific runtime record on the machine used for local Ollama inference:

```bash
python scripts/export_runtime_record.py \
  --output RUNTIME_REPRODUCIBILITY_RECORD.md \
  --json-output runtime_reproducibility_record.json
```

This records the available runtime metadata for the reproduction host: package versions, CUDA/PyTorch status, GPU/VRAM information, deterministic decoding controls, context-window setting, requested model tags, and local `ollama show --verbose` records when Ollama is available. Exact Ollama version, model digest, and quantization fields are recorded only when exposed by the installed Ollama version and local model store; otherwise the generated record preserves the unavailable-command diagnostics. Keep the generated Markdown file with the release artifacts.

Local Ollama models used in the reported experiments:

```bash
ollama pull qwen2.5:14b
ollama pull qwen3:14b
ollama pull gemma3:12b
ollama pull llama3.1:8b
ollama pull mistral-small3.1:24b
ollama list
```

Record the local `ollama --version`, `ollama list`, `ollama show <model>`, hardware, and wall-clock runtime before rerunning inference. The release fixes model tags and decoding/configuration settings, but exact Ollama backend versions, model digests or quantization metadata, and hardware/runtime characteristics are local-run metadata rather than immutable paper artifacts.

Core inference settings recorded in the fixed configs:

```text
temperature = 0.0
num_ctx = 32768
max_tokens = 1024
retrieval.top_k = 3 for the main matrix, HotpotQA-500, and 2Wiki-500 runs
retrieval.chunk_size = 220
retrieval.overlap = 40
protocol.version = diagnostic_v1_fixed
```

---

## 3. Processed input files

The paper release materializes five processed JSONL inputs:

```text
data/processed/controlled_oncu_200_safe16k.jsonl
data/processed/hotpotqa_cue_200.jsonl
data/processed/hotpotqa_cue_500.jsonl
data/processed/twowiki_cue_500.jsonl
data/processed/babilong_cue_200_external.jsonl
```

These files contain sample IDs, questions, passage-annotated contexts, gold answers, and metadata. ONCU-compatible datasets also contain oracle-evidence identifiers. BABILong-200 is used only for answer-performance validation because the current adapter does not expose oracle evidence compatible with ONCU.

If the files are absent, regenerate them before rerunning inference:

```bash
mkdir -p data/processed

python scripts/build_controlled_cue.py   --output data/processed/controlled_oncu_200_safe16k.jsonl   --limit 200   --context-lengths 4000 8000 16000   --seed 42

python scripts/build_hotpotqa_cue.py   --output data/processed/hotpotqa_cue_200.jsonl   --limit 200   --seed 42

python scripts/build_hotpotqa_cue.py   --output data/processed/hotpotqa_cue_500.jsonl   --limit 500   --seed 42

python scripts/build_2wiki_cue.py   --output data/processed/twowiki_cue_500.jsonl   --limit 500   --seed 42

python scripts/build_babilong_cue.py   --output data/processed/babilong_cue_200_external.jsonl   --configs 0k 1k 2k 4k   --tasks qa1 qa2 qa3 qa6 qa7   --limit-per-task 10
```

Expected 2Wiki generated-data audit:

```text
samples = 500
skipped = 0
sha256(data/processed/twowiki_cue_500.jsonl) =
081189b8766d7924661b218579ad808fb1fc293adffa41f3863b70d55ae5917a
```

Original public datasets, including HotpotQA, 2WikiMultiHopQA, and BABILong, should be obtained from their official sources subject to their licenses and terms of use.

Two auxiliary inputs are generated from released scripts rather than shipped as materialized JSONL in the current package:

```bash
python scripts/build_controlled_scaling_cue.py \
  --output data/processed/controlled_scaling_3200.jsonl \
  --num-per-cell 5 \
  --seed 42

python scripts/build_ruler_lite.py \
  --output data/processed/ruler_lite_240.jsonl \
  --samples-per-cell 20 \
  --seed 42
```

The corresponding controlled-scaling and RULER-lite frozen artifacts are summary-level release artifacts, not full raw-response archives.

---

## 4. Final 200-sample core matrix

The balanced main matrix evaluates three models on two datasets under four fixed diagnostic conditions:

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
python scripts/validate_diagnostic_protocol.py   --require-core   configs/controlled_safe16k_qwen25_14b_200_core_final.yaml   configs/controlled_safe16k_qwen3_14b_200_core_final.yaml   configs/controlled_safe16k_gemma3_12b_200_core_final.yaml   configs/hotpotqa_qwen25_14b_200_core_final.yaml   configs/hotpotqa_qwen3_14b_200_core_final.yaml   configs/hotpotqa_gemma3_12b_200_core_final.yaml
```

Run one config:

```bash
python -m longcue.run_experiment   --config configs/hotpotqa_qwen25_14b_200_core_final.yaml
```

Frozen artifacts used by the paper:

```text
experiment_backups/sci200_final_3model_20260525/
```

---

## 5. 2WikiMultiHopQA-ONCU-500 validation

2WikiMultiHopQA-ONCU-500 is the larger realistic multi-hop validation component:

```text
3 models × 500 samples × 4 conditions = 6000 predictions
```

Configs:

```text
configs/twowiki_qwen25_14b_500_core.yaml
configs/twowiki_qwen3_14b_500_core.yaml
configs/twowiki_gemma3_12b_500_core.yaml
```

Validate configs:

```bash
python scripts/validate_diagnostic_protocol.py   --require-core   configs/twowiki_qwen25_14b_500_core.yaml   configs/twowiki_qwen3_14b_500_core.yaml   configs/twowiki_gemma3_12b_500_core.yaml
```

Run the completed 2Wiki experiment family:

```bash
python -m longcue.run_experiment   --config configs/twowiki_qwen25_14b_500_core.yaml

python -m longcue.run_experiment   --config configs/twowiki_qwen3_14b_500_core.yaml

python -m longcue.run_experiment   --config configs/twowiki_gemma3_12b_500_core.yaml
```

Frozen artifacts used by the paper:

```text
experiment_backups/twowiki_500_validation_20260527/
```

Regenerate 2Wiki paper-facing derived tables from frozen per-sample metrics:

```bash
python scripts/recompute_twowiki500_tables.py
```

---

## 6. HotpotQA retrieval-budget ablation and HotpotQA-500 robustness

Ablation configs:

```text
configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml
configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml
```

HotpotQA-500 robustness configs:

```text
configs/hotpotqa_qwen25_14b_500_core_robust.yaml
configs/hotpotqa_qwen3_14b_500_core_robust.yaml
configs/hotpotqa_gemma3_12b_500_core_robust.yaml
```

Frozen artifacts:

```text
experiment_backups/hotpotqa_500_robustness_20260525/
```

---

## 7. BABILong-200 external validation

BABILong-200 is not treated as an ONCU benchmark. It is used as external answer-performance validation because the current BABILong adapter does not provide oracle-evidence annotations compatible with ONCU.

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

---

## 8. Model-family extension

The model-family extension adds `llama3.1:8b` and `mistral-small3.1:24b` to the Controlled-ONCU, HotpotQA-ONCU, and 2WikiMultiHopQA-ONCU protocols.

Configs:

```text
configs/model_family_extension/controlled_safe16k_200_llama31_8b_core.yaml
configs/model_family_extension/controlled_safe16k_200_mistral_small31_24b_core.yaml
configs/model_family_extension/hotpotqa_200_llama31_8b_core.yaml
configs/model_family_extension/hotpotqa_200_mistral_small31_24b_core.yaml
configs/model_family_extension/twowiki_500_llama31_8b_core.yaml
configs/model_family_extension/twowiki_500_mistral_small31_24b_core.yaml
```

Frozen artifacts:

```text
experiment_backups/model_family_extension_20260601/
model_family_extension_for_paper.tar.gz
```

The directory contains resolved configs, protocol manifests, logs, per-sample metrics, aggregate metrics, CUE/ONCU metrics, and table summaries for the completed extension runs.

## 9. RULER-lite external validation

RULER-lite is not treated as an ONCU benchmark. It is an answer-only external validation because the current adapter does not provide the full no-evidence and oracle-evidence reference protocol required for ONCU.

Build and run:

```bash
python scripts/build_ruler_lite.py \
  --output data/processed/ruler_lite_240.jsonl \
  --samples-per-cell 20 \
  --seed 42

python scripts/run_ruler_lite_external.py \
  --input data/processed/ruler_lite_240.jsonl \
  --output-dir outputs/ruler_lite_external_20260530 \
  --models qwen2.5:14b qwen3:14b gemma3:12b \
  --conditions full_context retrieved_context \
  --top-k 3 \
  --resume

python scripts/summarize_ruler_lite_external.py \
  --run-dir outputs/ruler_lite_external_20260530 \
  --output-dir experiment_backups/ruler_lite_external_20260530
```

Frozen artifacts used by the manuscript:

```text
experiment_backups/ruler_lite_external_20260530_final/
```

## 10. Failure taxonomy and human validation

The failure-taxonomy human validation artifacts include the blind audit sample, annotation codebook, anonymous annotator files, adjudicated final labels, agreement summaries, confusion matrices, and LaTeX tables.

Frozen artifacts:

```text
experiment_backups/failure_taxonomy_human_validation_20260530/
```

Regenerate summaries from the released annotation files:

```bash
python scripts/summarize_failure_taxonomy_audit.py \
  --output-dir experiment_backups/failure_taxonomy_human_validation_20260530
```

## 11. Regenerating confidence intervals and summaries

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

2Wiki-500 derived summaries:

```bash
python scripts/recompute_twowiki500_tables.py
```

Failure breakdown for the final 200-sample matrix:

```bash
python scripts/summarize_sci200_failure_breakdown.py
```

---

## 12. Notes for reviewers

The released summaries are intended to allow table-level auditing without rerunning all local LLM inference. Full reruns require local Ollama model availability, GPU/CPU resources, and the original public source datasets. Structured-output parse failures are retained and scored as incorrect in the released metrics.

## 13. Retriever-family ablations and ONCU sensitivity

### Matched dense/hybrid ONCU sensitivity

This sensitivity run varies only the retrieved-evidence family inside the matched four-condition protocol. It is not a claim that dense@16 or hybrid@16 is the strongest RAG system; it checks whether the paper's retrieval-conditioned ONCU pattern depends on lexical@3.

Generate or audit configs:

```bash
python scripts/prepare_retriever_family_oncu_sensitivity.py
```

Run one generated config:

```bash
python longcue/run_experiment.py \
  --config configs/retriever_family_oncu_sensitivity/hotpotqa200_qwen25_dense_k16.yaml
```

Frozen artifacts:

```text
experiment_backups/retriever_family_oncu_sensitivity_20260602/
```

### Retrieval-only and reader-facing retriever-family audits

This ablation is designed to answer whether the retrieved-evidence bottleneck is
specific to the default deterministic lexical retriever. It should be treated as a
diagnostic ablation, not as a replacement for the fixed four-condition ONCU matrix.

Install the optional dense-retrieval dependency before running dense or hybrid
retrievers:

```bash
pip install -r requirements.txt
```

Run retrieval-only diagnostics first:

```bash
python scripts/run_retriever_family_ablation.py \
  --config configs/ablations/retriever_family_hotpotqa_qwen25.yaml

python scripts/run_retriever_family_ablation.py \
  --config configs/ablations/retriever_family_twowiki_qwen25.yaml
```

The retrieval-only output reports evidence recall, full-chain coverage,
distractor passage rate, and oracle-hit rate for lexical, dense, hybrid,
deterministic iterative, and oracle retrievers over `top_k = 3, 5, 8, 16`.

If retrieval-only diagnostics show that dense or hybrid retrieval changes evidence
coverage, run the reader-facing ablation for Qwen2.5-14B:

```bash
python scripts/run_retriever_family_ablation.py \
  --config configs/ablations/retriever_family_hotpotqa_qwen25.yaml \
  --run-reader

python scripts/run_retriever_family_ablation.py \
  --config configs/ablations/retriever_family_twowiki_qwen25.yaml \
  --run-reader
```

Reader-facing outputs include answer F1, evidence F1, parse errors, and
ONCU-Relaxed-F1 computed against the frozen no-evidence and oracle reference
rows from the corresponding release artifacts.

Summarize reader-facing outputs:

```bash
python scripts/summarize_reader_facing_retriever_results.py \
  --run-dirs outputs/reader_facing_retfam_* \
  --output-dir experiment_backups/reader_facing_retriever_family_20260530
```

Frozen summary artifacts:

```text
experiment_backups/retriever_family_ablation_20260527/
experiment_backups/reader_facing_retriever_family_20260530/
reader_facing_summary_for_paper.tar.gz
```

---

## 14. Controlled context-length and position scaling extension

This extension audits ONCU as a function of context length and fine-grained
evidence location. It is motivated by position-sensitive long-context failures
and should be treated as a controlled diagnostic extension rather than as a
replacement for the fixed main matrix.

Generate the 3200-sample scaling input:

```bash
python scripts/build_controlled_scaling_cue.py \
  --output data/processed/controlled_scaling_3200.jsonl \
  --num-per-cell 5 \
  --seed 42
```

Expected grid size:

```text
4 context lengths × 10 evidence-position deciles × 4 distractor levels × 4 reasoning types × 5 seeds = 3200 samples
```

Validate the fixed scaling configs:

```bash
python scripts/validate_diagnostic_protocol.py \
  --require-core \
  configs/scaling/controlled_scaling_qwen25_14b_3200.yaml \
  configs/scaling/controlled_scaling_qwen3_14b_3200.yaml \
  configs/scaling/controlled_scaling_gemma3_12b_3200.yaml
```

Run the first model before expanding to the full three-model family:

```bash
python -m longcue.run_experiment \
  --config configs/scaling/controlled_scaling_qwen25_14b_3200.yaml
```

The current release includes summary-level controlled-scaling artifacts. To reproduce them after rerunning local inference, summarize the scaling outputs:

```bash
python scripts/summarize_controlled_scaling.py \
  --run-dir outputs/controlled_scaling_qwen25_14b_3200 \
  --output-dir experiment_backups/controlled_scaling_20260527/summary
```

For all three models, repeat `--run-dir`:

```bash
python scripts/summarize_controlled_scaling.py \
  --run-dir outputs/controlled_scaling_qwen25_14b_3200 \
  --run-dir outputs/controlled_scaling_qwen3_14b_3200 \
  --run-dir outputs/controlled_scaling_gemma3_12b_3200 \
  --output-dir experiment_backups/controlled_scaling_20260527/summary
```

The summarizer writes:

```text
controlled_scaling_condition_summary.csv
controlled_scaling_oncu_by_length_position.csv
controlled_scaling_failure_heatmap.csv
controlled_scaling_regression.csv
controlled_scaling_heatmap_table.tex
controlled_scaling_regression_table.tex
```

---

## Statistical modeling support

After the frozen result artifacts have been generated or restored, regenerate the reviewer-facing statistical support tables with:

```bash
python scripts/statistical_modeling.py \
  --output-dir experiment_backups/statistical_modeling_20260530
```

The script produces paired condition contrasts, controlled length-position contrasts, retrieval-family contrasts, and compact regression-style diagnostics:

```text
experiment_backups/statistical_modeling_20260530/statistical_effects_summary.csv
experiment_backups/statistical_modeling_20260530/statistical_effects_table.tex
experiment_backups/statistical_modeling_20260530/statistical_regression_summary.csv
experiment_backups/statistical_modeling_20260530/statistical_regression_table.tex
experiment_backups/statistical_modeling_20260530/statistical_modeling_manifest.json
```

The confirmatory contrasts use paired/sample-matched resampling whenever the same examples are evaluated under multiple conditions. The regression rows are intended as diagnostic support for effect direction and magnitude, not as replacements for the released fixed-condition metrics.
