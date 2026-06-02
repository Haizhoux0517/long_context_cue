#!/usr/bin/env python3
"""Build metric-comparison summaries for the ONCU diagnostic paper.

The goal of this script is not to introduce another evaluation metric. It
materializes reviewer-facing tables that compare what common scores can and
cannot diagnose:

* raw answer F1 / exact match
* evidence F1
* context gain over the no-evidence baseline
* oracle gap relative to the oracle-evidence reference
* ONCU, which normalizes by both the no-evidence baseline and the oracle ceiling
* retrieval-only recall/coverage measures for retriever-family ablations

The script reads only frozen release artifacts and writes CSV + LaTeX tables.
It does not inspect raw model outputs, rerun models, or alter any experiment
results.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

DEFAULT_OUTPUT_DIR = Path("experiment_backups/metric_comparison_20260530")

CORE_ANSWER_PATH = Path("experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv")
CORE_ONCU_PATH = Path("experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv")
TWOWIKI_CONDITION_PATH = Path("experiment_backups/twowiki_500_validation_20260527/summary/twowiki_condition_summary.csv")
TWOWIKI_ONCU_PATH = Path("experiment_backups/twowiki_500_validation_20260527/summary/twowiki_oncu_relaxed_f1_summary.csv")
SCALING_ONCU_PATH = Path("experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_oncu_by_length_position.csv")
RETRIEVER_HOTPOT_PATH = Path("experiment_backups/retriever_family_ablation_20260527/hotpotqa/retrieval_only_summary.csv")
RETRIEVER_TWOWIKI_PATH = Path("experiment_backups/retriever_family_ablation_20260527/twowiki/retrieval_only_summary.csv")

CONTEXTUAL_METHODS = {"direct", "retrieve_then_read"}
METHOD_DISPLAY = {
    "direct": "Full context",
    "retrieve_then_read": "Retrieved evidence",
    "no_evidence": "No evidence",
    "oracle": "Oracle evidence",
}


@dataclass(frozen=True)
class ScriptManifest:
    output_dir: str
    generated_files: list[str]
    source_files: list[str]
    core_rows: int
    controlled_scaling_rows: int
    retrieval_rows: int
    case_study_rows: int


def _require_file(root: Path, relative: Path) -> Path:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"Required artifact not found: {relative}")
    return path


def _read_csv(root: Path, relative: Path) -> pd.DataFrame:
    return pd.read_csv(_require_file(root, relative))


def _round_float(value: object, digits: int = 3) -> object:
    if value is None:
        return value
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value
    if math.isnan(numeric):
        return value
    return round(numeric, digits)


def _format_float(value: object, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "--"
    if math.isnan(numeric):
        return "--"
    return f"{numeric:.{digits}f}"


def _escape_latex(text: object) -> str:
    s = str(text)
    replacements = {
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
    return "".join(replacements.get(ch, ch) for ch in s)


def _diagnostic_label(dataset: str, method: str, oncu: float | None, context_gain: float | None, oracle_gap: float | None) -> str:
    if method == "retrieve_then_read" and oncu is not None and oncu >= 0.9:
        return "Compact evidence recovers most oracle advantage."
    if method == "retrieve_then_read" and oncu is not None and oncu < 0.5:
        return "Retrieved evidence loses recoverable advantage."
    if method == "direct" and "Controlled" in dataset and oncu is not None and oncu < 0.65:
        return "Full-context condition under-recovers oracle advantage."
    if method == "direct" and "Hotpot" in dataset and oncu is not None and oncu >= 0.7:
        return "Full context preserves multi-hop evidence better than retrieval."
    if method == "direct" and "2Wiki" in dataset and oncu is not None and oncu < 0.65:
        return "Realistic multi-hop utilization remains incomplete."
    if oracle_gap is not None and oracle_gap > 0.2:
        return "Large oracle gap remains after the condition."
    if context_gain is not None and context_gain > 0.2:
        return "Condition improves substantially over no-evidence baseline."
    return "Report with raw answer and evidence metrics."


def _build_condition_metric_comparison(root: Path) -> pd.DataFrame:
    """Build condition-level comparisons for core-200 and 2Wiki-500 artifacts."""
    rows: list[dict[str, object]] = []

    # Core 200-sample matrix.
    answer = _read_csv(root, CORE_ANSWER_PATH)
    oncu = _read_csv(root, CORE_ONCU_PATH)
    for _, row in answer[answer["Condition"].isin(CONTEXTUAL_METHODS)].iterrows():
        model = row["Model"]
        dataset = row["Dataset"]
        method = row["Condition"]
        group = answer[(answer["Model"] == model) & (answer["Dataset"] == dataset)]
        no_rows = group[group["Condition"] == "no_evidence"]
        oracle_rows = group[group["Condition"] == "oracle"]
        if no_rows.empty or oracle_rows.empty:
            continue
        no_f1 = float(no_rows.iloc[0]["Relaxed_F1"])
        oracle_f1 = float(oracle_rows.iloc[0]["Relaxed_F1"])
        raw_f1 = float(row["Relaxed_F1"])
        oncu_match = oncu[(oncu["Model"] == model) & (oncu["Dataset"] == dataset) & (oncu["Condition"] == method)]
        oncu_value = float(oncu_match.iloc[0]["ONCU_Relaxed_F1"]) if not oncu_match.empty else math.nan
        s_condition = float(oncu_match.iloc[0]["S_condition"]) if not oncu_match.empty else math.nan
        s_no = float(oncu_match.iloc[0]["S_no"]) if not oncu_match.empty else math.nan
        s_oracle = float(oncu_match.iloc[0]["S_oracle"]) if not oncu_match.empty else math.nan
        valid_groups = int(oncu_match.iloc[0]["Valid_Groups"]) if not oncu_match.empty else None
        context_gain = raw_f1 - no_f1
        oracle_gap = oracle_f1 - raw_f1
        group_context_gain = s_condition - s_no if not math.isnan(s_condition) and not math.isnan(s_no) else math.nan
        group_oracle_gap = s_oracle - s_condition if not math.isnan(s_oracle) and not math.isnan(s_condition) else math.nan
        rows.append(
            {
                "component": "core200",
                "dataset": dataset,
                "model": model,
                "method": method,
                "condition_display": METHOD_DISPLAY.get(method, method),
                "n": int(row["N"]),
                "parse_errors": int(row["Parse_Errors"]),
                "answer_f1_relaxed_example": raw_f1,
                "evidence_f1_example": float(row["Evidence_F1"]),
                "no_evidence_f1_example": no_f1,
                "oracle_f1_example": oracle_f1,
                "context_gain_example": context_gain,
                "oracle_gap_example": oracle_gap,
                "valid_groups": valid_groups,
                "S_no_group": s_no,
                "S_oracle_group": s_oracle,
                "S_condition_group": s_condition,
                "context_gain_group": group_context_gain,
                "oracle_gap_group": group_oracle_gap,
                "oncu_clipped": oncu_value,
                "diagnostic_reading": _diagnostic_label(dataset, method, oncu_value, context_gain, oracle_gap),
            }
        )

    # 2WikiMultiHopQA 500-sample validation.
    condition = _read_csv(root, TWOWIKI_CONDITION_PATH)
    tw_oncu = _read_csv(root, TWOWIKI_ONCU_PATH)
    for _, row in condition[condition["method"].isin(CONTEXTUAL_METHODS)].iterrows():
        model = row["model_display"]
        method = row["method"]
        dataset = "2WikiMultiHopQA-ONCU-500"
        group = condition[condition["model_display"] == model]
        no_rows = group[group["method"] == "no_evidence"]
        oracle_rows = group[group["method"] == "oracle"]
        if no_rows.empty or oracle_rows.empty:
            continue
        no_f1 = float(no_rows.iloc[0]["answer_f1_relaxed"])
        oracle_f1 = float(oracle_rows.iloc[0]["answer_f1_relaxed"])
        raw_f1 = float(row["answer_f1_relaxed"])
        oncu_match = tw_oncu[(tw_oncu["model"] == model) & (tw_oncu["long_method"] == method)]
        oncu_value = float(oncu_match.iloc[0]["oncu_clipped"]) if not oncu_match.empty else math.nan
        s_condition = float(oncu_match.iloc[0]["S_long"]) if not oncu_match.empty else math.nan
        s_no = float(oncu_match.iloc[0]["S_no"]) if not oncu_match.empty else math.nan
        s_oracle = float(oncu_match.iloc[0]["S_oracle"]) if not oncu_match.empty else math.nan
        valid_groups = int(oncu_match.iloc[0]["valid_groups"]) if not oncu_match.empty else None
        context_gain = raw_f1 - no_f1
        oracle_gap = oracle_f1 - raw_f1
        group_context_gain = s_condition - s_no if not math.isnan(s_condition) and not math.isnan(s_no) else math.nan
        group_oracle_gap = s_oracle - s_condition if not math.isnan(s_oracle) and not math.isnan(s_condition) else math.nan
        rows.append(
            {
                "component": "twowiki500",
                "dataset": dataset,
                "model": model,
                "method": method,
                "condition_display": METHOD_DISPLAY.get(method, method),
                "n": int(row["n"]),
                "parse_errors": int(row["parse_errors"]),
                "answer_f1_relaxed_example": raw_f1,
                "evidence_f1_example": float(row["evidence_f1"]),
                "no_evidence_f1_example": no_f1,
                "oracle_f1_example": oracle_f1,
                "context_gain_example": context_gain,
                "oracle_gap_example": oracle_gap,
                "valid_groups": valid_groups,
                "S_no_group": s_no,
                "S_oracle_group": s_oracle,
                "S_condition_group": s_condition,
                "context_gain_group": group_context_gain,
                "oracle_gap_group": group_oracle_gap,
                "oncu_clipped": oncu_value,
                "diagnostic_reading": _diagnostic_label(dataset, method, oncu_value, context_gain, oracle_gap),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    ordered = [
        "component",
        "dataset",
        "model",
        "method",
        "condition_display",
        "n",
        "parse_errors",
        "answer_f1_relaxed_example",
        "evidence_f1_example",
        "no_evidence_f1_example",
        "oracle_f1_example",
        "context_gain_example",
        "oracle_gap_example",
        "valid_groups",
        "S_no_group",
        "S_oracle_group",
        "S_condition_group",
        "context_gain_group",
        "oracle_gap_group",
        "oncu_clipped",
        "diagnostic_reading",
    ]
    return df[ordered]


def _build_controlled_scaling_metric_comparison(root: Path) -> pd.DataFrame:
    scaling = _read_csv(root, SCALING_ONCU_PATH)
    scaling = scaling[scaling["long_method"].isin(CONTEXTUAL_METHODS)].copy()
    if scaling.empty:
        return scaling
    scaling["context_gain"] = scaling["score_long"] - scaling["score_no_evidence"]
    scaling["oracle_gap"] = scaling["score_oracle"] - scaling["score_long"]
    scaling["condition_display"] = scaling["long_method"].map(METHOD_DISPLAY).fillna(scaling["long_method"])
    scaling["diagnostic_reading"] = scaling.apply(
        lambda r: _diagnostic_label(
            "Controlled-scaling",
            str(r["long_method"]),
            float(r["oncu_clipped"]),
            float(r["context_gain"]),
            float(r["oracle_gap"]),
        ),
        axis=1,
    )
    ordered = [
        "model_name",
        "context_length",
        "evidence_position",
        "position_fraction",
        "long_method",
        "condition_display",
        "n",
        "score_no_evidence",
        "score_oracle",
        "score_long",
        "context_gain",
        "oracle_gap",
        "oncu_raw",
        "oncu_clipped",
        "oncu_valid",
        "diagnostic_reading",
    ]
    return scaling[ordered].sort_values(["model_name", "context_length", "evidence_position", "long_method"])


def _build_retrieval_metric_comparison(root: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source, path in [("hotpotqa", RETRIEVER_HOTPOT_PATH), ("twowiki", RETRIEVER_TWOWIKI_PATH)]:
        df = _read_csv(root, path).copy()
        df["component"] = source
        df["diagnostic_reading"] = df.apply(
            lambda r: (
                "Complete evidence chain is available to a reader."
                if float(r.get("full_chain_coverage", 0.0)) >= 0.8
                else "Retrieval may bottleneck multi-hop coverage."
            ),
            axis=1,
        )
        frames.append(df)
    retrieval = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if retrieval.empty:
        return retrieval
    ordered = [
        "component",
        "dataset_name",
        "retriever",
        "top_k",
        "n",
        "retrieval_precision",
        "retrieval_recall",
        "retrieval_f1",
        "oracle_hit_rate",
        "full_chain_coverage",
        "distractor_id_rate",
        "retrieved_passage_count",
        "diagnostic_reading",
    ]
    return retrieval[ordered].sort_values(["component", "retriever", "top_k"])


def _select_case_studies(condition_df: pd.DataFrame, scaling_df: pd.DataFrame, retrieval_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add_condition(component: str, dataset: str, model: str, method: str, label: str) -> None:
        match = condition_df[
            (condition_df["dataset"] == dataset)
            & (condition_df["model"] == model)
            & (condition_df["method"] == method)
        ]
        if match.empty:
            return
        r = match.iloc[0]
        rows.append(
            {
                "case": label,
                "metric_family": "reader_condition",
                "component": component,
                "dataset": dataset,
                "model_or_retriever": model,
                "condition_or_setting": r["condition_display"],
                "answer_f1_or_recall": r["answer_f1_relaxed_example"],
                "evidence_f1_or_chain_coverage": r["evidence_f1_example"],
                "context_gain": r["context_gain_example"],
                "oracle_gap": r["oracle_gap_example"],
                "oncu": r["oncu_clipped"],
                "diagnostic_reading": r["diagnostic_reading"],
            }
        )

    add_condition(
        "core200",
        "Controlled-safe16K-200",
        "Qwen3-14B",
        "direct",
        "Controlled full context: raw F1 hides oracle-normalized under-recovery",
    )
    add_condition(
        "core200",
        "Controlled-safe16K-200",
        "Qwen3-14B",
        "retrieve_then_read",
        "Controlled retrieved evidence: compact evidence recovers oracle advantage",
    )
    add_condition(
        "core200",
        "HotpotQA-ONCU-200",
        "Qwen2.5-14B",
        "direct",
        "HotpotQA full context: raw and ONCU agree that full context helps",
    )
    add_condition(
        "core200",
        "HotpotQA-ONCU-200",
        "Qwen2.5-14B",
        "retrieve_then_read",
        "HotpotQA retrieved evidence: retrieval coverage lowers ONCU",
    )
    add_condition(
        "twowiki500",
        "2WikiMultiHopQA-ONCU-500",
        "Qwen3-14B",
        "direct",
        "2Wiki full context: non-trivial raw F1 but moderate ONCU",
    )
    add_condition(
        "twowiki500",
        "2WikiMultiHopQA-ONCU-500",
        "Qwen3-14B",
        "retrieve_then_read",
        "2Wiki retrieved evidence: low ONCU despite compact input",
    )

    # Add 32K scaling examples to show that answer advantage depends on position.
    if not scaling_df.empty:
        for pos, label in [
            ("pos_00", "Controlled 32K early evidence: raw context gain and ONCU collapse"),
            ("pos_09", "Controlled 32K final-decile evidence: ONCU recovers at the end"),
        ]:
            match = scaling_df[
                (scaling_df["model_name"] == "qwen3:14b")
                & (scaling_df["context_length"] == 32000)
                & (scaling_df["evidence_position"] == pos)
                & (scaling_df["long_method"] == "direct")
            ]
            if match.empty:
                continue
            r = match.iloc[0]
            rows.append(
                {
                    "case": label,
                    "metric_family": "controlled_scaling_cell",
                    "component": "controlled_scaling",
                    "dataset": f"32K/{pos}",
                    "model_or_retriever": "Qwen3-14B",
                    "condition_or_setting": "Full context",
                    "answer_f1_or_recall": r["score_long"],
                    "evidence_f1_or_chain_coverage": math.nan,
                    "context_gain": r["context_gain"],
                    "oracle_gap": r["oracle_gap"],
                    "oncu": r["oncu_clipped"],
                    "diagnostic_reading": r["diagnostic_reading"],
                }
            )

    # Add retrieval-only examples for recall/chain coverage comparison.
    if not retrieval_df.empty:
        for component, retriever, top_k, label in [
            ("hotpotqa", "lexical", 3, "Retrieval-only HotpotQA lexical@3: recall before reading"),
            ("twowiki", "dense", 16, "Retrieval-only 2Wiki dense@16: coverage increases with budget"),
        ]:
            match = retrieval_df[
                (retrieval_df["component"] == component)
                & (retrieval_df["retriever"] == retriever)
                & (retrieval_df["top_k"] == top_k)
            ]
            if match.empty:
                continue
            r = match.iloc[0]
            rows.append(
                {
                    "case": label,
                    "metric_family": "retrieval_only",
                    "component": component,
                    "dataset": r["dataset_name"],
                    "model_or_retriever": retriever,
                    "condition_or_setting": f"top-k={top_k}",
                    "answer_f1_or_recall": r["retrieval_recall"],
                    "evidence_f1_or_chain_coverage": r["full_chain_coverage"],
                    "context_gain": math.nan,
                    "oracle_gap": math.nan,
                    "oncu": math.nan,
                    "diagnostic_reading": r["diagnostic_reading"],
                }
            )

    return pd.DataFrame(rows)


def _write_alternative_scores_latex(path: Path) -> None:
    rows = [
        (
            "Raw answer F1 / EM",
            "No",
            "No",
            "No",
            "Final answer correctness",
            "Can conflate context use with no-evidence priors or parametric knowledge.",
        ),
        (
            "Evidence F1",
            "No",
            "No",
            "Post-reader evidence overlap",
            "Cited evidence quality",
            "Can be high when the final answer is converted incorrectly.",
        ),
        (
            "Retrieval recall@$k$",
            "No",
            "No",
            "Pre-reader availability",
            "Retriever evidence coverage",
            "Does not measure whether the reader uses retrieved evidence.",
        ),
        (
            r"Oracle gap $S_{\\mathrm{oracle}}-S_c$",
            "No",
            "Partially",
            "Optional",
            "Distance from isolated-evidence reference",
            "Does not adjust for no-evidence answerability.",
        ),
        (
            r"Context gain $S_c-S_{\\mathrm{no}}$",
            "Yes",
            "No",
            "Optional",
            "Improvement over no-evidence baseline",
            "Does not indicate how much recoverable evidence advantage was captured.",
        ),
        (
            "ONCU raw",
            "Yes",
            "Yes",
            "Via chosen score field",
            "Recovered oracle-evidence advantage",
            "Requires a positive oracle-over-baseline denominator.",
        ),
        (
            "ONCU clipped",
            "Yes",
            "Yes",
            "Via chosen score field",
            "Aggregate recovered fraction",
            "Clips diagnostic extremes above 1 or below 0.",
        ),
    ]
    lines = [
        r"\begin{table*}[!t]",
        r"\renewcommand{\arraystretch}{1.08}",
        r"\caption{Comparison of ONCU with Alternative Diagnostic Scores.}",
        r"\label{tab:metric_comparison_alternatives}",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\begin{tabular}{lccclp{0.30\textwidth}}",
        r"\toprule",
        r"Metric & Baseline & Oracle & Evidence & Primary use & Main limitation \\",
        r"\midrule",
    ]
    for row in rows:
        metric, baseline, oracle, evidence, use, limitation = row
        lines.append(
            f"{metric} & {_escape_latex(baseline)} & {_escape_latex(oracle)} & {_escape_latex(evidence)} & "
            f"{_escape_latex(use)} & {_escape_latex(limitation)} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}"])
    path.write_text("\n".join(lines) + "\n")


def _write_case_study_latex(path: Path, cases: pd.DataFrame) -> None:
    lines = [
        r"\begin{table*}[!t]",
        r"\renewcommand{\arraystretch}{1.08}",
        r"\caption{Metric-Comparison Case Studies. Raw answer F1, evidence F1 or chain coverage, context gain, oracle gap, and ONCU answer different diagnostic questions.}",
        r"\label{tab:metric_comparison_case_studies}",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\begin{tabular}{p{0.25\textwidth}llrrrrp{0.28\textwidth}}",
        r"\toprule",
        r"Case & Model/Retriever & Setting & Ans./Recall & Ev./Coverage & Gain & Gap & ONCU & Diagnostic reading \\",
        r"\midrule",
    ]
    for _, row in cases.iterrows():
        lines.append(
            f"{_escape_latex(row['case'])} & "
            f"{_escape_latex(row['model_or_retriever'])} & "
            f"{_escape_latex(row['condition_or_setting'])} & "
            f"{_format_float(row['answer_f1_or_recall'])} & "
            f"{_format_float(row['evidence_f1_or_chain_coverage'])} & "
            f"{_format_float(row['context_gain'])} & "
            f"{_format_float(row['oracle_gap'])} & "
            f"{_format_float(row['oncu'])} & "
            f"{_escape_latex(row['diagnostic_reading'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}"])
    path.write_text("\n".join(lines) + "\n")


def _write_markdown(path: Path, cases: pd.DataFrame) -> None:
    display = cases.copy()
    for col in ["answer_f1_or_recall", "evidence_f1_or_chain_coverage", "context_gain", "oracle_gap", "oncu"]:
        display[col] = display[col].apply(_format_float)
    path.write_text(display.to_markdown(index=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create metric-comparison summaries for ONCU reviewer analysis.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory relative to root. Default: {DEFAULT_OUTPUT_DIR}",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / "longcue").is_dir() or not (root / "scripts").is_dir():
        raise SystemExit(f"ERROR: {root} does not look like the long_context_cue repository root.")
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    condition_df = _build_condition_metric_comparison(root)
    scaling_df = _build_controlled_scaling_metric_comparison(root)
    retrieval_df = _build_retrieval_metric_comparison(root)
    cases_df = _select_case_studies(condition_df, scaling_df, retrieval_df)

    generated: list[str] = []

    condition_path = out_dir / "metric_comparison_condition_summary.csv"
    condition_df.round(6).to_csv(condition_path, index=False)
    generated.append(str(condition_path.relative_to(root)))

    scaling_path = out_dir / "metric_comparison_controlled_scaling.csv"
    scaling_df.round(6).to_csv(scaling_path, index=False)
    generated.append(str(scaling_path.relative_to(root)))

    retrieval_path = out_dir / "metric_comparison_retrieval_only.csv"
    retrieval_df.round(6).to_csv(retrieval_path, index=False)
    generated.append(str(retrieval_path.relative_to(root)))

    cases_path = out_dir / "metric_comparison_case_studies.csv"
    cases_df.round(6).to_csv(cases_path, index=False)
    generated.append(str(cases_path.relative_to(root)))

    alt_table_path = out_dir / "metric_comparison_alternative_scores_table.tex"
    _write_alternative_scores_latex(alt_table_path)
    generated.append(str(alt_table_path.relative_to(root)))

    case_table_path = out_dir / "metric_comparison_case_studies_table.tex"
    _write_case_study_latex(case_table_path, cases_df)
    generated.append(str(case_table_path.relative_to(root)))

    md_path = out_dir / "metric_comparison_case_studies.md"
    _write_markdown(md_path, cases_df)
    generated.append(str(md_path.relative_to(root)))

    manifest = ScriptManifest(
        output_dir=str(out_dir.relative_to(root)),
        generated_files=generated,
        source_files=[
            str(CORE_ANSWER_PATH),
            str(CORE_ONCU_PATH),
            str(TWOWIKI_CONDITION_PATH),
            str(TWOWIKI_ONCU_PATH),
            str(SCALING_ONCU_PATH),
            str(RETRIEVER_HOTPOT_PATH),
            str(RETRIEVER_TWOWIKI_PATH),
        ],
        core_rows=int(len(condition_df)),
        controlled_scaling_rows=int(len(scaling_df)),
        retrieval_rows=int(len(retrieval_df)),
        case_study_rows=int(len(cases_df)),
    )
    manifest_path = out_dir / "metric_comparison_manifest.json"
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n")
    generated.append(str(manifest_path.relative_to(root)))

    print(f"Wrote metric-comparison outputs to {out_dir}")
    print(f"condition rows: {len(condition_df)}")
    print(f"controlled-scaling rows: {len(scaling_df)}")
    print(f"retrieval-only rows: {len(retrieval_df)}")
    print(f"case-study rows: {len(cases_df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
