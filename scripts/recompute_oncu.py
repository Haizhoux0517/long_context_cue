from __future__ import annotations

"""Recompute ONCU from an existing per_sample_metrics.csv.

This script wraps the legacy CUE implementation and writes ONCU aliases
(`oncu_valid`, `oncu_raw`, `oncu_clipped`, etc.) alongside the legacy column
names. The formula is identical; the terminology is changed to emphasize the
oracle-normalized diagnostic protocol rather than prompt optimization.
"""

import argparse
from pathlib import Path

import pandas as pd

from recompute_cue import recompute_cue


ALIASES = {
    "cue_valid": "oncu_valid",
    "cue_invalid_reason": "oncu_invalid_reason",
    "cue_raw": "oncu_raw",
    "cue_clipped": "oncu_clipped",
    "cue_clipped_mean": "oncu_clipped_mean",
    "cue_raw_mean": "oncu_raw_mean",
}


def _add_aliases(path: Path) -> None:
    if path is None or not path.exists():
        return
    df = pd.read_csv(path)
    for old, new in ALIASES.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]
    df.to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recompute multi-score Oracle-Normalized Context Utilization from per_sample_metrics.csv."
    )
    parser.add_argument("--metrics", required=True, help="Path to per_sample_metrics.csv")
    parser.add_argument("--output", required=True, help="Output ONCU row CSV path")
    parser.add_argument("--aggregate", default=None, help="Optional aggregate summary CSV")
    parser.add_argument("--markdown", default=None, help="Optional aggregate markdown table")
    args = parser.parse_args()

    output_path = Path(args.output)
    aggregate_path = Path(args.aggregate) if args.aggregate else None
    markdown_path = Path(args.markdown) if args.markdown else None

    recompute_cue(
        metrics_path=Path(args.metrics),
        output_path=output_path,
        aggregate_path=aggregate_path,
        markdown_path=markdown_path,
    )
    _add_aliases(output_path)
    if aggregate_path is not None:
        _add_aliases(aggregate_path)
    print("Wrote ONCU-compatible outputs. Legacy cue_* columns are retained for backward compatibility.")


if __name__ == "__main__":
    main()
