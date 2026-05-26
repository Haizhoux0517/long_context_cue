import numpy as np
import pandas as pd
from pathlib import Path

RUNS = {
    ("Qwen2.5-14B", "BABILong-200"): "babilong_qwen25_14b_200_external",
    ("Qwen3-14B", "BABILong-200"): "babilong_qwen3_14b_200_external",
    ("Gemma3-12B", "BABILong-200"): "babilong_gemma3_12b_200_external",
}

METRICS = [
    "answer_f1_relaxed",
    "answer_f1_strict",
    "exact_match_relaxed",
]

def bootstrap_mean(values, n_boot=5000, seed=42):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    boot = values[idx].mean(axis=1)
    return values.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5), len(values)

rows = []
outdir = Path("experiment_backups/babilong_200_external_20260526/ci")
outdir.mkdir(parents=True, exist_ok=True)

for (model, dataset), run in RUNS.items():
    df = pd.read_csv(f"outputs/{run}/results/per_sample_metrics.csv")

    for condition in ["no_evidence", "direct", "retrieve_then_read"]:
        sub = df[df["method"] == condition]
        for metric in METRICS:
            mean, low, high, n = bootstrap_mean(sub[metric].values)
            rows.append({
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

out = pd.DataFrame(rows)
out.to_csv(outdir / "babilong200_metric_bootstrap_ci.csv", index=False)

print(out.round(3).to_string(index=False))
print("\nWrote:", outdir / "babilong200_metric_bootstrap_ci.csv")
