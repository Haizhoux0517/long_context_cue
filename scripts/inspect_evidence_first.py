from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.io import load_samples
from longcue.evaluation.answer_metrics import (
    exact_match,
    exact_match_relaxed,
    token_f1,
    token_f1_relaxed,
)

DEFAULT_METHODS = ("evidence_first", "evidence_first_verify")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Evidence-First experiment traces.")
    parser.add_argument("--dataset", required=True, help="Dataset JSONL used for the run.")
    parser.add_argument(
        "--raw",
        required=True,
        help="raw_model_responses.jsonl or raw_model_responses.jsonl.gz from a run.",
    )
    parser.add_argument("--sample-ids", nargs="*", default=[])
    parser.add_argument("--methods", nargs="*", default=list(DEFAULT_METHODS))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    samples = {sample.id: sample for sample in load_samples(args.dataset)}
    requested_ids = set(args.sample_ids)
    printed = 0
    for record in _load_records(args.raw):
        sample_id = str(record.get("sample_id", ""))
        if str(record.get("method", "")) not in set(args.methods):
            continue
        if requested_ids and sample_id not in requested_ids:
            continue
        sample = samples.get(sample_id)
        if sample is None:
            continue
        _print_trace(sample, record)
        printed += 1
        if args.limit > 0 and printed >= args.limit:
            break
    print(f"Printed {printed} Evidence-First traces.")


def _print_trace(sample: Any, record: dict[str, Any]) -> None:
    intermediate = record.get("intermediate", {})
    prediction = record.get("prediction", {})
    final_answer = str(intermediate.get("final_answer") or prediction.get("answer", ""))
    selected_ids = intermediate.get("selected_evidence_ids") or _selected_ids(intermediate)
    evidence_summary = str(
        intermediate.get("evidence_summary")
        or intermediate.get("compression", {}).get("evidence_summary", "")
    )
    print("=" * 88)
    print(f"sample_id: {sample.id}")
    print(f"method: {record.get('method', '')}")
    print(f"question: {sample.question}")
    print(f"gold_answer: {sample.gold_answer}")
    print("oracle_evidence:")
    for evidence in sample.oracle_evidence:
        print(f"  {evidence.evidence_id}: {evidence.text}")
    if not sample.oracle_evidence:
        print("  (none)")
    print(f"selected_evidence_ids: {selected_ids}")
    print(f"evidence_summary: {evidence_summary}")
    print(f"final_answer: {final_answer}")
    print(
        "strict_scores: "
        f"exact={exact_match(final_answer, sample.gold_answer):.3f} "
        f"f1={token_f1(final_answer, sample.gold_answer):.3f}"
    )
    print(
        "relaxed_scores: "
        f"exact={exact_match_relaxed(final_answer, sample.gold_answer, answer_type=sample.answer_type, reasoning_type=sample.reasoning_type):.3f} "
        f"f1={token_f1_relaxed(final_answer, sample.gold_answer, answer_type=sample.answer_type, reasoning_type=sample.reasoning_type):.3f}"
    )
    verification = intermediate.get("verification_result")
    if verification is not None:
        print(f"verification_result: {json.dumps(verification, ensure_ascii=False)}")


def _selected_ids(intermediate: dict[str, Any]) -> list[str]:
    selected = intermediate.get("extraction", {}).get("selected_evidence", [])
    return [
        str(item.get("evidence_id", ""))
        for item in selected
        if isinstance(item, dict) and item.get("evidence_id")
    ]


def _load_records(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    records: list[dict[str, Any]] = []
    handle_context = (
        gzip.open(input_path, "rt", encoding="utf-8")
        if input_path.suffix == ".gz"
        else input_path.open("r", encoding="utf-8")
    )
    with handle_context as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    records.append(payload)
    return records


if __name__ == "__main__":
    main()
