#!/usr/bin/env python3
"""Build a lightweight RULER-style external validation set.

This script intentionally does NOT build ONCU examples.  It creates an
external answer-performance validation set inspired by RULER-style long-context
tasks: retrieval, multi-hop tracing, and aggregation.

Default output:
    data/processed/ruler_lite_240.jsonl

Each row contains:
    sample_id, dataset_name, task_name, context_length, evidence_position,
    question, context, gold_answer, answer_type, metadata

The generated benchmark is synthetic, deterministic under --seed, and designed
for reviewer-facing external generalization checks rather than oracle-normalized
ONCU computation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import string
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_LENGTHS = [4000, 8000, 16000, 32000]
DEFAULT_TASKS = ["retrieval_key_value", "multi_hop_trace", "aggregation_sum"]
DEFAULT_POSITIONS = ["early", "middle", "late"]


FILLER_VOCAB = [
    "archive", "benchmark", "catalog", "document", "evidence", "filter",
    "index", "journal", "ledger", "matrix", "notebook", "observation",
    "protocol", "query", "registry", "sample", "table", "update",
    "validation", "workflow", "analysis", "baseline", "context", "dataset",
    "experiment", "feature", "group", "hypothesis", "iteration", "kernel",
    "label", "metric", "normalization", "oracle", "passage", "record",
    "summary", "token", "utility", "variable", "window", "zone",
]


def _stable_code(prefix: str, rng: random.Random, digits: int = 5) -> str:
    return f"{prefix}{rng.randint(0, 10 ** digits - 1):0{digits}d}"


def _hash_id(*parts: object, n: int = 12) -> str:
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:n]


def _filler_sentence(rng: random.Random, idx: int) -> str:
    words = rng.choices(FILLER_VOCAB, k=rng.randint(18, 30))
    serial = f"FILLER-{idx:05d}-{rng.randint(0, 9999):04d}"
    return (
        f"[passage_id: f{idx:05d}] "
        f"The unrelated note {serial} contains " + " ".join(words) + "."
    )


def _make_filler_paragraphs(rng: random.Random, count: int, start_idx: int = 0) -> List[str]:
    return [_filler_sentence(rng, start_idx + i) for i in range(count)]


def _target_filler_count(context_length: int, evidence_paragraph_count: int) -> int:
    # Approximate 35-45 words per filler paragraph.  We target a conservative
    # word budget so prompts remain inside a 32K Ollama context after adding
    # task instructions and JSON-output constraints.
    target_words = max(250, int(context_length * 0.62))
    return max(4, target_words // 38 - evidence_paragraph_count)


def _insert_evidence(
    filler: List[str],
    evidence: List[str],
    position: str,
) -> List[str]:
    if position == "early":
        idx = max(1, int(0.10 * len(filler)))
    elif position == "middle":
        idx = max(1, int(0.50 * len(filler)))
    elif position == "late":
        idx = max(1, int(0.90 * len(filler)))
    else:
        raise ValueError(f"Unsupported evidence position: {position}")
    return filler[:idx] + evidence + filler[idx:]


def _build_retrieval_key_value(
    rng: random.Random,
    sample_seed: int,
) -> Tuple[str, List[str], str, Dict[str, object]]:
    entity = _stable_code("ENTITY-", rng, 4)
    answer = _stable_code("CODE-", rng, 5)
    decoy_entity = _stable_code("ENTITY-", rng, 4)
    decoy_answer = _stable_code("CODE-", rng, 5)

    question = f"What is the access code for {entity}? Answer with the code only."
    evidence = [
        f"[passage_id: e0001] The access code for {entity} is {answer}. "
        f"This record is authoritative for the requested entity.",
        f"[passage_id: d0001] The access code for {decoy_entity} is {decoy_answer}. "
        f"This nearby distractor concerns a different entity.",
    ]
    meta = {
        "task_category": "retrieval",
        "gold_evidence_ids": ["e0001"],
        "distractor_ids": ["d0001"],
        "sample_seed": sample_seed,
    }
    return question, evidence, answer, meta


def _build_multi_hop_trace(
    rng: random.Random,
    sample_seed: int,
) -> Tuple[str, List[str], str, Dict[str, object]]:
    start = _stable_code("NODE-", rng, 4)
    mid1 = _stable_code("NODE-", rng, 4)
    mid2 = _stable_code("NODE-", rng, 4)
    final = _stable_code("VALUE-", rng, 5)

    # Add a plausible distractor chain starting with a similar-looking node.
    distractor_start = start[:-1] + str((int(start[-1]) + 1) % 10)
    distractor_mid = _stable_code("NODE-", rng, 4)
    distractor_final = _stable_code("VALUE-", rng, 5)

    question = (
        f"Following the routing table starting from {start}, what final value "
        f"do you reach after all listed hops? Answer with the final value only."
    )
    evidence = [
        f"[passage_id: e0001] In the routing table, {start} points to {mid1}.",
        f"[passage_id: e0002] In the routing table, {mid1} points to {mid2}.",
        f"[passage_id: e0003] In the routing table, {mid2} resolves to {final}.",
        f"[passage_id: d0001] In the routing table, {distractor_start} points to {distractor_mid}.",
        f"[passage_id: d0002] In the routing table, {distractor_mid} resolves to {distractor_final}.",
    ]
    meta = {
        "task_category": "multi_hop_tracing",
        "gold_evidence_ids": ["e0001", "e0002", "e0003"],
        "distractor_ids": ["d0001", "d0002"],
        "sample_seed": sample_seed,
    }
    return question, evidence, final, meta


def _build_aggregation_sum(
    rng: random.Random,
    sample_seed: int,
) -> Tuple[str, List[str], str, Dict[str, object]]:
    target_group = _stable_code("GROUP-", rng, 3)
    decoy_group = _stable_code("GROUP-", rng, 3)
    while decoy_group == target_group:
        decoy_group = _stable_code("GROUP-", rng, 3)

    values = [rng.randint(11, 97) for _ in range(4)]
    decoys = [rng.randint(11, 97) for _ in range(4)]
    answer = str(sum(values))

    target_records = [
        f"record {i+1}: group={target_group}, amount={v}" for i, v in enumerate(values)
    ]
    decoy_records = [
        f"record {i+1}: group={decoy_group}, amount={v}" for i, v in enumerate(decoys)
    ]

    all_records = target_records + decoy_records
    rng.shuffle(all_records)

    question = (
        f"What is the sum of all amounts for {target_group}? "
        f"Answer with the number only."
    )
    evidence = [
        "[passage_id: e0001] Aggregation ledger: " + "; ".join(all_records) + "."
    ]
    meta = {
        "task_category": "aggregation",
        "gold_evidence_ids": ["e0001"],
        "target_group": target_group,
        "target_values": values,
        "sample_seed": sample_seed,
    }
    return question, evidence, answer, meta


TASK_BUILDERS = {
    "retrieval_key_value": _build_retrieval_key_value,
    "multi_hop_trace": _build_multi_hop_trace,
    "aggregation_sum": _build_aggregation_sum,
}


def build_samples(
    *,
    context_lengths: List[int],
    tasks: List[str],
    positions: List[str],
    samples_per_cell: int,
    seed: int,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    global_idx = 0

    for context_length in context_lengths:
        for task_name in tasks:
            if task_name not in TASK_BUILDERS:
                raise ValueError(f"Unknown task_name={task_name}. Known: {sorted(TASK_BUILDERS)}")
            for i in range(samples_per_cell):
                position = positions[i % len(positions)]
                sample_seed = seed * 1_000_003 + context_length * 101 + i * 17 + len(task_name)
                rng = random.Random(sample_seed)

                question, evidence, answer, meta = TASK_BUILDERS[task_name](rng, sample_seed)
                filler_count = _target_filler_count(context_length, len(evidence))
                filler = _make_filler_paragraphs(rng, filler_count, start_idx=global_idx * 1000)
                context_paragraphs = _insert_evidence(filler, evidence, position)
                context = "\n\n".join(context_paragraphs)

                sample_id = f"ruler_lite_{global_idx + 1:06d}"
                row = {
                    "sample_id": sample_id,
                    "dataset_name": "ruler_lite_external",
                    "task_name": task_name,
                    "task_category": meta["task_category"],
                    "context_length": context_length,
                    "evidence_position": position,
                    "question": question,
                    "context": context,
                    "gold_answer": answer,
                    "answer_type": "string" if not answer.isdigit() else "number",
                    "metadata": meta,
                }
                rows.append(row)
                global_idx += 1

    return rows


def write_jsonl(rows: Iterable[Dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/processed/ruler_lite_240.jsonl"))
    parser.add_argument("--samples-per-cell", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--context-lengths", type=int, nargs="+", default=DEFAULT_LENGTHS)
    parser.add_argument("--tasks", nargs="+", default=DEFAULT_TASKS)
    parser.add_argument("--positions", nargs="+", default=DEFAULT_POSITIONS)
    args = parser.parse_args()

    rows = build_samples(
        context_lengths=args.context_lengths,
        tasks=args.tasks,
        positions=args.positions,
        samples_per_cell=args.samples_per_cell,
        seed=args.seed,
    )
    write_jsonl(rows, args.output)

    manifest = {
        "dataset_name": "ruler_lite_external",
        "output": str(args.output),
        "num_samples": len(rows),
        "context_lengths": args.context_lengths,
        "tasks": args.tasks,
        "positions": args.positions,
        "samples_per_cell": args.samples_per_cell,
        "seed": args.seed,
        "role": "External answer-performance validation; not ONCU.",
    }
    manifest_path = args.output.with_suffix(args.output.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {len(rows)} RULER-lite samples to {args.output}")
    print(f"Wrote manifest to {manifest_path}")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
