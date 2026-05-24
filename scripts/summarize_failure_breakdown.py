import pandas as pd
from pathlib import Path


RUNS = {
    ("Qwen2.5-14B", "Controlled-safe16K"): "controlled_safe16k_qwen25_14b_100_core",
    ("Qwen2.5-14B", "HotpotQA-ONCU-100"): "hotpotqa_qwen25_14b_100_core",
    ("Qwen3-14B", "Controlled-safe16K"): "controlled_safe16k_qwen3_14b_100_core",
    ("Qwen3-14B", "HotpotQA-ONCU-100"): "hotpotqa_qwen3_14b_100_core",
}


def main():
    outdir = Path("experiment_backups/core_2x2_qwen25_qwen3_20260524/failure_analysis")
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []

    for (model, dataset), run in RUNS.items():
        df = pd.read_csv(f"outputs/{run}/results/per_sample_metrics.csv")

        if "failure_type" not in df.columns:
            raise ValueError(f"{run} has no failure_type column")

        for method in ["direct", "retrieve_then_read", "oracle", "no_evidence"]:
            sub = df[df["method"] == method]
            counts = sub["failure_type"].fillna("unknown").value_counts()

            total = len(sub)
            for failure_type, count in counts.items():
                rows.append({
                    "Model": model,
                    "Dataset": dataset,
                    "Condition": method,
                    "Failure_Type": failure_type,
                    "Count": int(count),
                    "Rate": count / total if total else 0.0,
                    "N": total,
                })

    result = pd.DataFrame(rows)
    result = result.sort_values(["Model", "Dataset", "Condition", "Failure_Type"])

    result.to_csv(outdir / "core_2x2_failure_breakdown.csv", index=False)

    with open(outdir / "core_2x2_failure_breakdown.tex", "w", encoding="utf-8") as f:
        f.write(result.to_latex(index=False, float_format="%.3f", escape=False))

    print(result.round(3).to_string(index=False))
    print(f"\nWrote failure breakdown to {outdir}")


if __name__ == "__main__":
    main()
