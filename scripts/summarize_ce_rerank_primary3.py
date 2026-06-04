from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path("outputs/rerank_sensitivity_20260602/ce_reader_facing")
OUT = Path("experiment_backups/rerank_sensitivity_20260602/primary3_ce_rerank_summary")
OUT.mkdir(parents=True, exist_ok=True)

MODELS = {
    "qwen25": "Qwen2.5-14B",
    "qwen3": "Qwen3-14B",
    "gemma3": "Gemma3-12B",
}

DATASETS = {
    "hotpotqa200": "HotpotQA-200",
    "twowiki500": "2Wiki-500",
}

rows = []

for run_dir in sorted(ROOT.glob("*")):
    if not run_dir.is_dir():
        continue

    name = run_dir.name
    parts = name.split("_")
    if len(parts) < 5:
        continue

    dataset_key = parts[0]
    model_key = parts[1]

    if dataset_key not in DATASETS or model_key not in MODELS:
        continue

    if model_key not in MODELS:
        continue

    cond_path = run_dir / "reader_condition_summary.csv"
    oncu_path = run_dir / "reader_oncu_summary.csv"
    if not cond_path.exists() or not oncu_path.exists():
        continue

    cdf = pd.read_csv(cond_path)
    odf = pd.read_csv(oncu_path)
    if cdf.empty or odf.empty:
        continue

    c = cdf.iloc[0]
    o = odf.iloc[0]

    retriever = str(c["retriever"])
    top_k = int(c["top_k"])
    candidate_k = retriever.replace("hybrid_ce", "")
    setting = f"CE@{candidate_k}$\\rightarrow${top_k}"

    rows.append({
        "dataset_key": dataset_key,
        "dataset": DATASETS[dataset_key],
        "model_key": model_key,
        "model": MODELS[model_key],
        "setting": setting,
        "answer_f1": float(c["answer_f1_relaxed"]),
        "evidence_f1": float(c["evidence_f1"]),
        "valid_groups": int(o["valid_groups"]),
        "total_groups": int(o["total_groups"]),
        "oncu": float(o["oncu_relaxed_f1"]),
        "parse_errors": int(c["parse_errors"]),
    })

df = pd.DataFrame(rows)
df = df[df["model_key"].isin(["qwen25", "qwen3", "gemma3"])].copy()

df.to_csv(OUT / "primary3_ce_rerank_all_rows.csv", index=False)

# Best rows by answer F1, one row per dataset-model.
idx = df.groupby(["dataset_key", "model_key"])["answer_f1"].idxmax()
best_answer = df.loc[idx].copy()
best_answer = best_answer.sort_values(["dataset_key", "model_key"])
best_answer.to_csv(OUT / "primary3_ce_rerank_best_answer_rows.csv", index=False)

# Also best by ONCU for audit.
idx_oncu = df.groupby(["dataset_key", "model_key"])["oncu"].idxmax()
best_oncu = df.loc[idx_oncu].copy()
best_oncu = best_oncu.sort_values(["dataset_key", "model_key"])
best_oncu.to_csv(OUT / "primary3_ce_rerank_best_oncu_rows.csv", index=False)

def fmt(x: float) -> str:
    return f"{x:.3f}"

lines = []
lines.append(r"\begin{table*}[!t]")
lines.append(r"\renewcommand{\arraystretch}{1.08}")
lines.append(r"\caption{Primary Three-Model Cross-Encoder Reranking Audit. CE@$m\rightarrow k$ denotes hybrid first-stage retrieval with $m$ candidates, cross-encoder reranking, and final reader budget $k$. The table reports the best answer-F1 reranked setting for each model--dataset pair; ONCU is computed by joining each reranked retrieved prediction with the corresponding no-evidence and oracle-evidence references by sample identifier.}")
lines.append(r"\label{tab:primary3_ce_rerank_audit}")
lines.append(r"\centering")
lines.append(r"\scriptsize")
lines.append(r"\setlength{\tabcolsep}{3pt}")
lines.append(r"\begin{tabular}{lllrrrrr}")
lines.append(r"\toprule")
lines.append(r"Dataset & Model & Best reranked setting & Answer F1 & Evidence F1 & Valid denom. & ONCU & Parse err. \\")
lines.append(r"\midrule")

for _, r in best_answer.iterrows():
    lines.append(
        f"{r['dataset']} & {r['model']} & {r['setting']} & "
        f"{fmt(r['answer_f1'])} & {fmt(r['evidence_f1'])} & "
        f"{int(r['valid_groups'])}/{int(r['total_groups'])} & {fmt(r['oncu'])} & {int(r['parse_errors'])} \\\\"
    )

lines.append(r"\bottomrule")
lines.append(r"\end{tabular}")
lines.append(r"\end{table*}")

(OUT / "primary3_ce_rerank_best_answer_table.tex").write_text("\n".join(lines) + "\n")

print("Wrote:", OUT)
print("\nBest answer rows:")
print(best_answer.to_string(index=False))
print("\nBest ONCU rows:")
print(best_oncu.to_string(index=False))
