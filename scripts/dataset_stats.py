from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from longcue.data.io import load_samples
from longcue.data.stats import dataset_stats, write_dataset_stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute CUE JSONL dataset statistics.")
    parser.add_argument("dataset_path")
    parser.add_argument("--output-dir", default="outputs/dataset_stats")
    args = parser.parse_args()
    report = dataset_stats(load_samples(args.dataset_path))
    artifacts = write_dataset_stats(
        report, dataset_path=args.dataset_path, output_dir=args.output_dir
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"CSV: {artifacts['csv']}")
    print(f"Markdown: {artifacts['markdown']}")


if __name__ == "__main__":
    main()
