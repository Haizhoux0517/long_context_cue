from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.generator import ControlledBenchmarkGenerator
from longcue.data.io import save_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the deterministic demo benchmark.")
    parser.add_argument("--count", type=int, default=100, help="Number of samples.")
    parser.add_argument("--seed", type=int, default=13, help="Deterministic random seed.")
    parser.add_argument(
        "--output",
        default="data/processed/controlled_benchmark.jsonl",
        help="Output JSONL path.",
    )
    args = parser.parse_args()
    output_path = save_samples(
        ControlledBenchmarkGenerator(sample_count=args.count, seed=args.seed).generate(),
        Path(args.output),
    )
    print(f"Wrote {args.count} samples to {output_path}.")


if __name__ == "__main__":
    main()
