from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.babilong_adapter import load_babilong_cue
from longcue.data.io import save_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BABILong CUE adapters from Hugging Face.")
    parser.add_argument("--output", default="data/processed/babilong_cue.jsonl")
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--limit-per-task", type=int, default=100)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    samples, stats = load_babilong_cue(
        args.configs,
        args.tasks,
        limit_per_task=args.limit_per_task,
        logger=logging.getLogger("longcue.babilong"),
    )
    output = save_samples(samples, args.output)
    print(f"Wrote {len(samples)} BABILong CUE samples to {output}.")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
