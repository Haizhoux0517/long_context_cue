import pandas as pd
from pathlib import Path

runs = {
    ("Qwen2.5-14B", "Controlled-safe16K"): "controlled_safe16k_qwen25_14b_100_core",
    ("Qwen2.5-14B", "HotpotQA-ONCU-100"): "hotpotqa_qwen25_14b_100_core",
    ("Qwen3-14B", "Controlled-safe16K"): "controlled_safe16k_qwen3_14b_100_core",
    ("Qwen3-14B", "HotpotQA-ONCU-100"): "hotpotqa_qwen3_14b_100_core",
}

backup = Path("experiment_backups/core_2x2_qwen25_qwen3_20260524")
summary_dir = backup / "summary"
summary_dir.mkdir(parents=True, exist_ok=True)

answer_rows = []

for (model, dataset), run in runs.items():
    metrics_path = Path(f"outputs/{run}/results/per_sample_metrics.csv")
    if not metrics_path.exists():
        raise FileNotFoundError(metrics_path)

    metrics = pd.read_csv(metrics_path)

    for method in ["no_evidence", "direct", "retrieve_then_read", "oracle"]:
        sub = metrics[metrics["method"] == method]
        answer_rows.append({
            "Model": model,
            "Dataset": dataset,
            "Condition": method,
            "N": len(sub),
            "Parse Errors": int(sub["parse_error"].notna().sum()),
            "Strict F1": sub["answer_f1_strict"].mean(),
            "Relaxed F1": sub["answer_f1_relaxed"].mean(),
            "Relaxed EM": sub["exact_match_relaxed"].mean(),
            "Evidence F1": sub["evidence_f1"].mean(),
        })

answer_table = pd.DataFrame(answer_rows)
answer_table.to_csv(summary_dir / "core_2x2_answer_evidence_summary.csv", index=False)

oncu_rows = []

for (model, dataset), run in runs.items():
    oncu_path = Path(f"outputs/{run}/results/oncu_metrics_multiscore_summary.csv")
    if not oncu_path.exists():
        raise FileNotFoundError(oncu_path)

    oncu = pd.read_csv(oncu_path)
    oncu = oncu[oncu["score_field"] == "answer_f1_relaxed"]

    for _, r in oncu.iterrows():
        oncu_rows.append({
            "Model": model,
            "Dataset": dataset,
            "Condition": r["long_method"],
            "Valid Groups": int(r["valid_groups"]),
            "S_no": r["score_no_evidence_mean"],
            "S_oracle": r["score_oracle_mean"],
            "S_condition": r["score_long_mean"],
            "ONCU_Relaxed_F1": r["oncu_clipped_mean"],
        })

oncu_table = pd.DataFrame(oncu_rows)
oncu_table.to_csv(summary_dir / "core_2x2_oncu_relaxed_f1_summary.csv", index=False)

with open(summary_dir / "core_2x2_answer_evidence_summary.tex", "w", encoding="utf-8") as f:
    f.write(answer_table.to_latex(index=False, float_format="%.3f", escape=False))

with open(summary_dir / "core_2x2_oncu_relaxed_f1_summary.tex", "w", encoding="utf-8") as f:
    f.write(oncu_table.to_latex(index=False, float_format="%.3f", escape=False))

print("Wrote summary files to:", summary_dir)
print("\nAnswer / Evidence Summary:")
print(answer_table.round(3).to_string(index=False))
print("\nONCU Summary:")
print(oncu_table.round(3).to_string(index=False))
