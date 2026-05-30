#!/usr/bin/env python3
"""Build a decile-position controlled scaling dataset for ONCU diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.controlled_generator import (  # noqa: E402
    CONTROLLED_CONTEXT_LENGTHS,
    CONTROLLED_DECILE_EVIDENCE_POSITIONS,
    CONTROLLED_DISTRACTOR_SIMILARITIES,
    CONTROLLED_REASONING_TYPES,
    ControlledCUEGenerator,
    controlled_summary,
)
from longcue.data.io import save_samples  # noqa: E402


def _parse_ints(text: str | None, default: tuple[int, ...]) -> tuple[int, ...]:
    if not text:
        return default
    values = tuple(int(item.strip()) for item in text.split(",") if item.strip())
    if not values:
        raise ValueError("At least one context length is required.")
    return values


def _parse_strings(text: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not text:
        return default
    values = tuple(item.strip() for item in text.split(",") if item.strip())
    if not values:
        raise ValueError("At least one value is required.")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a controlled scaling dataset that places evidence in ten "
            "decile buckets across 4K/8K/16K/32K contexts."
        )
    )
    parser.add_argument("--output", default="data/processed/controlled_scaling_3200.jsonl")
    parser.add_argument(
        "--num-per-cell",
        type=int,
        default=5,
        help="Replicates per length x position x distractor x reasoning cell. Default: 5.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--context-lengths",
        default=None,
        help="Comma-separated context lengths. Default: 4000,8000,16000,32000.",
    )
    parser.add_argument(
        "--positions",
        default=None,
        help="Comma-separated evidence-position labels. Default: pos_00,...,pos_09.",
    )
    parser.add_argument(
        "--distractor-similarities",
        default=None,
        help="Comma-separated distractor settings. Default: none,low,high,conflicting.",
    )
    parser.add_argument(
        "--reasoning-types",
        default=None,
        help="Comma-separated reasoning types. Default: single_hop,multi_hop,comparison,arithmetic.",
    )
    args = parser.parse_args()

    samples = ControlledCUEGenerator(
        num_per_cell=args.num_per_cell,
        seed=args.seed,
        context_lengths=_parse_ints(args.context_lengths, CONTROLLED_CONTEXT_LENGTHS),
        evidence_positions=_parse_strings(args.positions, CONTROLLED_DECILE_EVIDENCE_POSITIONS),
        distractor_similarities=_parse_strings(
            args.distractor_similarities,
            CONTROLLED_DISTRACTOR_SIMILARITIES,
        ),
        reasoning_types=_parse_strings(args.reasoning_types, CONTROLLED_REASONING_TYPES),
    ).generate()
    output = save_samples(samples, args.output)
    summary = controlled_summary(samples)
    summary.update(
        {
            "builder": "build_controlled_scaling_cue.py",
            "num_per_cell": args.num_per_cell,
            "seed": args.seed,
            "position_scheme": "decile_midpoints",
        }
    )
    print(f"Wrote {len(samples)} controlled scaling samples to {output}.")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
