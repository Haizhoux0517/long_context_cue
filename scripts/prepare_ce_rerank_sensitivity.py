from __future__ import annotations

import argparse
from pathlib import Path
import yaml


DATASETS = {
    "hotpotqa200": {
        "dataset_name": "hotpotqa_oncu_200",
        "dataset_path": "/workspace/long_context_cue/data/processed/hotpotqa_cue_200.jsonl",
        "reference": {
            "qwen25": "/workspace/long_context_cue/experiment_backups/sci200_final_3model_20260525/hotpotqa_qwen25_14b_200_core_final/results/per_sample_metrics.csv",
            "qwen3": "/workspace/long_context_cue/experiment_backups/sci200_final_3model_20260525/hotpotqa_qwen3_14b_200_core_final/results/per_sample_metrics.csv",
            "gemma3": "/workspace/long_context_cue/experiment_backups/sci200_final_3model_20260525/hotpotqa_gemma3_12b_200_core_final/results/per_sample_metrics.csv",
            "llama31": "/workspace/long_context_cue/experiment_backups/model_family_extension_20260601/hotpotqa_200_llama31_8b/results/per_sample_metrics.csv",
            "mistral": "/workspace/long_context_cue/experiment_backups/model_family_extension_20260601/hotpotqa_200_mistral_small31_24b/results/per_sample_metrics.csv",
        },
    },
    "hotpotqa500": {
        "dataset_name": "hotpotqa_oncu_500",
        "dataset_path": "/workspace/long_context_cue/data/processed/hotpotqa_cue_500.jsonl",
        "reference": {
            "qwen25": "/workspace/long_context_cue/experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_qwen25_14b_500/results/per_sample_metrics.csv",
            "qwen3": "/workspace/long_context_cue/experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_qwen3_14b_500/results/per_sample_metrics.csv",
            "gemma3": "/workspace/long_context_cue/experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_gemma3_12b_500/results/per_sample_metrics.csv",
            "llama31": "",
            "mistral": "",
        },
    },
    "twowiki500": {
        "dataset_name": "twowiki_oncu_500",
        "dataset_path": "/workspace/long_context_cue/data/processed/twowiki_cue_500.jsonl",
        "reference": {
            "qwen25": "/workspace/long_context_cue/experiment_backups/twowiki_500_validation_20260527/per_model/qwen25/per_sample_metrics.csv",
            "qwen3": "/workspace/long_context_cue/experiment_backups/twowiki_500_validation_20260527/per_model/qwen3/per_sample_metrics.csv",
            "gemma3": "/workspace/long_context_cue/experiment_backups/twowiki_500_validation_20260527/per_model/gemma3/per_sample_metrics.csv",
            "llama31": "/workspace/long_context_cue/experiment_backups/model_family_extension_20260601/twowiki_500_llama31_8b/results/per_sample_metrics.csv",
            "mistral": "/workspace/long_context_cue/experiment_backups/model_family_extension_20260601/twowiki_500_mistral_small31_24b/results/per_sample_metrics.csv",
        },
    },
}


MODELS = {
    "qwen25": {
        "model_name": "qwen2.5:14b",
        "num_ctx": 32768,
        "timeout": 900,
    },
    "qwen3": {
        "model_name": "qwen3:14b",
        "num_ctx": 32768,
        "timeout": 900,
    },
    "gemma3": {
        "model_name": "gemma3:12b",
        "num_ctx": 32768,
        "timeout": 900,
    },
    "llama31": {
        "model_name": "llama3.1:8b",
        "num_ctx": 32768,
        "timeout": 900,
    },
    "mistral": {
        "model_name": "mistral-small3.1:24b",
        "num_ctx": 32768,
        "timeout": 1200,
    },
}


CONDITIONS = [
    ("hybrid_ce32", 8),
    ("hybrid_ce32", 16),
    ("hybrid_ce64", 8),
    ("hybrid_ce64", 16),
    ("hybrid_ce64", 24),
    ("hybrid_ce128", 16),
    ("hybrid_ce128", 24),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="configs/rerank_sensitivity/ce_reader_facing")
    parser.add_argument("--run-root", default="/workspace/long_context_cue/outputs/rerank_sensitivity_20260602/ce_reader_facing")
    parser.add_argument("--strict-reference", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    skipped = []

    for dataset_key, dataset in DATASETS.items():
        dataset_path = Path(dataset["dataset_path"])
        if not dataset_path.exists():
            skipped.append((dataset_key, "*", "*", "missing dataset_path", str(dataset_path)))
            continue

        for model_key, model in MODELS.items():
            ref_path_str = dataset["reference"].get(model_key, "")
            ref_path = Path(ref_path_str) if ref_path_str else None

            if not ref_path or not ref_path.exists():
                msg = "missing reference_metrics_path"
                skipped.append((dataset_key, model_key, "*", msg, ref_path_str))
                if args.strict_reference:
                    continue

            for retriever, top_k in CONDITIONS:
                name = f"{dataset_key}_{model_key}_{retriever}_k{top_k}"
                cfg = {
                    "dataset_name": dataset["dataset_name"],
                    "dataset_path": str(dataset_path),
                    "output_dir": f"{args.run_root}/{name}",
                    "reference_metrics_path": str(ref_path) if ref_path and ref_path.exists() else "",
                    "model": {
                        "provider": "ollama",
                        "model_name": model["model_name"],
                        "num_ctx": model["num_ctx"],
                        "timeout": model["timeout"],
                    },
                    "generation": {
                        "max_tokens": 1024,
                        "temperature": 0.0,
                    },
                    "retriever_family": {
                        "retrievers": [retriever],
                        "top_k": [top_k],
                        "reader_retrievers": [retriever],
                        "reader_top_k": [top_k],
                        "chunk_size": 220,
                        "overlap": 40,
                        "dense_model_name": "sentence-transformers/all-MiniLM-L6-v2",
                        "rrf_k": 60,
                        "ce_rerank_model_name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                        "ce_rerank_batch_size": 32,
                        "ce_rerank_device": "auto",
                    },
                    "logging": {
                        "save_full_prompts": False,
                    },
                    "protocol": {
                        "purpose": "ce_rerank_sensitivity",
                        "retrieved_condition_variant": f"{retriever}@{top_k}",
                        "first_stage_family": "hybrid",
                        "first_stage_candidate_k": int(retriever.replace("hybrid_ce", "")),
                        "final_top_k": top_k,
                        "reranker": "cross-encoder/ms-marco-MiniLM-L6-v2",
                    },
                }

                path = out_dir / f"{name}.yaml"
                path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
                written.append(path)

    manifest = out_dir / "CONFIG_MANIFEST.txt"
    with manifest.open("w", encoding="utf-8") as f:
        f.write(f"written={len(written)}\n")
        for path in written:
            f.write(f"WRITE {path}\n")
        f.write(f"skipped={len(skipped)}\n")
        for row in skipped:
            f.write("SKIP " + "\t".join(map(str, row)) + "\n")

    print(f"Wrote {len(written)} configs to {out_dir}")
    print(f"Skipped {len(skipped)} entries")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
