#!/usr/bin/env python3
"""Summarize RULER-lite external validation outputs.

Reads:
    outputs/ruler_lite_external/per_sample_metrics.csv

Writes:
    experiment_backups/ruler_lite_external_YYYYMMDD/
        ruler_lite_condition_summary.csv
        ruler_lite_model_summary.csv
        ruler_lite_length_task_summary.csv
        ruler_lite_external_validation_table.tex
        ruler_lite_external_manifest.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def _fmt(x: float) -> str:
    if pd.isna(x):
        return "--"
    return f"{float(x):.3f}"


def _escape_latex(text: object) -> str:
    s = str(text)
    return (
        s.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
    )


def write_external_table(df: pd.DataFrame, output: Path) -> None:
    model_summary = (
        df.groupby(["model_name", "condition"], as_index=False)
        .agg(
            n=("sample_id", "count"),
            exact_match=("exact_match", "mean"),
            answer_f1=("answer_f1", "mean"),
            parse_failure_rate=("parse_failure", "mean"),
        )
        .sort_values(["model_name", "condition"])
    )

    lines = []
    lines.append(r"\begin{table*}[!t]")
    lines.append(r"\renewcommand{\arraystretch}{1.10}")
    lines.append(r"\caption{RULER-lite External Answer-Performance Validation. This out-of-protocol validation reports answer performance only and is not used for ONCU computation because the setting is not constructed with the four-condition oracle-normalized protocol.}")
    lines.append(r"\label{tab:ruler_lite_external_validation}")
    lines.append(r"\centering")
    lines.append(r"\scriptsize")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\begin{tabular}{llrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Model & Condition & $n$ & Exact Match & Answer F1 & Parse Fail. \\")
    lines.append(r"\midrule")

    for _, row in model_summary.iterrows():
        lines.append(
            f"{_escape_latex(row['model_name'])} & "
            f"{_escape_latex(row['condition'])} & "
            f"{int(row['n'])} & "
            f"{_fmt(row['exact_match'])} & "
            f"{_fmt(row['answer_f1'])} & "
            f"{_fmt(row['parse_failure_rate'])} \\\\"
        )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table*}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=Path("outputs/ruler_lite_external"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Default: experiment_backups/ruler_lite_external_<YYYYMMDD>",
    )
    args = parser.parse_args()

    metrics_path = args.run_dir / "per_sample_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics file: {metrics_path}")

    output_dir = args.output_dir or Path(f"experiment_backups/ruler_lite_external_{datetime.utcnow().strftime('%Y%m%d')}")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(metrics_path)
    condition_summary = (
        df.groupby(["model_name", "condition", "task_name", "context_length"], as_index=False)
        .agg(
            n=("sample_id", "count"),
            exact_match=("exact_match", "mean"),
            answer_f1=("answer_f1", "mean"),
            parse_failure_rate=("parse_failure", "mean"),
        )
        .sort_values(["model_name", "condition", "task_name", "context_length"])
    )
    model_summary = (
        df.groupby(["model_name", "condition"], as_index=False)
        .agg(
            n=("sample_id", "count"),
            exact_match=("exact_match", "mean"),
            answer_f1=("answer_f1", "mean"),
            parse_failure_rate=("parse_failure", "mean"),
        )
        .sort_values(["model_name", "condition"])
    )
    length_task_summary = (
        df.groupby(["condition", "task_name", "context_length"], as_index=False)
        .agg(
            n=("sample_id", "count"),
            exact_match=("exact_match", "mean"),
            answer_f1=("answer_f1", "mean"),
            parse_failure_rate=("parse_failure", "mean"),
        )
        .sort_values(["condition", "task_name", "context_length"])
    )

    condition_summary.to_csv(output_dir / "ruler_lite_condition_summary.csv", index=False)
    model_summary.to_csv(output_dir / "ruler_lite_model_summary.csv", index=False)
    length_task_summary.to_csv(output_dir / "ruler_lite_length_task_summary.csv", index=False)
    write_external_table(df, output_dir / "ruler_lite_external_validation_table.tex")

    manifest = {
        "run_dir": str(args.run_dir),
        "metrics_path": str(metrics_path),
        "output_dir": str(output_dir),
        "num_rows": int(len(df)),
        "models": sorted(map(str, df["model_name"].unique())),
        "conditions": sorted(map(str, df["condition"].unique())),
        "tasks": sorted(map(str, df["task_name"].unique())),
        "context_lengths": sorted(map(int, df["context_length"].unique())),
        "role": "External answer-performance validation; not ONCU.",
    }
    (output_dir / "ruler_lite_external_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote RULER-lite summaries to {output_dir}")
    print(f"condition rows: {len(condition_summary)}")
    print(f"model rows: {len(model_summary)}")
    print(f"length-task rows: {len(length_task_summary)}")


if __name__ == "__main__":
    main()
