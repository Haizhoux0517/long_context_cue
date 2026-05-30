#!/usr/bin/env python3
"""Generate statistical support tables for the ONCU diagnostic paper.

This script intentionally keeps the confirmatory statistics simple and
auditable. It uses paired/sample-matched contrasts whenever the same examples
are evaluated under multiple diagnostic conditions, and it reports effect sizes,
bootstrap confidence intervals, normal-approximation p-values, and Holm/FDR
adjustments. The outputs are intended as reviewer-facing statistical support for
the descriptive ONCU tables, not as a replacement for the released per-sample
metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "experiment_backups" / "statistical_modeling_20260530"
SCORE_FIELD = "answer_f1_relaxed"
RNG_SEED = 20260530


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paired and regression-style statistical summaries.")
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Repository root.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory.")
    parser.add_argument("--bootstrap", type=int, default=5000, help="Bootstrap replicates for paired CIs.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    effects: list[dict[str, Any]] = []
    effects.extend(_core_condition_effects(root, args.bootstrap))
    effects.extend(_twowiki_condition_effects(root, args.bootstrap))
    effects.extend(_controlled_scaling_effects(root, args.bootstrap))
    effects.extend(_retriever_family_effects(root, args.bootstrap))

    effects = _apply_multiple_testing(effects)
    effects_path = output_dir / "statistical_effects_summary.csv"
    _write_csv(effects_path, effects)
    _write_effects_tex(output_dir / "statistical_effects_table.tex", effects)

    regression_rows = []
    regression_rows.extend(_controlled_scaling_regression(root))
    regression_rows.extend(_retriever_family_regression(root))
    regression_rows = _apply_multiple_testing(regression_rows)
    _write_csv(output_dir / "statistical_regression_summary.csv", regression_rows)
    _write_regression_tex(output_dir / "statistical_regression_table.tex", regression_rows)

    manifest = {
        "script": "scripts/statistical_modeling.py",
        "score_field": SCORE_FIELD,
        "bootstrap_replicates": args.bootstrap,
        "random_seed": RNG_SEED,
        "outputs": {
            "effects": "statistical_effects_summary.csv",
            "effects_table": "statistical_effects_table.tex",
            "regression": "statistical_regression_summary.csv",
            "regression_table": "statistical_regression_table.tex",
        },
        "notes": [
            "Paired contrasts resample matched units with replacement.",
            "P-values are normal-approximation diagnostics derived from paired differences or OLS standard errors.",
            "Holm controls family-wise error rate for the confirmatory family; Benjamini-Hochberg is also reported for exploratory auditing.",
            "Regression rows are descriptive support for effect direction; the paper's main claims are based on fixed-condition outputs and confidence intervals.",
        ],
    }
    (output_dir / "statistical_modeling_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(f"Wrote statistical modeling outputs to {output_dir}")
    print(f"effect rows: {len(effects)}")
    print(f"regression rows: {len(regression_rows)}")


# ---------------------------------------------------------------------------
# Confirmatory paired effects
# ---------------------------------------------------------------------------


def _core_condition_effects(root: Path, bootstrap: int) -> list[dict[str, Any]]:
    base = root / "experiment_backups" / "sci200_final_3model_20260525"
    paths = sorted(base.glob("*/results/per_sample_metrics.csv"))
    rows: list[dict[str, Any]] = []
    for path in paths:
        df = pd.read_csv(path)
        if df.empty:
            continue
        model = _display_model_name(str(df["model_name"].iloc[0]))
        source = str(df["source"].iloc[0])
        dataset = "Controlled-safe16K-200" if source == "controlled" else "HotpotQA-ONCU-200"
        if source == "controlled":
            rows.append(
                _paired_condition_contrast(
                    df=df,
                    label=f"{dataset}: retrieved minus full",
                    family="condition_effects_confirmatory",
                    model=model,
                    dataset=dataset,
                    condition_a="retrieve_then_read",
                    condition_b="direct",
                    direction="retrieved - full",
                    bootstrap=bootstrap,
                )
            )
        elif source == "hotpotqa":
            rows.append(
                _paired_condition_contrast(
                    df=df,
                    label=f"{dataset}: full minus retrieved",
                    family="condition_effects_confirmatory",
                    model=model,
                    dataset=dataset,
                    condition_a="direct",
                    condition_b="retrieve_then_read",
                    direction="full - retrieved",
                    bootstrap=bootstrap,
                )
            )
    return rows


def _twowiki_condition_effects(root: Path, bootstrap: int) -> list[dict[str, Any]]:
    base = root / "experiment_backups" / "twowiki_500_validation_20260527" / "per_model"
    paths = sorted(base.glob("*/per_sample_metrics.csv"))
    rows: list[dict[str, Any]] = []
    for path in paths:
        df = pd.read_csv(path)
        if df.empty:
            continue
        model = _display_model_name(str(df["model_name"].iloc[0]))
        rows.append(
            _paired_condition_contrast(
                df=df,
                label="2WikiMultiHopQA-ONCU-500: full minus retrieved",
                family="condition_effects_confirmatory",
                model=model,
                dataset="2WikiMultiHopQA-ONCU-500",
                condition_a="direct",
                condition_b="retrieve_then_read",
                direction="full - retrieved",
                bootstrap=bootstrap,
            )
        )
    return rows


def _paired_condition_contrast(
    *,
    df: pd.DataFrame,
    label: str,
    family: str,
    model: str,
    dataset: str,
    condition_a: str,
    condition_b: str,
    direction: str,
    bootstrap: int,
) -> dict[str, Any]:
    subset = df[df["method"].isin([condition_a, condition_b])].copy()
    pivot = subset.pivot_table(index="sample_id", columns="method", values=SCORE_FIELD, aggfunc="mean")
    pivot = pivot.dropna(subset=[condition_a, condition_b])
    diff = (pivot[condition_a] - pivot[condition_b]).astype(float).to_numpy()
    ci_low, ci_high = _bootstrap_ci(diff, bootstrap)
    return _effect_row(
        analysis=label,
        family=family,
        model=model,
        dataset=dataset,
        contrast=direction,
        estimate=float(np.mean(diff)) if len(diff) else math.nan,
        ci_low=ci_low,
        ci_high=ci_high,
        effect_size=_paired_effect_size(diff),
        p_value=_normal_p_from_diffs(diff),
        n=len(diff),
        metric=SCORE_FIELD,
        interpretation=_interpret_condition_effect(dataset, direction, diff),
    )


def _controlled_scaling_effects(root: Path, bootstrap: int) -> list[dict[str, Any]]:
    path = root / "experiment_backups" / "controlled_scaling_20260527" / "summary" / "controlled_scaling_oncu_by_length_position.csv"
    if not path.is_file():
        return []
    df = pd.read_csv(path)
    rows: list[dict[str, Any]] = []
    for model_name, model_df in df.groupby("model_name"):
        model = _display_model_name(str(model_name))
        direct = model_df[model_df["long_method"] == "direct"].copy()
        retrieved = model_df[model_df["long_method"] == "retrieve_then_read"].copy()

        # Length drop: 4K minus 32K, paired by evidence-position bucket.
        wide = direct.pivot_table(index="evidence_position", columns="context_length", values="oncu_clipped", aggfunc="mean")
        if 4000 in wide.columns and 32000 in wide.columns:
            diff = (wide[4000] - wide[32000]).dropna().to_numpy(dtype=float)
            ci_low, ci_high = _bootstrap_ci(diff, bootstrap)
            rows.append(
                _effect_row(
                    analysis="Controlled scaling: 4K minus 32K full-context ONCU",
                    family="scaling_effects_confirmatory",
                    model=model,
                    dataset="Controlled-scaling-3200",
                    contrast="4K - 32K full-context ONCU",
                    estimate=float(np.mean(diff)),
                    ci_low=ci_low,
                    ci_high=ci_high,
                    effect_size=_paired_effect_size(diff),
                    p_value=_normal_p_from_diffs(diff),
                    n=len(diff),
                    metric="ONCU_Relaxed_F1",
                    interpretation="Positive values indicate length-induced full-context utilization loss.",
                )
            )

        # End-position advantage at 32K: use pos_09 minus the average of pos_00 through pos_07.
        d32 = direct[direct["context_length"] == 32000].set_index("evidence_position")
        if "pos_09" in d32.index:
            early_positions = [f"pos_{i:02d}" for i in range(8) if f"pos_{i:02d}" in d32.index]
            if early_positions:
                end_val = float(d32.loc["pos_09", "oncu_clipped"])
                early_vals = d32.loc[early_positions, "oncu_clipped"].astype(float).to_numpy()
                diff = end_val - early_vals
                ci_low, ci_high = _bootstrap_ci(diff, bootstrap)
                rows.append(
                    _effect_row(
                        analysis="Controlled scaling: 32K final decile minus early/middle deciles",
                        family="scaling_effects_confirmatory",
                        model=model,
                        dataset="Controlled-scaling-3200",
                        contrast="pos_09 - mean(pos_00..pos_07) at 32K",
                        estimate=float(np.mean(diff)),
                        ci_low=ci_low,
                        ci_high=ci_high,
                        effect_size=_paired_effect_size(diff),
                        p_value=_normal_p_from_diffs(diff),
                        n=len(diff),
                        metric="ONCU_Relaxed_F1",
                        interpretation="Positive values indicate recency/end-position advantage at 32K.",
                    )
                )

        # Compact evidence advantage at 32K: retrieved minus direct, paired by position.
        direct32 = direct[direct["context_length"] == 32000].set_index("evidence_position")
        ret32 = retrieved[retrieved["context_length"] == 32000].set_index("evidence_position")
        common = sorted(set(direct32.index) & set(ret32.index))
        if common:
            diff = (ret32.loc[common, "oncu_clipped"].astype(float) - direct32.loc[common, "oncu_clipped"].astype(float)).to_numpy()
            ci_low, ci_high = _bootstrap_ci(diff, bootstrap)
            rows.append(
                _effect_row(
                    analysis="Controlled scaling: 32K retrieved minus full-context ONCU",
                    family="scaling_effects_confirmatory",
                    model=model,
                    dataset="Controlled-scaling-3200",
                    contrast="retrieved - full at 32K",
                    estimate=float(np.mean(diff)),
                    ci_low=ci_low,
                    ci_high=ci_high,
                    effect_size=_paired_effect_size(diff),
                    p_value=_normal_p_from_diffs(diff),
                    n=len(diff),
                    metric="ONCU_Relaxed_F1",
                    interpretation="Positive values indicate that compact evidence recovers oracle-normalized advantage at 32K.",
                )
            )
    return rows


def _retriever_family_effects(root: Path, bootstrap: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset_dir, dataset_label in [
        ("hotpotqa", "HotpotQA-ONCU-200"),
        ("twowiki", "2WikiMultiHopQA-ONCU-500"),
    ]:
        path = root / "experiment_backups" / "retriever_family_ablation_20260527" / dataset_dir / "retrieval_only_per_sample.csv"
        if not path.is_file():
            continue
        df = pd.read_csv(path)
        # Retrieval budget effect for lexical retrieval: top16 minus top3.
        lexical = df[df["retriever"] == "lexical"].copy()
        pivot = lexical.pivot_table(index="sample_id", columns="top_k", values="full_chain_coverage", aggfunc="mean")
        if 3 in pivot.columns and 16 in pivot.columns:
            diff = (pivot[16] - pivot[3]).dropna().to_numpy(dtype=float)
            ci_low, ci_high = _bootstrap_ci(diff, bootstrap)
            rows.append(
                _effect_row(
                    analysis="Retriever ablation: lexical top-16 minus top-3 chain coverage",
                    family="retriever_effects_exploratory",
                    model="retrieval-only",
                    dataset=dataset_label,
                    contrast="lexical top16 - top3",
                    estimate=float(np.mean(diff)),
                    ci_low=ci_low,
                    ci_high=ci_high,
                    effect_size=_paired_effect_size(diff),
                    p_value=_normal_p_from_diffs(diff),
                    n=len(diff),
                    metric="full_chain_coverage",
                    interpretation="Positive values indicate that larger retrieval budgets recover more complete evidence chains.",
                )
            )
        # Dense vs lexical at top-3.
        top3 = df[df["top_k"] == 3].copy()
        pivot = top3.pivot_table(index="sample_id", columns="retriever", values="full_chain_coverage", aggfunc="mean")
        if "dense" in pivot.columns and "lexical" in pivot.columns:
            diff = (pivot["dense"] - pivot["lexical"]).dropna().to_numpy(dtype=float)
            ci_low, ci_high = _bootstrap_ci(diff, bootstrap)
            rows.append(
                _effect_row(
                    analysis="Retriever ablation: dense minus lexical top-3 chain coverage",
                    family="retriever_effects_exploratory",
                    model="retrieval-only",
                    dataset=dataset_label,
                    contrast="dense - lexical at top3",
                    estimate=float(np.mean(diff)),
                    ci_low=ci_low,
                    ci_high=ci_high,
                    effect_size=_paired_effect_size(diff),
                    p_value=_normal_p_from_diffs(diff),
                    n=len(diff),
                    metric="full_chain_coverage",
                    interpretation="Positive values indicate stronger dense full-chain recovery at the main retrieval budget.",
                )
            )
    return rows


# ---------------------------------------------------------------------------
# Regression-style support
# ---------------------------------------------------------------------------


def _controlled_scaling_regression(root: Path) -> list[dict[str, Any]]:
    path = root / "experiment_backups" / "controlled_scaling_20260527" / "summary" / "controlled_scaling_oncu_by_length_position.csv"
    if not path.is_file():
        return []
    df = pd.read_csv(path)
    df = df[df["long_method"] == "direct"].copy()
    rows: list[dict[str, Any]] = []
    for model_name, g in df.groupby("model_name"):
        g = g.dropna(subset=["oncu_clipped", "context_length", "position_fraction"]).copy()
        g["log2_length_centered"] = np.log2(g["context_length"].astype(float)) - np.log2(g["context_length"].astype(float)).mean()
        g["position_centered"] = g["position_fraction"].astype(float) - g["position_fraction"].astype(float).mean()
        g["distance_from_end_centered"] = (1.0 - g["position_fraction"].astype(float)) - (1.0 - g["position_fraction"].astype(float)).mean()
        X = np.column_stack(
            [
                np.ones(len(g)),
                g["log2_length_centered"].to_numpy(),
                g["position_centered"].to_numpy(),
                g["distance_from_end_centered"].to_numpy(),
            ]
        )
        terms = ["intercept", "log2_context_length_centered", "position_fraction_centered", "distance_from_end_centered"]
        y = g["oncu_clipped"].astype(float).to_numpy()
        result = _ols_fit(X, y)
        for term, coef, se, pval in zip(terms, result["coef"], result["se"], result["p_value"]):
            rows.append(
                {
                    "analysis": "Controlled scaling OLS over length-position cells",
                    "family": "regression_effects_exploratory",
                    "model": _display_model_name(str(model_name)),
                    "dataset": "Controlled-scaling-3200",
                    "term": term,
                    "estimate": coef,
                    "standard_error": se,
                    "p_value": pval,
                    "r_squared": result["r_squared"],
                    "n": len(g),
                    "metric": "full-context ONCU_Relaxed_F1",
                    "interpretation": _regression_interpretation(term),
                }
            )
    return rows


def _retriever_family_regression(root: Path) -> list[dict[str, Any]]:
    frames = []
    for dataset_dir, dataset_label in [
        ("hotpotqa", "HotpotQA-ONCU-200"),
        ("twowiki", "2WikiMultiHopQA-ONCU-500"),
    ]:
        path = root / "experiment_backups" / "retriever_family_ablation_20260527" / dataset_dir / "retrieval_only_per_sample.csv"
        if path.is_file():
            df = pd.read_csv(path)
            df["dataset_label"] = dataset_label
            frames.append(df)
    if not frames:
        return []
    df = pd.concat(frames, ignore_index=True)
    # Summary-level design: top_k plus retriever and dataset indicators.
    g = (
        df.groupby(["dataset_label", "retriever", "top_k"], as_index=False)
        .agg(full_chain_coverage=("full_chain_coverage", "mean"), distractor_id_rate=("distractor_id_rate", "mean"))
    )
    g["log2_top_k_centered"] = np.log2(g["top_k"].astype(float)) - np.log2(g["top_k"].astype(float)).mean()

    retrievers = sorted(r for r in g["retriever"].unique() if r != "lexical")
    datasets = sorted(d for d in g["dataset_label"].unique() if d != "HotpotQA-ONCU-200")
    X_parts = [np.ones(len(g)), g["log2_top_k_centered"].to_numpy()]
    terms = ["intercept", "log2_top_k_centered"]
    for r in retrievers:
        X_parts.append((g["retriever"] == r).astype(float).to_numpy())
        terms.append(f"retriever_{r}_vs_lexical")
    for d in datasets:
        X_parts.append((g["dataset_label"] == d).astype(float).to_numpy())
        terms.append(f"dataset_{d}_vs_HotpotQA")
    X = np.column_stack(X_parts)
    y = g["full_chain_coverage"].astype(float).to_numpy()
    result = _ols_fit(X, y)
    rows = []
    for term, coef, se, pval in zip(terms, result["coef"], result["se"], result["p_value"]):
        rows.append(
            {
                "analysis": "Retriever-family OLS over retrieval summary cells",
                "family": "regression_effects_exploratory",
                "model": "retrieval-only",
                "dataset": "HotpotQA-ONCU-200 + 2WikiMultiHopQA-ONCU-500",
                "term": term,
                "estimate": coef,
                "standard_error": se,
                "p_value": pval,
                "r_squared": result["r_squared"],
                "n": len(g),
                "metric": "full_chain_coverage",
                "interpretation": _regression_interpretation(term),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def _bootstrap_ci(values: np.ndarray, reps: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(RNG_SEED + len(values))
    if len(values) == 1:
        return float(values[0]), float(values[0])
    samples = rng.choice(values, size=(reps, len(values)), replace=True)
    means = samples.mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _paired_effect_size(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return math.nan
    sd = float(np.std(values, ddof=1))
    if sd == 0:
        return math.inf if float(np.mean(values)) > 0 else (0.0 if float(np.mean(values)) == 0 else -math.inf)
    return float(np.mean(values) / sd)


def _normal_p_from_diffs(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return math.nan
    sd = float(np.std(values, ddof=1))
    if sd == 0:
        return 0.0 if abs(float(np.mean(values))) > 0 else 1.0
    z = abs(float(np.mean(values)) / (sd / math.sqrt(len(values))))
    return float(math.erfc(z / math.sqrt(2.0)))


def _ols_fit(X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    residuals = y - y_hat
    n, p = X.shape
    df = max(n - p, 1)
    rss = float(np.sum(residuals**2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - rss / tss if tss > 0 else math.nan
    sigma2 = rss / df
    xtx_inv = np.linalg.pinv(X.T @ X)
    cov = sigma2 * xtx_inv
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    p_values = []
    for b, s in zip(beta, se):
        if s == 0:
            p_values.append(0.0 if abs(b) > 0 else 1.0)
        else:
            z = abs(float(b / s))
            p_values.append(float(math.erfc(z / math.sqrt(2.0))))
    return {
        "coef": [float(x) for x in beta],
        "se": [float(x) for x in se],
        "p_value": p_values,
        "r_squared": float(r_squared),
    }


def _apply_multiple_testing(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Apply corrections within each family.
    by_family: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        p = row.get("p_value", math.nan)
        if p is not None and np.isfinite(float(p)):
            by_family[str(row.get("family", "default"))].append(idx)

    for indices in by_family.values():
        pvals = [float(rows[i]["p_value"]) for i in indices]
        holm = _holm_adjust(pvals)
        bh = _bh_adjust(pvals)
        for i, hp, bp in zip(indices, holm, bh):
            rows[i]["p_holm"] = hp
            rows[i]["p_bh_fdr"] = bp

    for row in rows:
        row.setdefault("p_holm", math.nan)
        row.setdefault("p_bh_fdr", math.nan)
    return rows


def _holm_adjust(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)
        adjusted[idx] = min(1.0, running)
    return adjusted


def _bh_adjust(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i], reverse=True)
    adjusted = [0.0] * m
    running = 1.0
    for rank_from_end, idx in enumerate(order):
        rank = m - rank_from_end
        val = pvals[idx] * m / rank
        running = min(running, val)
        adjusted[idx] = min(1.0, running)
    return adjusted


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _effect_row(**kwargs: Any) -> dict[str, Any]:
    ordered = {
        "analysis": kwargs.get("analysis"),
        "family": kwargs.get("family"),
        "model": kwargs.get("model"),
        "dataset": kwargs.get("dataset"),
        "contrast": kwargs.get("contrast"),
        "metric": kwargs.get("metric"),
        "estimate": kwargs.get("estimate"),
        "ci_low": kwargs.get("ci_low"),
        "ci_high": kwargs.get("ci_high"),
        "effect_size": kwargs.get("effect_size"),
        "p_value": kwargs.get("p_value"),
        "p_holm": math.nan,
        "p_bh_fdr": math.nan,
        "n": kwargs.get("n"),
        "interpretation": kwargs.get("interpretation"),
    }
    return ordered


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    # Ensure union fields are included in stable order.
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_effects_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    # Select the most paper-relevant rows to keep the main table compact.
    selected = [
        r for r in rows
        if r["family"] in {"condition_effects_confirmatory", "scaling_effects_confirmatory", "retriever_effects_exploratory"}
    ]
    selected = selected[:18]
    lines = [
        "% Auto-generated by scripts/statistical_modeling.py",
        "\\begin{table*}[!t]",
        "\\renewcommand{\\arraystretch}{1.08}",
        "\\caption{Statistical Support for Main Diagnostic Effects. Estimates are paired mean differences unless otherwise noted. Confidence intervals are paired bootstrap 95\\% intervals. $p_{\\mathrm{Holm}}$ controls family-wise error within the stated analysis family.}",
        "\\label{tab:statistical_effects_support}",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{2.2pt}",
        "\\begin{tabular}{p{0.19\\textwidth} p{0.16\\textwidth} p{0.18\\textwidth} r r r r}",
        "\\toprule",
        "Analysis & Model & Contrast & Est. & 95\\% CI & Effect & $p_{\\mathrm{Holm}}$ \\\\",
        "\\midrule",
    ]
    for row in selected:
        analysis = _latex_escape(str(row["analysis"]).replace("Controlled scaling: ", "Scaling: ").replace("Retriever ablation: ", "Retriever: "))
        model = _latex_escape(str(row["model"]))
        contrast = _latex_escape(str(row["contrast"]))
        est = _fmt(float(row["estimate"]))
        ci = f"[{_fmt(float(row['ci_low']))}, {_fmt(float(row['ci_high']))}]"
        eff = _fmt(float(row["effect_size"]))
        p = _fmt_p(float(row["p_holm"]))
        lines.append(f"{analysis} & {model} & {contrast} & {est} & {ci} & {eff} & {p} \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_regression_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    selected = [
        r for r in rows
        if r.get("term") in {
            "log2_context_length_centered",
            "position_fraction_centered",
            "distance_from_end_centered",
            "log2_top_k_centered",
            "retriever_dense_vs_lexical",
            "retriever_hybrid_vs_lexical",
            "retriever_oracle_vs_lexical",
        }
    ]
    lines = [
        "% Auto-generated by scripts/statistical_modeling.py",
        "\\begin{table*}[!t]",
        "\\renewcommand{\\arraystretch}{1.08}",
        "\\caption{Regression-Style Statistical Checks. Controlled scaling rows are OLS diagnostics over aggregated length--position ONCU cells. Retriever rows are OLS diagnostics over retrieval-summary cells. These models support effect direction and magnitude rather than replacing the paired analyses.}",
        "\\label{tab:statistical_regression_support}",
        "\\centering",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{p{0.24\\textwidth} p{0.18\\textwidth} p{0.22\\textwidth} r r r}",
        "\\toprule",
        "Analysis & Model/Dataset & Term & Est. & SE & $p_{\\mathrm{BH}}$ \\\\",
        "\\midrule",
    ]
    for row in selected:
        analysis = _latex_escape(str(row["analysis"]).replace("Controlled scaling OLS over length-position cells", "Scaling OLS").replace("Retriever-family OLS over retrieval summary cells", "Retriever OLS"))
        model_dataset = _latex_escape(f"{row['model']} / {row['dataset']}")
        term = _latex_escape(str(row["term"]))
        lines.append(
            f"{analysis} & {model_dataset} & {term} & {_fmt(float(row['estimate']))} & {_fmt(float(row['standard_error']))} & {_fmt_p(float(row['p_bh_fdr']))} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _fmt(x: float) -> str:
    if not np.isfinite(x):
        return "--"
    return f"{x:.3f}"


def _fmt_p(x: float) -> str:
    if not np.isfinite(x):
        return "--"
    if x < 0.001:
        return "$<$.001"
    return f"{x:.3f}"


def _latex_escape(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("#", "\\#")
    )


def _display_model_name(model_name: str) -> str:
    mapping = {
        "qwen2.5:14b": "Qwen2.5-14B",
        "qwen3:14b": "Qwen3-14B",
        "gemma3:12b": "Gemma3-12B",
    }
    return mapping.get(model_name, model_name)


def _interpret_condition_effect(dataset: str, direction: str, diff: np.ndarray) -> str:
    if not len(diff):
        return ""
    estimate = float(np.mean(diff))
    if "Controlled" in dataset and "retrieved" in direction:
        return "Positive values support the controlled full-context utilization bottleneck."
    if "HotpotQA" in dataset or "2Wiki" in dataset:
        return "Positive values support the realistic multi-hop retrieval-coverage bottleneck."
    return "Positive values support the stated condition contrast."


def _regression_interpretation(term: str) -> str:
    if "log2_context_length" in term:
        return "Negative controlled-scaling coefficients indicate lower ONCU at longer contexts."
    if "position_fraction" in term:
        return "Positive coefficients indicate stronger utilization near later evidence positions."
    if "distance_from_end" in term:
        return "Negative coefficients indicate an end-position advantage."
    if "log2_top_k" in term:
        return "Positive coefficients indicate greater full-chain coverage at larger retrieval budgets."
    if "retriever" in term:
        return "Retriever-family coefficient relative to lexical retrieval."
    return ""


if __name__ == "__main__":
    main()
