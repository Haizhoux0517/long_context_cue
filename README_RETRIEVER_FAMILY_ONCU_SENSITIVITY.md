# Retriever-Family ONCU Sensitivity Protocol

This extension creates four-condition ONCU configs in which only the retrieved-evidence input family is varied. It is intended to answer a reviewer concern about whether the main retrieved-evidence results depend on the deterministic lexical retriever.

The sensitivity run is **not** a new benchmark. It reuses the same four-condition ONCU protocol:

- no evidence
- full context
- retrieved evidence
- oracle-evidence reference

For each model and dataset, the no-evidence, full-context, and oracle-evidence conditions remain matched. The retrieved-evidence condition changes from the main lexical@3 setting to dense@16 or hybrid@16.

## Generate configs

```bash
python scripts/prepare_retriever_family_oncu_sensitivity.py
```

This writes configs under:

```text
configs/retriever_family_oncu_sensitivity/
```

## Run one config

```bash
PYTHONUNBUFFERED=1 python longcue/run_experiment.py \
  --config configs/retriever_family_oncu_sensitivity/hotpotqa200_qwen25_dense_k16.yaml
```

## Run all generated configs

```bash
mkdir -p outputs/logs
for cfg in configs/retriever_family_oncu_sensitivity/*.yaml; do
  name=$(basename "$cfg" .yaml)
  PYTHONUNBUFFERED=1 python longcue/run_experiment.py --config "$cfg" \
    2>&1 | tee "outputs/logs/${name}.log"
done
```

## Interpretation

Use the resulting `results/cue_metrics.csv`, `results/aggregate_metrics.csv`, and `results/per_sample_metrics.csv` files as a retriever-family ONCU sensitivity analysis. The paper should report these results only after the runs are completed and frozen under `experiment_backups/`.
