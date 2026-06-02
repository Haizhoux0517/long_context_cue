#!/usr/bin/env python3
"""Create four-condition retriever-family ONCU sensitivity configs.

The core ONCU protocol already supports replacing the retrieved-evidence
condition by setting retrieval.retriever and retrieval.top_k in a normal
longcue/run_experiment.py YAML config.  This helper materializes those configs
so that dense@16 and hybrid@16 retrieved-evidence inputs can be evaluated under
the same no-evidence, full-context, retrieved-evidence, and oracle-reference
conditions as the main ONCU runs.

The generated runs are sensitivity analyses, not new benchmarks: no-evidence,
full-context, and oracle-evidence references remain matched to the same model
and dataset, while only the retrieved-evidence input family changes.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import yaml

TEMPLATE_CONFIGS = {
    "hotpotqa200_qwen25": "configs/hotpotqa_qwen25_14b_200_core_final.yaml",
    "hotpotqa200_qwen3": "configs/hotpotqa_qwen3_14b_200_core_final.yaml",
    "hotpotqa200_gemma3": "configs/hotpotqa_gemma3_12b_200_core_final.yaml",
    "twowiki500_qwen25": "configs/twowiki_qwen25_14b_500_core.yaml",
    "twowiki500_qwen3": "configs/twowiki_qwen3_14b_500_core.yaml",
    "twowiki500_gemma3": "configs/twowiki_gemma3_12b_500_core.yaml",
}

DEFAULT_RETRIEVERS = ("dense", "hybrid")
DEFAULT_TOP_K = 16


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="configs/retriever_family_oncu_sensitivity")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--retrievers",
        nargs="+",
        default=list(DEFAULT_RETRIEVERS),
        help="Retrieved-evidence retriever families to instantiate.",
    )
    parser.add_argument(
        "--template",
        action="append",
        default=[],
        help="Optional template key to include. Defaults to all known templates.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = args.template or sorted(TEMPLATE_CONFIGS)
    written = []
    for key in selected:
        if key not in TEMPLATE_CONFIGS:
            raise KeyError(f"Unknown template key: {key}. Available: {sorted(TEMPLATE_CONFIGS)}")
        template_path = repo_root / TEMPLATE_CONFIGS[key]
        config = _load_yaml(template_path)
        for retriever in args.retrievers:
            new_config = copy.deepcopy(config)
            new_config["methods"] = ["no_evidence", "direct", "retrieve_then_read", "oracle"]
            retrieval = dict(new_config.get("retrieval", {}))
            retrieval["retriever"] = str(retriever)
            retrieval["top_k"] = int(args.top_k)
            retrieval.setdefault("chunk_size", 220)
            retrieval.setdefault("overlap", 40)
            retrieval.setdefault("dense_model_name", "sentence-transformers/all-MiniLM-L6-v2")
            retrieval.setdefault("rrf_k", 60)
            new_config["retrieval"] = retrieval
            new_config.setdefault("protocol", {})["purpose"] = "retriever_family_oncu_sensitivity"
            new_config.setdefault("protocol", {})["retrieved_condition_variant"] = f"{retriever}@{args.top_k}"
            output_name = f"{key}_{retriever}_k{args.top_k}"
            new_config["output_dir"] = f"outputs/retriever_family_oncu_sensitivity/{output_name}"
            target = out_dir / f"{output_name}.yaml"
            target.write_text(yaml.safe_dump(new_config, sort_keys=False), encoding="utf-8")
            written.append(target)

    print(f"Wrote {len(written)} configs under {out_dir}")
    for path in written:
        print(path.relative_to(repo_root))


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


if __name__ == "__main__":
    main()
