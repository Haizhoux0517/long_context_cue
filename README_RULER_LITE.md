# RULER-lite External Validation Scripts

These scripts add a lightweight RULER-style external validation layer to the
ONCU project.

This is **not** an ONCU benchmark.  It is an external answer-performance
validation designed to test whether full-context and retrieved-context behavior
generalizes beyond the ONCU-compatible datasets.

## Files

- `build_ruler_lite.py`: generates a deterministic synthetic RULER-lite JSONL.
- `run_ruler_lite_external.py`: runs full-context and retrieved-context answer validation through Ollama.
- `summarize_ruler_lite_external.py`: writes CSV summaries and a LaTeX table.

## Recommended run

```bash
cd /workspace/long_context_cue

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

## Smoke test

```bash
python scripts/build_ruler_lite.py \
  --output data/processed/ruler_lite_smoke.jsonl \
  --samples-per-cell 1 \
  --context-lengths 4000 \
  --seed 42

python scripts/run_ruler_lite_external.py \
  --input data/processed/ruler_lite_smoke.jsonl \
  --output-dir outputs/ruler_lite_smoke \
  --models qwen2.5:14b \
  --conditions full_context retrieved_context \
  --limit 3 \
  --resume

python scripts/summarize_ruler_lite_external.py \
  --run-dir outputs/ruler_lite_smoke \
  --output-dir experiment_backups/ruler_lite_smoke
```

## Paper positioning

Use this as:

> External long-context answer-performance validation, not ONCU.

Do not write that RULER-lite computes ONCU unless you add a compatible
no-evidence/oracle-evidence protocol.
