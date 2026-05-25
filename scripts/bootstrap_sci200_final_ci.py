import argparse
import numpy as np
import pandas as pd
from pathlib import Path


RUNS = {
    ("Qwen2.5-14B", "Controlled-safe16K-200"): "controlled_safe16k_qwen25_14b_200_core_final",
    ("Qwen2.5-14B", "HotpotQA-ONCU-200"): "hotpotqa_qwen25_14b_200_core_final",
    ("Qwen3-14B", "Controlled-safe16K-200"): "controlled_safe16k_qwen3_14b_200_core_final",
    ("Qwen3-14B", "HotpotQA-ONCU-200"): "hotpotqa_qwen3_14b_200_core_final",
    ("Gemma3-12B", "Controlled-safe16K-200"): "controlled_safe16k_gemma3_12b_200_core_final",
    ("Gemma3-12B", "HotpotQA-ONCU-200"): "hotpotqa_gemma3_12b_200_core_final",
}


METRICS = [
    "answer_f1_relaxed",
    "answer_f1_strict",
    "exact_match_relaxed",
    "evidence_f1",
]


def bootstrap_mean(values, n_boot=5000, seed=42):
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]

    if len(values) == 0:
        return np.nan, np.nan, np.nan, 0

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    boot_means = values[idx].mean(axis=1)

    mean = values.mean()
    low, high = np.percentile(boot_means, [2.5, 97.5])
    return mean, low, high, len(values)


def detect_oncu_column(df):
    candidates = [
        "oncu_clipped",
        "cue_clipped",
        "oncu",
        "cue",
        "oncu_score",
        "cue_score",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(
        "Could not find ONCU/CUE value column in oncu_metrics_multiscore.csv. "
        f"Available columns: {list(df.columns)}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", default="outputs")
    parser.add_argument(
        "--outdir",
        default="experiment_backups/sci200_final_3model_20260525/ci",
    )
    parser.add_argument("--n-boot", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    metric_rows = []
    oncu_rows = []

    for (model, dataset), run in RUNS.items():
        metric_path = Path(args.outputs) / run / "results" / "per_sample_metrics.csv"
        oncu_path = Path(args.outputs) / run / "results" / "oncu_metrics_multiscore.csv"

        if not metric_path.exists():
            raise FileNotFoundError(metric_path)

        if not oncu_path.exists():
            raise FileNotFoundError(
                f"{oncu_path} not found. Run scripts/recompute_oncu.py for {run} first."
            )

        metrics_df = pd.read_csv(metric_path)

        for method in ["no_evidence", "direct", "retrieve_then_read", "oracle"]:
            sub = metrics_df[metrics_df["method"] == method]

            for metric in METRICS:
                mean, low, high, n = bootstrap_mean(
                    sub[metric].values,
                    n_boot=args.n_boot,
                    seed=args.seed,
                )
                metric_rows.append({
                    "Model": model,
                    "Dataset": dataset,
                    "Condition": method,
                    "Metric": metric,
                    "Mean": mean,
                    "CI95_Low": low,
                    "CI95_High": high,
                    "N": n,
                    "Parse_Errors": int(sub["parse_error"].notna().sum()),
                })

        oncu_df = pd.read_csv(oncu_path)
        oncu_df = oncu_df[oncu_df["score_field"] == "answer_f1_relaxed"].copy()

        value_col = detect_oncu_column(oncu_df)

        for long_method in ["direct", "retrieve_then_read"]:
            sub = oncu_df[oncu_df["long_method"] == long_method].copy()

            mean, low, high, n = bootstrap_mean(
                sub[value_col].values,
                n_boot=args.n_boot,
                seed=args.seed,
            )
            oncu_rows.append({
                "Model": model,
                "Dataset": dataset,
                "Condition": long_method,
                "Metric": "ONCU_Relaxed_F1",
                "Mean": mean,
                "CI95_Low": low,
                "CI95_High": high,
                "Valid_Groups": n,
                "Value_Column": value_col,
            })

    metric_table = pd.DataFrame(metric_rows)
    oncu_table = pd.DataFrame(oncu_rows)

    metric_table.to_csv(outdir / "sci200_metric_bootstrap_ci.csv", index=False)
    oncu_table.to_csv(outdir / "sci200_oncu_bootstrap_ci.csv", index=False)

    with open(outdir / "sci200_metric_bootstrap_ci.tex", "w", encoding="utf-8") as f:
        f.write(metric_table.to_latex(index=False, float_format="%.3f", escape=False))

    with open(outdir / "sci200_oncu_bootstrap_ci.tex", "w", encoding="utf-8") as f:
        f.write(oncu_table.to_latex(index=False, float_format="%.3f", escape=False))

    print("\n=== Final SCI-200 Metric Bootstrap CI ===")
    print(metric_table.round(3).to_string(index=False))

    print("\n=== Final SCI-200 ONCU Bootstrap CI ===")
    print(oncu_table.round(3).to_string(index=False))

    print(f"\nWrote bootstrap CI files to: {outdir}")


if __name__ == "__main__":
    main()
