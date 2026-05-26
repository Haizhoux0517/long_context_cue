from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.io import save_samples
from longcue.data.twowiki_adapter import (
    DEFAULT_TWOWIKI_DATASET,
    load_2wikimultihopqa_cue,
    load_2wikimultihopqa_cue_from_path,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build 2WikiMultiHopQA-ONCU from Hugging Face or local JSON/JSONL files.")
    parser.add_argument("--output", default="data/processed/twowiki_cue_500.jsonl")
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--context-lengths", type=int, nargs="+", default=[4000, 8000, 16000])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dataset-name", default=DEFAULT_TWOWIKI_DATASET)
    parser.add_argument("--input", help="Optional local JSON/JSONL file or directory. If set, Hugging Face loading is skipped.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logger = logging.getLogger("longcue.2wikimultihopqa")

    if args.input:
        samples, stats = load_2wikimultihopqa_cue_from_path(
            args.input,
            limit=args.limit,
            context_lengths=args.context_lengths,
            seed=args.seed,
            logger=logger,
        )
    else:
        samples, stats = load_2wikimultihopqa_cue(
            split=args.split,
            limit=args.limit,
            context_lengths=args.context_lengths,
            seed=args.seed,
            dataset_name=args.dataset_name,
            logger=logger,
        )

    output = save_samples(samples, args.output)
    stats_path = Path(args.output).with_suffix(".skipped.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(samples)} 2WikiMultiHopQA-ONCU samples to {output}.")
    print(f"Saved skipped-sample statistics to {stats_path}.")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
