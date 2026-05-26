import numpy as np
import pandas as pd
from pathlib import Path

RUNS = {
    ("Qwen2.5-14B", "HotpotQA-500"): "hotpotqa_qwen25_14b_500_core_robust",
    ("Qwen3-14B", "HotpotQA-500"): "hotpotqa_qwen3_14b_500_core_robust",
    ("Gemma3-12B", "HotpotQA-500"): "hotpotqa_gemma3_12b_500_core_robust",
}

METRICS = [
    "answer_f1_relaxed",
    "answer_f1_strict",
    "evidence_f1",
]

def bootstrap_mean(values, n_boot=5000, seed=42):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    boot = values[idx].mean(axis=1)
    return values.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5), len(values)

outdir = Path("experiment_backups/hotpotqa_500_robustness_20260525/ci")
outdir.mkdir(parents=True, exist_ok=True)

metric_rows = []
oncu_rows = []

for (model, dataset), run in RUNS.items():
    metrics = pd.read_csv(f"outputs/{run}/results/per_sample_metrics.csv")

    for condition in ["direct", "retrieve_then_read", "oracle", "no_evidence"]:
        sub = metrics[metrics["method"] == condition]
        for metric in METRICS:
            mean, low, high, n = bootstrap_mean(sub[metric].values)
            metric_rows.append({
                "Model": model,
                "Dataset": dataset,
                "Condition": condition,
                "Metric": metric,
                "Mean": mean,
                "CI95_Low": low,
                "CI95_High": high,
                "N": n,
                "Parse_Errors": int(sub["parse_error"].notna().sum()),
            })

    oncu = pd.read_csv(f"outputs/{run}/results/oncu_metrics_multiscore.csv")
    oncu = oncu[oncu["score_field"] == "answer_f1_relaxed"].copy()

    for condition in ["direct", "retrieve_then_read"]:
        sub = oncu[(oncu["long_method"] == condition) & (oncu["oncu_valid"] == True)]
        mean, low, high, n = bootstrap_mean(sub["oncu_clipped"].values)
        oncu_rows.append({
            "Model": model,
            "Dataset": dataset,
            "Condition": condition,
            "Metric": "ONCU_Relaxed_F1",
            "Mean": mean,
            "CI95_Low": low,
            "CI95_High": high,
            "Valid_Groups": n,
        })

metric_df = pd.DataFrame(metric_rows)
oncu_df = pd.DataFrame(oncu_rows)

metric_df.to_csv(outdir / "hotpotqa500_metric_bootstrap_ci.csv", index=False)
oncu_df.to_csv(outdir / "hotpotqa500_oncu_bootstrap_ci.csv", index=False)

print("\n=== HotpotQA-500 Metric Bootstrap CI ===")
print(metric_df.round(3).to_string(index=False))

print("\n=== HotpotQA-500 ONCU Bootstrap CI ===")
print(oncu_df.round(3).to_string(index=False))

print("\nWrote:", outdir)
