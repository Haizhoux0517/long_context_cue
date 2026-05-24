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
from longcue.data.ruler_adapter import convert_ruler_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert local RULER records to CUE JSONL.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="data/processed/ruler_cue.jsonl")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    samples, stats = convert_ruler_path(args.input, logging.getLogger("longcue.ruler"))
    output = save_samples(samples, args.output)
    print(f"Wrote {len(samples)} RULER CUE samples to {output}.")
    print(json.dumps(stats, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
