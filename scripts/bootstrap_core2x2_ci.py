import argparse
import numpy as np
import pandas as pd
from pathlib import Path


RUNS = {
    ("Qwen2.5-14B", "Controlled-safe16K"): "controlled_safe16k_qwen25_14b_100_core",
    ("Qwen2.5-14B", "HotpotQA-ONCU-100"): "hotpotqa_qwen25_14b_100_core",
    ("Qwen3-14B", "Controlled-safe16K"): "controlled_safe16k_qwen3_14b_100_core",
    ("Qwen3-14B", "HotpotQA-ONCU-100"): "hotpotqa_qwen3_14b_100_core",
}


def bootstrap_mean(values, n_boot=2000, seed=42):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return np.nan, np.nan, np.nan

    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        means.append(sample.mean())

    mean = values.mean()
    low, high = np.percentile(means, [2.5, 97.5])
    return mean, low, high


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", default="outputs")
    parser.add_argument("--outdir", default="experiment_backups/core_2x2_qwen25_qwen3_20260524/ci")
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []

    for (model, dataset), run in RUNS.items():
        path = Path(args.outputs) / run / "results" / "per_sample_metrics.csv"
        df = pd.read_csv(path)

        for method in ["no_evidence", "direct", "retrieve_then_read", "oracle"]:
            sub = df[df["method"] == method]

            for metric in ["answer_f1_relaxed", "answer_f1_strict", "exact_match_relaxed", "evidence_f1"]:
                mean, low, high = bootstrap_mean(
                    sub[metric].values,
                    n_boot=args.n_boot,
                    seed=42,
                )
                rows.append({
                    "Model": model,
                    "Dataset": dataset,
                    "Condition": method,
                    "Metric": metric,
                    "Mean": mean,
                    "CI95_Low": low,
                    "CI95_High": high,
                    "N": len(sub),
                    "Parse_Errors": int(sub["parse_error"].notna().sum()),
                })

    result = pd.DataFrame(rows)
    result.to_csv(outdir / "core_2x2_metric_bootstrap_ci.csv", index=False)

    with open(outdir / "core_2x2_metric_bootstrap_ci.tex", "w", encoding="utf-8") as f:
        f.write(result.to_latex(index=False, float_format="%.3f", escape=False))

    print(result.round(3).to_string(index=False))
    print(f"\nWrote CI files to {outdir}")


if __name__ == "__main__":
    main()
