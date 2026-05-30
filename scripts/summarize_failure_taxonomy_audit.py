#!/usr/bin/env python3
"""Summarize two-annotator failure-taxonomy validation.

This script computes inter-annotator agreement, Cohen's kappa, an annotator
confusion matrix, and rule-vs-human agreement for the blind audit files exported
by export_failure_taxonomy_audit.py.

Typical use after both annotators fill their CSVs:
    python scripts/summarize_failure_taxonomy_audit.py

If an adjudicated file is available, pass:
    --adjudicated experiment_backups/.../failure_taxonomy_adjudicated.csv

The adjudicated file should contain audit_id and adjudicated_label. Without an
adjudicated file, rule-vs-human agreement is computed on consensus-only items,
and disagreements are exported for adjudication.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

LABELS = [
    "localization",
    "selection",
    "integration",
    "conversion",
    "parse_format",
    "ambiguous",
]

LABEL_ALIASES = {
    "localization": "localization",
    "evidence_localization_failure": "localization",
    "selection": "selection",
    "evidence_selection_failure": "selection",
    "integration": "integration",
    "evidence_integration_failure": "integration",
    "conversion": "conversion",
    "answer_conversion_failure": "conversion",
    "parse": "parse_format",
    "parse_failure": "parse_format",
    "format": "parse_format",
    "parse_format": "parse_format",
    "parse_or_format": "parse_format",
    "parse-format": "parse_format",
    "ambiguous": "ambiguous",
    "unclear": "ambiguous",
    "mixed": "ambiguous",
}


def _norm_label(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    raw = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    return LABEL_ALIASES.get(raw, raw)


def _find_label_col(df: pd.DataFrame, preferred: list[str]) -> str:
    for col in preferred:
        if col in df.columns:
            return col
    candidates = [c for c in df.columns if "label" in c.lower() and "rule" not in c.lower()]
    if candidates:
        return candidates[-1]
    raise ValueError(f"Could not find a human-label column. Available columns: {list(df.columns)}")


def _cohen_kappa(a: list[str], b: list[str], labels: list[str]) -> float:
    if len(a) != len(b):
        raise ValueError("Label vectors must have the same length.")
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pa = {lab: a.count(lab) / n for lab in labels}
    pb = {lab: b.count(lab) / n for lab in labels}
    pe = sum(pa[lab] * pb[lab] for lab in labels)
    if abs(1.0 - pe) < 1e-12:
        return 1.0 if abs(po - 1.0) < 1e-12 else 0.0
    return (po - pe) / (1.0 - pe)


def _raw_agreement(a: list[str], b: list[str]) -> float:
    if not a:
        return float("nan")
    return sum(x == y for x, y in zip(a, b)) / len(a)


def _confusion(a: list[str], b: list[str], labels: list[str]) -> pd.DataFrame:
    return pd.crosstab(
        pd.Categorical(a, categories=labels),
        pd.Categorical(b, categories=labels),
        rownames=["annotator_a"],
        colnames=["annotator_b"],
        dropna=False,
    )


def _write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=True if df.index.name or not isinstance(df.index, pd.RangeIndex) else False, quoting=csv.QUOTE_MINIMAL)


def _format_float(x: float) -> str:
    if pd.isna(x):
        return "--"
    return f"{x:.3f}"


def _latex_escape(text: Any) -> str:
    s = str(text)
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for k, v in repl.items():
        s = s.replace(k, v)
    return s


def _write_agreement_table(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        r"\begin{table}[!t]",
        r"\renewcommand{\arraystretch}{1.10}",
        r"\caption{Human Validation of Failure-Type Assignment. Agreement is computed on the blind two-annotator audit sample. Rule-vs-human agreement is computed against adjudicated labels when available, otherwise against annotator-consensus items only.}",
        r"\label{tab:failure_taxonomy_human_validation}",
        r"\centering",
        r"\footnotesize",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Quantity & Value & Items \\",
        r"\midrule",
        f"Annotator raw agreement & {_format_float(summary['annotator_raw_agreement'])} & {summary['n_annotated']} \\",
        f"Cohen's $\\kappa$ & {_format_float(summary['cohen_kappa'])} & {summary['n_annotated']} \\",
        f"Consensus items & {_format_float(summary['consensus_rate'])} & {summary['n_consensus']} \\",
        f"Rule-vs-human raw agreement & {_format_float(summary['rule_vs_human_raw_agreement'])} & {summary['n_rule_vs_human']} \\",
        f"Rule-vs-human Cohen's $\\kappa$ & {_format_float(summary['rule_vs_human_kappa'])} & {summary['n_rule_vs_human']} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _load_adjudicated(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    if "audit_id" not in df.columns:
        raise ValueError("Adjudicated file must contain audit_id.")
    col = _find_label_col(df, ["adjudicated_label", "final_label", "human_label"])
    out = df[["audit_id", col]].copy()
    out = out.rename(columns={col: "adjudicated_label"})
    out["adjudicated_label"] = out["adjudicated_label"].map(_norm_label)
    return out


def summarize(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    out_dir = (root / args.output_dir).resolve()
    key_path = out_dir / "failure_taxonomy_audit_sample_key.csv"
    ann_a_path = out_dir / "failure_taxonomy_annotator_a.csv"
    ann_b_path = out_dir / "failure_taxonomy_annotator_b.csv"

    if not key_path.exists():
        raise FileNotFoundError(f"Missing key file: {key_path}")
    if not ann_a_path.exists() or not ann_b_path.exists():
        raise FileNotFoundError("Missing annotator CSVs. Run export script first and fill both annotation files.")

    key = pd.read_csv(key_path)
    ann_a = pd.read_csv(ann_a_path)
    ann_b = pd.read_csv(ann_b_path)

    col_a = _find_label_col(ann_a, ["human_label_annotator_a", "human_label"])
    col_b = _find_label_col(ann_b, ["human_label_annotator_b", "human_label"])

    merged = key[["audit_id", "rule_failure_label", "dataset", "model_name", "condition", "sample_id"]].merge(
        ann_a[["audit_id", col_a]], on="audit_id", how="left"
    ).merge(ann_b[["audit_id", col_b]], on="audit_id", how="left")
    merged = merged.rename(columns={col_a: "annotator_a_label", col_b: "annotator_b_label"})
    merged["annotator_a_label"] = merged["annotator_a_label"].map(_norm_label)
    merged["annotator_b_label"] = merged["annotator_b_label"].map(_norm_label)
    merged["rule_failure_label"] = merged["rule_failure_label"].map(_norm_label)

    valid = merged[
        merged["annotator_a_label"].isin(LABELS) & merged["annotator_b_label"].isin(LABELS)
    ].copy()
    if valid.empty:
        raise RuntimeError("No completed annotation rows found. Fill human_label columns before summarizing.")

    a = valid["annotator_a_label"].tolist()
    b = valid["annotator_b_label"].tolist()
    raw = _raw_agreement(a, b)
    kappa = _cohen_kappa(a, b, LABELS)
    valid["consensus_label"] = [x if x == y else "needs_adjudication" for x, y in zip(a, b)]

    disagreements = valid[valid["consensus_label"] == "needs_adjudication"].copy()
    disagreements_path = out_dir / "failure_taxonomy_disagreements_for_adjudication.csv"
    # Include full annotation context for adjudication by merging back to blind fields.
    blind = pd.read_csv(out_dir / "failure_taxonomy_audit_sample_blind.csv")
    # Keep adjudication blind to the rule label. The rule label remains only in
    # failure_taxonomy_audit_sample_key.csv for post-adjudication analysis.
    disagreements_full = blind.merge(
        disagreements[["audit_id", "annotator_a_label", "annotator_b_label"]],
        on="audit_id",
        how="inner",
    )
    disagreements_full["adjudicated_label"] = ""
    disagreements_full["adjudication_notes"] = ""
    disagreements_full.to_csv(disagreements_path, index=False)

    adjudicated = _load_adjudicated(Path(args.adjudicated).resolve() if args.adjudicated else None)
    if adjudicated is not None:
        valid = valid.merge(adjudicated, on="audit_id", how="left")
        human_col = "adjudicated_label"
        rule_eval = valid[valid[human_col].isin(LABELS)].copy()
    else:
        human_col = "consensus_label"
        rule_eval = valid[valid[human_col].isin(LABELS)].copy()

    if not rule_eval.empty:
        rule_labels = rule_eval["rule_failure_label"].tolist()
        human_labels = rule_eval[human_col].tolist()
        rule_raw = _raw_agreement(rule_labels, human_labels)
        rule_kappa = _cohen_kappa(rule_labels, human_labels, LABELS)
        rule_confusion = pd.crosstab(
            pd.Categorical(rule_labels, categories=LABELS),
            pd.Categorical(human_labels, categories=LABELS),
            rownames=["rule_label"],
            colnames=["human_label"],
            dropna=False,
        )
    else:
        rule_raw = float("nan")
        rule_kappa = float("nan")
        rule_confusion = pd.DataFrame(index=LABELS, columns=LABELS).fillna(0)

    conf = _confusion(a, b, LABELS)
    _write_csv(out_dir / "failure_taxonomy_annotator_confusion_matrix.csv", conf)
    _write_csv(out_dir / "failure_taxonomy_rule_vs_human_confusion_matrix.csv", rule_confusion)
    _write_csv(out_dir / "failure_taxonomy_completed_annotations.csv", valid)

    summary = {
        "n_exported": int(len(key)),
        "n_annotated": int(len(valid)),
        "annotator_raw_agreement": float(raw),
        "cohen_kappa": float(kappa),
        "n_disagreements": int(len(disagreements)),
        "n_consensus": int((valid["consensus_label"] != "needs_adjudication").sum()),
        "consensus_rate": float((valid["consensus_label"] != "needs_adjudication").mean()),
        "rule_vs_human_basis": "adjudicated" if adjudicated is not None else "consensus_only",
        "n_rule_vs_human": int(len(rule_eval)),
        "rule_vs_human_raw_agreement": float(rule_raw),
        "rule_vs_human_kappa": float(rule_kappa),
    }
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(out_dir / "failure_taxonomy_agreement_summary.csv", index=False)
    _write_agreement_table(out_dir / "failure_taxonomy_agreement_table.tex", summary)

    manifest = {
        "task": "failure_taxonomy_human_validation_summary",
        "labels": LABELS,
        "summary": summary,
        "outputs": [
            "failure_taxonomy_agreement_summary.csv",
            "failure_taxonomy_annotator_confusion_matrix.csv",
            "failure_taxonomy_rule_vs_human_confusion_matrix.csv",
            "failure_taxonomy_completed_annotations.csv",
            "failure_taxonomy_disagreements_for_adjudication.csv",
            "failure_taxonomy_agreement_table.tex",
        ],
    }
    (out_dir / "failure_taxonomy_summary_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Wrote failure-taxonomy agreement summaries to {out_dir}")
    print(f"annotated rows: {summary['n_annotated']} / {summary['n_exported']}")
    print(f"annotator raw agreement: {summary['annotator_raw_agreement']:.3f}")
    print(f"Cohen's kappa: {summary['cohen_kappa']:.3f}")
    print(f"disagreements needing adjudication: {summary['n_disagreements']}")
    print(f"rule-vs-human basis: {summary['rule_vs_human_basis']}")


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument(
        "--output-dir",
        default="experiment_backups/failure_taxonomy_human_validation_20260530",
        help="Audit output directory relative to repo root.",
    )
    parser.add_argument(
        "--adjudicated",
        default="",
        help="Optional adjudicated CSV containing audit_id and adjudicated_label.",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    summarize(args)


if __name__ == "__main__":
    main()
