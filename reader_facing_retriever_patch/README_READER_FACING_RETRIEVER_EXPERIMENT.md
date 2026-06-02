# Reader-facing retriever-family ONCU experiment

This patch adds the experiment required to support any paper-level claim about retrieve-then-read / RAG-style systems.
The existing retrieval-family ablation is retrieval-only. This experiment actually runs the reader on lexical, dense, and hybrid retrieved contexts and recomputes ONCU against the existing no-evidence and oracle-evidence references.

## Install requirements

```bash
pip install -r requirements.txt
```

The dense retriever uses `sentence-transformers/all-MiniLM-L6-v2` by default.

## Run all reader-facing experiments

From the repository root:

```bash
for cfg in configs/ablations/reader_facing_retfam_*.yaml; do
  echo "Running $cfg"
  PYTHONUNBUFFERED=1 python scripts/run_retriever_family_ablation.py \
    --config "$cfg" \
    --run-reader
done
```

This runs:

- HotpotQA-ONCU-200: Qwen2.5-14B, Qwen3-14B, Gemma3-12B
- 2WikiMultiHopQA-ONCU-500: Qwen2.5-14B, Qwen3-14B, Gemma3-12B
- Retriever families: lexical, dense, hybrid
- Reader top-k: 3, 8, 16

Total reader-facing predictions:

- HotpotQA: `3 models × 200 samples × 3 retrievers × 3 top-k = 5,400`
- 2Wiki: `3 models × 500 samples × 3 retrievers × 3 top-k = 13,500`
- Total: `18,900` reader predictions, plus retrieval-only diagnostics.

## Summarize

```bash
python scripts/summarize_reader_facing_retriever_results.py \
  --run-dirs outputs/reader_facing_retfam_* \
  --output-dir experiment_backups/reader_facing_retriever_family_20260530
```

Main output files:

```text
experiment_backups/reader_facing_retriever_family_20260530/reader_facing_joined_summary.csv
experiment_backups/reader_facing_retriever_family_20260530/reader_facing_winners.csv
experiment_backups/reader_facing_retriever_family_20260530/reader_facing_retfam_results_table.tex
experiment_backups/reader_facing_retriever_family_20260530/retrieval_only_family_summary.csv
```

## Paper interpretation rule

Do not claim system-level RAG conclusions until the `reader_facing_joined_summary.csv` exists.
If dense or hybrid improves retrieval-only coverage but not reader-facing ONCU, the paper should state that better retrieval coverage does not automatically transfer to reader-side answer utilization.
If dense or hybrid improves both evidence coverage and reader-facing ONCU, then the paper can retain a stronger retrieve-then-read diagnostic claim.
