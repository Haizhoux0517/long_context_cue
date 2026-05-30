#!/usr/bin/env python3
"""Summarize controlled context-length and position scaling runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCORE_FIELD = "answer_f1_relaxed"
CORE_METHODS = {"no_evidence", "direct", "retrieve_then_read", "oracle"}
CONTEXT_ORDER = [4000, 8000, 16000, 32000]
POSITION_ORDER = [f"pos_{index:02d}" for index in range(10)] + ["front", "middle", "end", "scattered", "unknown"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize controlled scaling outputs into ONCU and failure heatmaps."
    )
    parser.add_argument(
        "--run-dir",
        action="append",
        required=True,
        help="Run output directory containing results/per_sample_metrics.csv. Repeatable.",
    )
    parser.add_argument(
        "--output-dir",
        default="experiment_backups/controlled_scaling_20260527/summary",
    )
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for run_dir_text in args.run_dir:
        run_dir = Path(run_dir_text)
        metrics_path = run_dir / "results" / "per_sample_metrics.csv"
        if not metrics_path.is_file():
            raise FileNotFoundError(f"Missing per-sample metrics: {metrics_path}")
        records.extend(_read_csv(metrics_path))
        manifest_path = run_dir / "protocol_manifest.json"
        if manifest_path.is_file():
            try:
                manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    condition_summary = summarize_conditions(records)
    oncu_rows = summarize_oncu_by_length_position(records)
    failure_rows = summarize_failure_heatmap(records)
    regression_rows = summarize_position_length_regression(oncu_rows)

    _write_csv(output_dir / "controlled_scaling_condition_summary.csv", condition_summary)
    _write_csv(output_dir / "controlled_scaling_oncu_by_length_position.csv", oncu_rows)
    _write_csv(output_dir / "controlled_scaling_failure_heatmap.csv", failure_rows)
    _write_csv(output_dir / "controlled_scaling_regression.csv", regression_rows)
    _write_markdown(output_dir / "controlled_scaling_oncu_by_length_position.md", oncu_rows)
    _write_tex_heatmap_table(
        output_dir / "controlled_scaling_heatmap_table.tex",
        oncu_rows,
        method="direct",
    )
    _write_tex_regression_table(
        output_dir / "controlled_scaling_regression_table.tex",
        regression_rows,
    )
    (output_dir / "controlled_scaling_summary_manifest.json").write_text(
        json.dumps(
            {
                "run_dirs": [str(Path(item)) for item in args.run_dir],
                "input_rows": len(records),
                "manifests": manifests,
                "score_field": SCORE_FIELD,
                "outputs": {
                    "condition_summary": "controlled_scaling_condition_summary.csv",
                    "oncu_by_length_position": "controlled_scaling_oncu_by_length_position.csv",
                    "failure_heatmap": "controlled_scaling_failure_heatmap.csv",
                    "regression": "controlled_scaling_regression.csv",
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(f"Wrote controlled scaling summaries to {output_dir}")
    print(f"condition rows: {len(condition_summary)}")
    print(f"ONCU rows: {len(oncu_rows)}")
    print(f"failure rows: {len(failure_rows)}")
    print(f"regression rows: {len(regression_rows)}")


def summarize_conditions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    fields = (
        "model_name",
        "method",
        "context_length",
        "evidence_position",
        "reasoning_type",
        "distractor_similarity",
    )
    for record in records:
        if str(record.get("method", "")) not in CORE_METHODS:
            continue
        key = tuple(record.get(field, "unknown") for field in fields)
        groups[key].append(record)
    rows: list[dict[str, Any]] = []
    for key, items in sorted(groups.items(), key=_sort_key):
        row = dict(zip(fields, key))
        row.update(
            {
                "n": len(items),
                "answer_f1_relaxed": _mean(items, "answer_f1_relaxed"),
                "exact_match_relaxed": _mean(items, "exact_match_relaxed"),
                "evidence_f1": _mean(items, "evidence_f1"),
                "parse_error_rate": _parse_error_rate(items),
            }
        )
        rows.append(row)
    return rows


def summarize_oncu_by_length_position(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    fields = ("model_name", "context_length", "evidence_position")
    for record in records:
        method = str(record.get("method", ""))
        if method not in CORE_METHODS:
            continue
        key = tuple(record.get(field, "unknown") for field in fields)
        grouped[key][method].append(record)

    rows: list[dict[str, Any]] = []
    for key, by_method in sorted(grouped.items(), key=_sort_key):
        model_name, context_length, evidence_position = key
        score_no = _mean(by_method.get("no_evidence", []), SCORE_FIELD)
        score_oracle = _mean(by_method.get("oracle", []), SCORE_FIELD)
        denominator = _safe_subtract(score_oracle, score_no)
        for method in ("direct", "retrieve_then_read"):
            items = by_method.get(method, [])
            score_long = _mean(items, SCORE_FIELD)
            invalid_reason = _invalid_reason(score_no, score_oracle, items)
            raw = ""
            clipped = ""
            if not invalid_reason and denominator and score_long is not None and score_no is not None:
                raw_value = (score_long - score_no) / denominator
                raw = raw_value
                clipped = max(0.0, min(1.0, raw_value))
            rows.append(
                {
                    "model_name": model_name,
                    "context_length": context_length,
                    "evidence_position": evidence_position,
                    "position_fraction": _position_fraction(evidence_position),
                    "long_method": method,
                    "score_field": SCORE_FIELD,
                    "score_no_evidence": score_no,
                    "score_oracle": score_oracle,
                    "score_long": score_long,
                    "n": len(items),
                    "oncu_valid": not bool(invalid_reason),
                    "oncu_invalid_reason": invalid_reason,
                    "oncu_raw": raw,
                    "oncu_clipped": clipped,
                }
            )
    return rows


def summarize_failure_heatmap(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    fields = ("model_name", "method", "context_length", "evidence_position")
    for record in records:
        method = str(record.get("method", ""))
        if method not in {"direct", "retrieve_then_read"}:
            continue
        key = tuple(record.get(field, "unknown") for field in fields)
        grouped[key].append(record)
    rows: list[dict[str, Any]] = []
    for key, items in sorted(grouped.items(), key=_sort_key):
        counts = Counter(str(item.get("failure_type", "unknown") or "unknown") for item in items)
        total = len(items)
        for failure_type in sorted(counts):
            rows.append(
                {
                    **dict(zip(fields, key)),
                    "failure_type": failure_type,
                    "count": counts[failure_type],
                    "n": total,
                    "rate": counts[failure_type] / total if total else "",
                }
            )
    return rows


def summarize_position_length_regression(oncu_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fit a lightweight OLS diagnostic model over valid full-context ONCU cells."""
    rows: list[dict[str, Any]] = []
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in oncu_rows:
        if row.get("long_method") != "direct" or not row.get("oncu_valid"):
            continue
        if row.get("oncu_clipped") in ("", None):
            continue
        by_model[str(row.get("model_name", "unknown"))].append(row)

    for model_name, items in sorted(by_model.items()):
        fitted = _fit_ols(items)
        for term, coef in fitted.get("coefficients", {}).items():
            rows.append(
                {
                    "model_name": model_name,
                    "model_type": "ols_diagnostic",
                    "dependent_variable": "full_context_oncu_clipped",
                    "term": term,
                    "coefficient": coef,
                    "r_squared": fitted.get("r_squared", ""),
                    "n": len(items),
                    "note": "OLS summary over aggregated length-position ONCU cells; use as diagnostic effect direction, not causal inference.",
                }
            )
    return rows


