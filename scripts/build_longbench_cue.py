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
from longcue.data.longbench_adapter import load_longbench_cue


def main() -> None:
    parser = argparse.ArgumentParser(description="Build LongBench CUE adapters from Hugging Face.")
    parser.add_argument("--output", default="data/processed/longbench_cue.jsonl")
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--limit-per-task", type=int, default=100)
    parser.add_argument("--split", default="test")
    parser.add_argument(
        "--local-dir",
        help="Optional LongBench directory containing <task>.jsonl or <task>.json files.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    logger = logging.getLogger("longcue.longbench")
    samples, stats = load_longbench_cue(
        args.tasks,
        limit_per_task=args.limit_per_task,
        split=args.split,
        local_dir=args.local_dir,
        logger=logger,
    )
    if not samples:
        logger.warning(
            "LongBench conversion produced 0 samples. Place task JSONL files under data/raw/LongBench and rerun with --local-dir data/raw/LongBench if online loading is unavailable."
        )
    output = save_samples(samples, args.output)
    print(f"Wrote {len(samples)} LongBench CUE samples to {output}.")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
