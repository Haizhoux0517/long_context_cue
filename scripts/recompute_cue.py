from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SCORE_FIELDS = [
    "exact_match_strict",
    "answer_f1_strict",
    "exact_match_relaxed",
    "answer_f1_relaxed",
]

LEGACY_SCORE_FIELDS = {
    "exact_match": "exact_match",
    "answer_f1": "answer_f1",
}

DEFAULT_GROUP_COLS = [
    "source",
    "model_name",
    "reasoning_type",
    "context_length",
    "evidence_position",
    "evidence_density",
    "distractor_similarity",
]


BASE_METHOD_NO = "no_evidence"
BASE_METHOD_ORACLE = "oracle"


def _available_score_fields(df: pd.DataFrame) -> list[str]:
    fields = [col for col in DEFAULT_SCORE_FIELDS if col in df.columns]

    # Backward compatibility for older runs.
    for col in LEGACY_SCORE_FIELDS:
        if col in df.columns and col not in fields:
            fields.append(col)

    if not fields:
        raise ValueError(
            "No supported score fields found. Expected one of: "
            + ", ".join(DEFAULT_SCORE_FIELDS + list(LEGACY_SCORE_FIELDS))
        )
    return fields


def _available_group_cols(df: pd.DataFrame) -> list[str]:
    return [col for col in DEFAULT_GROUP_COLS if col in df.columns]


def recompute_cue(
    metrics_path: Path,
    output_path: Path,
    aggregate_path: Path | None = None,
    markdown_path: Path | None = None,
) -> pd.DataFrame:
    df = pd.read_csv(metrics_path)

    if "method" not in df.columns:
        raise ValueError("Input metrics CSV must contain a 'method' column.")

    if "cue_applicable" in df.columns:
        df = df[df["cue_applicable"].astype(str).str.lower().isin(["true", "1", "yes"])]

    score_fields = _available_score_fields(df)
    group_cols = _available_group_cols(df)

    # Avoid NaN causing groupby drops.
    for col in group_cols:
        df[col] = df[col].fillna("unknown")

    long_methods = sorted(
        method
        for method in df["method"].dropna().unique()
        if method not in {BASE_METHOD_NO, BASE_METHOD_ORACLE}
    )

    rows: list[dict] = []

    grouped = df.groupby(group_cols, dropna=False) if group_cols else [((), df)]

    for group_key, group_df in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        group_meta = dict(zip(group_cols, group_key))

        no_df = group_df[group_df["method"] == BASE_METHOD_NO]
        oracle_df = group_df[group_df["method"] == BASE_METHOD_ORACLE]

        if no_df.empty or oracle_df.empty:
            for long_method in long_methods:
                for score_field in score_fields:
                    rows.append(
                        {
                            **group_meta,
                            "long_method": long_method,
                            "score_field": score_field,
                            "score_no_evidence": None,
                            "score_oracle": None,
                            "score_long": None,
                            "n": len(group_df),
                            "cue_valid": False,
                            "cue_invalid_reason": "missing_no_or_oracle",
                            "cue_raw": None,
                            "cue_clipped": None,
                        }
                    )
            continue

        for score_field in score_fields:
            no_score = pd.to_numeric(no_df[score_field], errors="coerce").mean()
            oracle_score = pd.to_numeric(oracle_df[score_field], errors="coerce").mean()

            for long_method in long_methods:
                long_df = group_df[group_df["method"] == long_method]

                if long_df.empty:
                    rows.append(
                        {
                            **group_meta,
                            "long_method": long_method,
                            "score_field": score_field,
                            "score_no_evidence": no_score,
                            "score_oracle": oracle_score,
                            "score_long": None,
                            "n": len(group_df),
                            "cue_valid": False,
                            "cue_invalid_reason": "missing_long_method",
                            "cue_raw": None,
                            "cue_clipped": None,
                        }
                    )
                    continue

                long_score = pd.to_numeric(long_df[score_field], errors="coerce").mean()

                invalid_reason = ""
                cue_raw = None
                cue_clipped = None
                cue_valid = True

                if pd.isna(no_score) or pd.isna(oracle_score) or pd.isna(long_score):
                    cue_valid = False
                    invalid_reason = "nan_score"
                elif oracle_score <= no_score:
                    cue_valid = False
                    invalid_reason = "oracle_not_above_no_evidence"
                else:
                    cue_raw = (long_score - no_score) / (oracle_score - no_score)
                    cue_clipped = max(0.0, min(1.0, cue_raw))

                rows.append(
                    {
                        **group_meta,
                        "long_method": long_method,
                        "score_field": score_field,
                        "score_no_evidence": no_score,
                        "score_oracle": oracle_score,
                        "score_long": long_score,
                        "n": len(group_df),
                        "cue_valid": cue_valid,
                        "cue_invalid_reason": invalid_reason if not cue_valid else "",
                        "cue_raw": cue_raw,
                        "cue_clipped": cue_clipped,
                    }
                )

    cue = pd.DataFrame(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cue.to_csv(output_path, index=False)

    if aggregate_path is not None:
        valid = cue[cue["cue_valid"] == True].copy()
        if valid.empty:
            summary = pd.DataFrame()
        else:
            summary = (
                valid.groupby(["long_method", "score_field"])
                .agg(
                    valid_groups=("cue_clipped", "count"),
                    cue_clipped_mean=("cue_clipped", "mean"),
                    cue_raw_mean=("cue_raw", "mean"),
                    score_no_evidence_mean=("score_no_evidence", "mean"),
                    score_oracle_mean=("score_oracle", "mean"),
                    score_long_mean=("score_long", "mean"),
                )
                .reset_index()
                .sort_values(["score_field", "cue_clipped_mean"], ascending=[True, False])
            )

        aggregate_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(aggregate_path, index=False)

        if markdown_path is not None:
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            markdown_path.write_text(summary.to_markdown(index=False), encoding="utf-8")

    print(f"Wrote CUE rows to {output_path}")
    if aggregate_path is not None:
        print(f"Wrote CUE summary to {aggregate_path}")
    if markdown_path is not None:
        print(f"Wrote CUE markdown to {markdown_path}")

    return cue


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recompute multi-score CUE from per_sample_metrics.csv."
    )
    parser.add_argument("--metrics", required=True, help="Path to per_sample_metrics.csv")
    parser.add_argument("--output", required=True, help="Output cue_metrics CSV path")
    parser.add_argument("--aggregate", default=None, help="Optional aggregate summary CSV")
    parser.add_argument("--markdown", default=None, help="Optional aggregate markdown table")
    args = parser.parse_args()

    recompute_cue(
        metrics_path=Path(args.metrics),
        output_path=Path(args.output),
        aggregate_path=Path(args.aggregate) if args.aggregate else None,
        markdown_path=Path(args.markdown) if args.markdown else None,
    )


if __name__ == "__main__":
    main()
