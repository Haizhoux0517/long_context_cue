from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.controlled_generator import ControlledCUEGenerator, controlled_summary
from longcue.data.io import save_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Controlled-CUE benchmark.")
    parser.add_argument("--output", default="data/processed/controlled_cue.jsonl")
    parser.add_argument("--num-per-cell", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    samples = ControlledCUEGenerator(
        num_per_cell=args.num_per_cell, seed=args.seed
    ).generate()
    output = save_samples(samples, args.output)
    print(f"Wrote {len(samples)} Controlled-CUE samples to {output}.")
    print(json.dumps(controlled_summary(samples), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
