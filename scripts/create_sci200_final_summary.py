import pandas as pd
from pathlib import Path

runs = {
    ("Qwen2.5-14B", "Controlled-safe16K-200"): "controlled_safe16k_qwen25_14b_200_core_final",
    ("Qwen2.5-14B", "HotpotQA-ONCU-200"): "hotpotqa_qwen25_14b_200_core_final",
    ("Qwen3-14B", "Controlled-safe16K-200"): "controlled_safe16k_qwen3_14b_200_core_final",
    ("Qwen3-14B", "HotpotQA-ONCU-200"): "hotpotqa_qwen3_14b_200_core_final",
    ("Gemma3-12B", "Controlled-safe16K-200"): "controlled_safe16k_gemma3_12b_200_core_final",
    ("Gemma3-12B", "HotpotQA-ONCU-200"): "hotpotqa_gemma3_12b_200_core_final",
}

outdir = Path("experiment_backups/sci200_final_3model_20260525/summary")
outdir.mkdir(parents=True, exist_ok=True)

answer_rows = []
oncu_rows = []

for (model, dataset), run in runs.items():
    metrics = pd.read_csv(f"outputs/{run}/results/per_sample_metrics.csv")

    for method in ["no_evidence", "direct", "retrieve_then_read", "oracle"]:
        sub = metrics[metrics["method"] == method]
        answer_rows.append({
            "Model": model,
            "Dataset": dataset,
            "Condition": method,
            "N": len(sub),
            "Parse_Errors": int(sub["parse_error"].notna().sum()),
            "Strict_F1": sub["answer_f1_strict"].mean(),
            "Relaxed_F1": sub["answer_f1_relaxed"].mean(),
            "Relaxed_EM": sub["exact_match_relaxed"].mean(),
            "Evidence_F1": sub["evidence_f1"].mean(),
        })

    oncu = pd.read_csv(f"outputs/{run}/results/oncu_metrics_multiscore_summary.csv")
    oncu = oncu[oncu["score_field"] == "answer_f1_relaxed"]

    for _, r in oncu.iterrows():
        oncu_rows.append({
            "Model": model,
            "Dataset": dataset,
            "Condition": r["long_method"],
            "Valid_Groups": int(r["valid_groups"]),
            "S_no": r["score_no_evidence_mean"],
            "S_oracle": r["score_oracle_mean"],
            "S_condition": r["score_long_mean"],
            "ONCU_Relaxed_F1": r["oncu_clipped_mean"],
        })

answer_table = pd.DataFrame(answer_rows)
oncu_table = pd.DataFrame(oncu_rows)

answer_table.to_csv(outdir / "sci200_answer_evidence_summary.csv", index=False)
oncu_table.to_csv(outdir / "sci200_oncu_relaxed_f1_summary.csv", index=False)

with open(outdir / "sci200_answer_evidence_summary.tex", "w", encoding="utf-8") as f:
    f.write(answer_table.to_latex(index=False, float_format="%.3f", escape=False))

with open(outdir / "sci200_oncu_relaxed_f1_summary.tex", "w", encoding="utf-8") as f:
    f.write(oncu_table.to_latex(index=False, float_format="%.3f", escape=False))

print("Wrote final SCI-200 summary to", outdir)
print(answer_table.round(3).to_string(index=False))
print()
print(oncu_table.round(3).to_string(index=False))
