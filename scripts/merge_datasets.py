from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.merge import merge_dataset_paths
from longcue.data.stats import dataset_stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge CUE JSONL datasets with schema validation.")
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    samples, merge_summary = merge_dataset_paths(args.inputs, args.output)
    print(f"Wrote {len(samples)} merged CUE samples to {args.output}.")
    print(json.dumps({"merge": merge_summary, "dataset": dataset_stats(samples)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
