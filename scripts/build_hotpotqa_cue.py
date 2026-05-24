from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.hotpotqa_adapter import load_hotpotqa_cue
from longcue.data.io import save_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Build HotpotQA-CUE from Hugging Face.")
    parser.add_argument("--output", default="data/processed/hotpotqa_cue.jsonl")
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--context-lengths", type=int, nargs="+", default=[4000, 8000, 16000])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logger = logging.getLogger("longcue.hotpotqa")
    samples, stats = load_hotpotqa_cue(
        split=args.split,
        limit=args.limit,
        context_lengths=args.context_lengths,
        seed=args.seed,
        logger=logger,
    )
    output = save_samples(samples, args.output)
    stats_path = Path(args.output).with_suffix(".skipped.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(samples)} HotpotQA-CUE samples to {output}.")
    print(f"Saved skipped-sample statistics to {stats_path}.")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
