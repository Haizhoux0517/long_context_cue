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

METHODS = ["no_evidence", "direct", "retrieve_then_read", "oracle"]


def canonical_failure_type(x):
    if pd.isna(x) or str(x).strip() == "":
        return "unknown"

    s = str(x).strip().lower()

    if "parse" in s or "json" in s:
        return "parse_error"
    if "success" in s or s == "correct":
        return "success"
    if "localization" in s or "locat" in s:
        return "evidence_localization_failure"
    if "selection" in s or "select" in s:
        return "evidence_selection_failure"
    if "integration" in s or "integrat" in s:
        return "evidence_integration_failure"
    if "conversion" in s or "convert" in s:
        return "answer_conversion_failure"

    return s


def short_name(canonical):
    mapping = {
        "evidence_localization_failure": "Loc.",
        "evidence_selection_failure": "Sel.",
        "evidence_integration_failure": "Int.",
        "answer_conversion_failure": "Conv.",
        "success": "Succ.",
        "parse_error": "Parse",
        "unknown": "Other",
    }
    return mapping.get(canonical, "Other")


def main():
    outdir = Path("experiment_backups/sci200_final_3model_20260525/failure_analysis")
    outdir.mkdir(parents=True, exist_ok=True)

    long_rows = []
    compact_rows = []
    raw_value_rows = []

    for (model, dataset), run in RUNS.items():
        path = Path(f"outputs/{run}/results/per_sample_metrics.csv")
        if not path.exists():
            raise FileNotFoundError(path)

        df = pd.read_csv(path)

        if "failure_type" not in df.columns:
            raise ValueError(
                f"{run} has no failure_type column. Available columns: {list(df.columns)}"
            )

        raw_values = df["failure_type"].fillna("NaN").value_counts(dropna=False)
        for raw, count in raw_values.items():
            raw_value_rows.append({
                "Model": model,
                "Dataset": dataset,
                "Run": run,
                "Raw_Failure_Type": raw,
                "Count": int(count),
            })

        df["failure_type_canonical"] = df["failure_type"].apply(canonical_failure_type)

        # Treat parse errors explicitly, even if failure_type is missing or different.
        if "parse_error" in df.columns:
            parse_mask = df["parse_error"].notna()
            df.loc[parse_mask, "failure_type_canonical"] = "parse_error"

        for method in METHODS:
            sub = df[df["method"] == method].copy()
            n = len(sub)
            if n == 0:
                continue

            counts = sub["failure_type_canonical"].value_counts()

            row = {
                "Model": model,
                "Dataset": dataset,
                "Condition": method,
                "N": n,
            }

            # initialize compact percentages
            for col in ["Loc.", "Sel.", "Int.", "Conv.", "Succ.", "Parse", "Other"]:
                row[col] = 0.0

            for failure_type, count in counts.items():
                short = short_name(failure_type)
                row[short] += 100.0 * count / n

                long_rows.append({
                    "Model": model,
                    "Dataset": dataset,
                    "Condition": method,
                    "Failure_Type": failure_type,
                    "Count": int(count),
                    "Rate": count / n,
                    "Percent": 100.0 * count / n,
                    "N": n,
                })

            compact_rows.append(row)

    long_table = pd.DataFrame(long_rows)
    compact_table = pd.DataFrame(compact_rows)
    raw_values_table = pd.DataFrame(raw_value_rows)

    # Main paper table: contextual conditions only.
    contextual = compact_table[
        compact_table["Condition"].isin(["direct", "retrieve_then_read"])
    ].copy()

    condition_map = {
        "direct": "Full Context",
        "retrieve_then_read": "Retrieved Evidence",
        "no_evidence": "No Evidence",
        "oracle": "Oracle Evidence",
    }

    compact_table["Condition_Display"] = compact_table["Condition"].map(condition_map)
    contextual["Condition_Display"] = contextual["Condition"].map(condition_map)

    order_cols = [
        "Model",
        "Dataset",
        "Condition_Display",
        "N",
        "Loc.",
        "Sel.",
        "Int.",
        "Conv.",
        "Succ.",
        "Parse",
        "Other",
    ]

    compact_table = compact_table[order_cols]
    contextual = contextual[order_cols]

    long_table.to_csv(outdir / "sci200_failure_breakdown_long.csv", index=False)
    compact_table.to_csv(outdir / "sci200_failure_breakdown_compact_all_conditions.csv", index=False)
    contextual.to_csv(outdir / "sci200_failure_breakdown_contextual_compact.csv", index=False)
    raw_values_table.to_csv(outdir / "sci200_failure_raw_values.csv", index=False)

    with open(outdir / "sci200_failure_breakdown_contextual_compact.tex", "w", encoding="utf-8") as f:
        f.write(contextual.to_latex(index=False, float_format="%.1f", escape=False))

    with open(outdir / "sci200_failure_breakdown_compact_all_conditions.tex", "w", encoding="utf-8") as f:
        f.write(compact_table.to_latex(index=False, float_format="%.1f", escape=False))

    print("\n=== Raw failure_type values by run ===")
    print(raw_values_table.to_string(index=False))

    print("\n=== Final SCI-200 Failure Breakdown: Contextual Conditions ===")
    print(contextual.round(1).to_string(index=False))

    print(f"\nWrote failure analysis files to: {outdir}")


if __name__ == "__main__":
    main()
