#!/usr/bin/env python3
"""Recompute the 2WikiMultiHopQA-ONCU-500 derived summary tables.

This script summarizes the completed 2Wiki per-sample metrics released under
``experiment_backups/twowiki_500_validation_20260527/per_model`` and writes the
paper-facing summary CSVs back into the same backup directory.

It intentionally consumes frozen per-sample metrics rather than raw model
responses so reviewers can audit the paper tables without rerunning local LLM
inference.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiment_backups" / "twowiki_500_validation_20260527"
PER_MODEL = BASE / "per_model"

MODELS = {
    "qwen25": "Qwen2.5-14B",
    "qwen3": "Qwen3-14B",
    "gemma3": "Gemma3-12B",
}

GROUP_COLS = [
    "reasoning_type",
    "context_length",
    "evidence_position",
    "evidence_density",
    "distractor_similarity",
]


def bootstrap_mean(vals: np.ndarray, seed: int = 42, n_bootstrap: int = 5000) -> tuple[float, float, float]:
    """Return mean and two-sided percentile bootstrap interval."""
    vals = np.asarray(vals, dtype=float)
    if vals.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, vals.size, size=(n_bootstrap, vals.size))
    means = vals[idx].mean(axis=1)
    return float(vals.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def load_per_sample() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for key, display_name in MODELS.items():
        path = PER_MODEL / key / "per_sample_metrics.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing per-sample metrics: {path}")
        df = pd.read_csv(path)
        df["model_display"] = display_name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    (BASE / "summary").mkdir(parents=True, exist_ok=True)
    (BASE / "ci").mkdir(parents=True, exist_ok=True)

    per = load_per_sample()

    condition_summary = (
        per.groupby(["model_display", "method"])
        .agg(
            n=("sample_id", "count"),
            parse_errors=("parse_error", lambda s: s.notna().sum()),
            answer_f1_relaxed=("answer_f1_relaxed", "mean"),
            exact_match_relaxed=("exact_match_relaxed", "mean"),
            evidence_f1=("evidence_f1", "mean"),
        )
        .reset_index()
    )
    condition_summary.to_csv(BASE / "summary" / "twowiki_condition_summary.csv", index=False)

    rows: list[dict[str, object]] = []
    for model, df in per.groupby("model_display"):
        grouped = df.groupby(GROUP_COLS + ["method"])["answer_f1_relaxed"].mean().reset_index()
        pivot = grouped.pivot_table(index=GROUP_COLS, columns="method", values="answer_f1_relaxed")
        for method in ["direct", "retrieve_then_read"]:
            tmp = pivot[["no_evidence", "oracle", method]].dropna()
            tmp = tmp[tmp["oracle"] > tmp["no_evidence"]]
            raw = (tmp[method] - tmp["no_evidence"]) / (tmp["oracle"] - tmp["no_evidence"])
            clipped = raw.clip(0, 1)
            mean, low, high = bootstrap_mean(clipped.values)
            rows.append(
                {
                    "model": model,
                    "long_method": method,
                    "valid_groups": len(tmp),
                    "total_groups": len(pivot),
                    "S_no": tmp["no_evidence"].mean(),
                    "S_oracle": tmp["oracle"].mean(),
                    "S_long": tmp[method].mean(),
                    "oncu_clipped": mean,
                    "ci_low": low,
                    "ci_high": high,
                }
            )

    oncu = pd.DataFrame(rows)
    oncu.to_csv(BASE / "summary" / "twowiki_oncu_relaxed_f1_summary.csv", index=False)
    oncu[["model", "long_method", "oncu_clipped", "ci_low", "ci_high", "valid_groups", "total_groups"]].to_csv(
        BASE / "ci" / "twowiki_oncu_relaxed_f1_bootstrap_ci.csv", index=False
    )

    print(f"Wrote 2Wiki derived summaries under {BASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