def _fit_ols(items: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import numpy as np
    except Exception:
        return {"coefficients": {}, "r_squared": ""}
    y = np.array([float(item["oncu_clipped"]) for item in items], dtype=float)
    length_values = np.array([math.log2(float(item["context_length"])) for item in items], dtype=float)
    position_values = np.array([float(item.get("position_fraction") or 0.5) for item in items], dtype=float)
    middle_penalty = np.abs(position_values - 0.5)
    X = np.column_stack(
        [
            np.ones(len(items)),
            length_values - length_values.mean(),
            position_values - position_values.mean(),
            middle_penalty - middle_penalty.mean(),
        ]
    )
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else ""
    return {
        "coefficients": {
            "intercept": float(coef[0]),
            "log2_context_length_centered": float(coef[1]),
            "position_fraction_centered": float(coef[2]),
            "distance_from_middle_centered": float(coef[3]),
        },
        "r_squared": r2,
    }


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict[str, Any]], limit: int = 80) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0])
    lines = ["| " + " | ".join(fieldnames) + " |", "| " + " | ".join(["---"] * len(fieldnames)) + " |"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(_format_value(row.get(field, "")) for field in fieldnames) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_tex_heatmap_table(path: Path, rows: list[dict[str, Any]], *, method: str) -> None:
    filtered = [row for row in rows if row.get("long_method") == method and row.get("oncu_valid")]
    if not filtered:
        path.write_text("% No valid controlled scaling rows available.\n", encoding="utf-8")
        return
    # Use the first model in lexical order for a compact reviewer-facing table.
    model_name = sorted({str(row["model_name"]) for row in filtered})[0]
    model_rows = [row for row in filtered if str(row["model_name"]) == model_name]
    values = {(int(row["context_length"]), str(row["evidence_position"])): float(row["oncu_clipped"]) for row in model_rows}
    positions = [pos for pos in POSITION_ORDER if any((length, pos) in values for length in CONTEXT_ORDER)]
    lines = [
        r"\begin{table*}[!t]",
        r"\renewcommand{\arraystretch}{1.08}",
        rf"\caption{{Controlled scaling ONCU heatmap for {model_name}. Values are clipped ONCU-Relaxed-F1 for the full-context condition.}}",
        r"\label{tab:controlled_scaling_heatmap}",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{l" + "c" * len(positions) + "}",
        r"\toprule",
        "Context & " + " & ".join(positions) + r" \\",
        r"\midrule",
    ]
    for length in CONTEXT_ORDER:
        row_vals = [_format_float(values.get((length, pos), "")) for pos in positions]
        lines.append(f"{length//1000}K & " + " & ".join(row_vals) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_tex_regression_table(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("% No regression rows available.\n", encoding="utf-8")
        return
    lines = [
        r"\begin{table}[!t]",
        r"\renewcommand{\arraystretch}{1.08}",
        r"\caption{Controlled scaling diagnostic regression summary. Coefficients are fit over aggregated full-context ONCU cells.}",
        r"\label{tab:controlled_scaling_regression}",
        r"\centering",
        r"\scriptsize",
        r"\begin{tabular}{llrr}",
        r"\toprule",
        r"Model & Term & Coef. & $R^2$ \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['model_name']} & {row['term'].replace('_', chr(92) + '_')} & {_format_float(row['coefficient'])} & {_format_float(row['r_squared'])} \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mean(items: list[dict[str, Any]], field: str) -> float | None:
    values = []
    for item in items:
        value = item.get(field, "")
        if value == "" or value is None:
            continue
        values.append(float(value))
    return mean(values) if values else None


def _parse_error_rate(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    return sum(1 for item in items if str(item.get("parse_error", "")).strip()) / len(items)


def _invalid_reason(score_no: float | None, score_oracle: float | None, items: list[dict[str, Any]]) -> str:
    if score_no is None:
        return "missing_no_evidence"
    if score_oracle is None:
        return "missing_oracle"
    if score_oracle <= score_no:
        return "oracle_not_above_no_evidence"
    if not items:
        return "missing_contextual_condition"
    return ""


def _safe_subtract(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def _position_fraction(label: Any) -> float | str:
    text = str(label)
    if text == "front":
        return 0.05
    if text == "middle":
        return 0.50
    if text == "end":
        return 0.88
    if text.startswith("pos_"):
        try:
            return (int(text.split("_", 1)[1]) + 0.5) / 10.0
        except (IndexError, ValueError):
            return ""
    return ""


def _sort_key(item: Any) -> Any:
    if isinstance(item, tuple):
        return tuple(_sort_component(part) for part in item)
    if isinstance(item, dict):
        return tuple(_sort_component(item.get(key, "")) for key in sorted(item))
    return item


def _sort_component(value: Any) -> Any:
    text = str(value)
    try:
        return (0, int(text))
    except ValueError:
        pass
    if text in POSITION_ORDER:
        return (1, POSITION_ORDER.index(text))
    return (2, text)


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return _format_float(value)
    return str(value)


def _format_float(value: Any) -> str:
    if value == "" or value is None:
        return ""
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


if __name__ == "__main__":
    main()
