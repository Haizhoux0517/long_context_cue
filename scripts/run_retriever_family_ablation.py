from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from statistics import mean
from typing import Any

import yaml

from longcue.data.io import load_samples, save_jsonl
from longcue.evaluation.answer_metrics import (
    exact_match,
    exact_match_relaxed,
    token_f1,
    token_f1_relaxed,
)
from longcue.evaluation.cue import compute_cue_rows
from longcue.evaluation.evidence_metrics import citation_grounding, evidence_scores
from longcue.evaluation.failure_diagnosis import diagnose_failure
from longcue.methods.common import parse_answer
from longcue.methods.retrievers import (
    RetrievedChunk,
    dense_ranking,
    extract_passage_ids,
    lexical_ranking,
    make_chunks,
    reciprocal_rank_fusion,
    retrieve_chunks,
    retrieval_diagnostics,
    _query_expansion_text,
)
from longcue.methods.ce_reranker import cross_encoder_ranking
from longcue.models.base import BaseModelClient
from longcue.prompts.templates import direct_answer_prompt
from longcue.run_experiment import _make_client


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run retriever-family ablations for ONCU-compatible datasets."
    )
    parser.add_argument("--config", required=True, help="Ablation YAML config.")
    parser.add_argument(
        "--run-reader",
        action="store_true",
        help="Also run the reader model on selected retriever/top-k conditions.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional smoke-test limit on the number of samples to process.",
    )
    args = parser.parse_args()
    run_ablation(Path(args.config), run_reader=args.run_reader, limit=args.limit)


def run_ablation(config_path: Path, *, run_reader: bool = False, limit: int | None = None) -> None:
    config = _load_yaml(config_path)
    output_dir = _resolve_path(config_path, str(config["output_dir"]))
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = _resolve_path(config_path, str(config["dataset_path"]))
    samples = load_samples(dataset_path)
    if limit is not None:
        samples = samples[: max(0, int(limit))]
    settings = config.get("retriever_family", {})
    retrievers = [str(item) for item in settings.get("retrievers", ["lexical", "oracle"])]
    top_ks = [int(item) for item in settings.get("top_k", [3, 5, 8, 16])]
    chunk_size = int(settings.get("chunk_size", 220))
    overlap = int(settings.get("overlap", 40))

    retrieval_rows = []
    for sample in _progress(samples, desc="retrieval-only samples"):
        ranking_bundle = _precompute_rankings_for_sample(
            sample=sample,
            retrievers=retrievers,
            chunk_size=chunk_size,
            overlap=overlap,
            dense_model_name=str(
                settings.get(
                    "dense_model_name",
                    "sentence-transformers/all-MiniLM-L6-v2",
                )
            ),
            rrf_k=int(settings.get("rrf_k", 60)),
            iterative_seed_k=int(settings.get("iterative_seed_k", 2)),
            iterative_expansion_words=int(settings.get("iterative_expansion_words", 96)),
            ce_rerank_model_name=str(
                settings.get("ce_rerank_model_name", "cross-encoder/ms-marco-MiniLM-L6-v2")
            ),
            ce_rerank_batch_size=int(settings.get("ce_rerank_batch_size", 32)),
            ce_rerank_device=settings.get("ce_rerank_device", None),
        )
        for retriever in retrievers:
            for top_k in top_ks:
                chunks = _chunks_for_retriever_topk(sample, ranking_bundle, retriever, top_k)
                diag = retrieval_diagnostics(chunks, sample.gold_evidence_ids)
                retrieval_rows.append(
                    {
                        "sample_id": sample.id,
                        "source": sample.source,
                        "dataset_name": config.get("dataset_name", sample.source),
                        "retriever": retriever,
                        "top_k": top_k,
                        "chunk_size": chunk_size,
                        "overlap": overlap,
                        "reasoning_type": sample.reasoning_type,
                        "context_length": sample.context_length,
                        "evidence_position": sample.evidence_position,
                        "evidence_density": sample.evidence_density,
                        "distractor_similarity": sample.distractor_similarity,
                        "gold_evidence_ids": ";".join(sample.gold_evidence_ids),
                        "retrieved_evidence_ids": ";".join(_flatten_ids(chunks)),
                        "retrieved_chunk_indices": ";".join(str(c.index) for c in chunks),
                        **diag,
                    }
                )

    _write_csv(output_dir / "retrieval_only_per_sample.csv", retrieval_rows)
    retrieval_summary = _summarize_retrieval(retrieval_rows)
    _write_csv(output_dir / "retrieval_only_summary.csv", retrieval_summary)
    _write_markdown(output_dir / "retrieval_only_summary.md", retrieval_summary)

    _write_json(
        output_dir / "protocol_manifest.json",
        {
            "config": str(config_path),
            "dataset_path": str(dataset_path),
            "sample_count": len(samples),
            "retrievers": retrievers,
            "top_k": top_ks,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "run_reader": bool(run_reader),
            "purpose": "retriever_family_ablation",
        },
    )
    _write_json(output_dir / "resolved_config.json", config)

    if run_reader:
        reader_rows = _run_reader_conditions(config_path, config, samples, output_dir)
        _write_csv(output_dir / "reader_per_sample_metrics.csv", reader_rows)
        reader_summary = _summarize_reader(reader_rows)
        _write_csv(output_dir / "reader_condition_summary.csv", reader_summary)
        _write_markdown(output_dir / "reader_condition_summary.md", reader_summary)
        reference_metrics = config.get("reference_metrics_path")
        if reference_metrics:
            ref_path = _resolve_path(config_path, str(reference_metrics))
            oncu_rows = _compute_reader_oncu(reader_rows, ref_path)
            _write_csv(output_dir / "reader_oncu_rows.csv", oncu_rows)
            oncu_summary = _summarize_reader_oncu(oncu_rows)
            _write_csv(output_dir / "reader_oncu_summary.csv", oncu_summary)
            _write_markdown(output_dir / "reader_oncu_summary.md", oncu_summary)



def _progress(items: list[Any], *, desc: str) -> Any:
    try:
        from tqdm import tqdm

        return tqdm(items, desc=desc, unit="sample")
    except Exception:  # pragma: no cover - progress bars are optional.
        return items


def _precompute_rankings_for_sample(
    *,
    sample: Any,
    retrievers: list[str],
    chunk_size: int,
    overlap: int,
    dense_model_name: str,
    rrf_k: int,
    iterative_seed_k: int,
    iterative_expansion_words: int,
    ce_rerank_model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2",
    ce_rerank_batch_size: int = 32,
    ce_rerank_device: str | None = None,
) -> dict[str, Any]:
    """Precompute all expensive rankings once per sample.

    The first implementation recomputed dense embeddings for every retriever/top-k
    pair. This helper computes chunks, lexical rankings, dense rankings, and fused
    rankings once, then all top-k values are obtained by slicing prefixes.
    """
    normalized = {str(name).lower().strip() for name in retrievers}
    chunks = make_chunks(sample.long_context, chunk_size=chunk_size, overlap=overlap)
    rankings: dict[str, list[tuple[int, float]]] = {}

    ce_retrievers = sorted(name for name in normalized if _is_hybrid_ce_retriever(name))
    needs_ce = bool(ce_retrievers)
    needs_lexical = bool(normalized.intersection({"lexical", "hybrid", "iterative", "multi_hop_iterative", "multihop_iterative"})) or needs_ce
    needs_dense = bool(normalized.intersection({"dense", "hybrid"})) or needs_ce

    lexical_ranked: list[tuple[int, float]] | None = None
    dense_ranked: list[tuple[int, float]] | None = None
    hybrid_ranked: list[tuple[int, float]] | None = None

    if chunks and needs_lexical:
        lexical_ranked = lexical_ranking(sample.question, chunks)
    if chunks and needs_dense:
        dense_ranked = dense_ranking(sample.question, chunks, model_name=dense_model_name)

    if "lexical" in normalized and lexical_ranked is not None:
        rankings["lexical"] = lexical_ranked
    if "dense" in normalized and dense_ranked is not None:
        rankings["dense"] = dense_ranked
    if ("hybrid" in normalized or needs_ce) and lexical_ranked is not None and dense_ranked is not None:
        hybrid_ranked = reciprocal_rank_fusion(
            [[idx for idx, _ in lexical_ranked], [idx for idx, _ in dense_ranked]],
            rrf_k=rrf_k,
        )
        if "hybrid" in normalized:
            rankings["hybrid"] = hybrid_ranked

    if needs_ce and hybrid_ranked is not None:
        for ce_name in ce_retrievers:
            candidate_k = _candidate_k_from_hybrid_ce_label(ce_name)
            candidate_indices = [idx for idx, _ in hybrid_ranked[:candidate_k]]
            rankings[ce_name] = cross_encoder_ranking(
                sample.question,
                chunks,
                candidate_indices,
                model_name=ce_rerank_model_name,
                batch_size=ce_rerank_batch_size,
                device=ce_rerank_device,
            )

    if normalized.intersection({"iterative", "multi_hop_iterative", "multihop_iterative"}) and lexical_ranked is not None:
        seed_chunks = [chunks[idx] for idx, _ in lexical_ranked[: max(1, iterative_seed_k)]]
        expansion = _query_expansion_text(seed_chunks, max_words=iterative_expansion_words)
        expanded_query = f"{sample.question}\n{expansion}".strip()
        second_pass = lexical_ranking(expanded_query, chunks)
        iterative_ranked = reciprocal_rank_fusion(
            [[idx for idx, _ in lexical_ranked], [idx for idx, _ in second_pass]],
            rrf_k=rrf_k,
        )
        rankings["iterative"] = iterative_ranked
        rankings["multi_hop_iterative"] = iterative_ranked
        rankings["multihop_iterative"] = iterative_ranked

    return {"chunks": chunks, "rankings": rankings}



def _is_hybrid_ce_retriever(name: str) -> bool:
    return re.fullmatch(r"hybrid_ce\d+", str(name).lower().strip()) is not None


def _candidate_k_from_hybrid_ce_label(name: str) -> int:
    match = re.fullmatch(r"hybrid_ce(\d+)", str(name).lower().strip())
    if not match:
        raise ValueError(f"Invalid CE rerank retriever label: {name!r}. Use labels like hybrid_ce64.")
    return max(1, int(match.group(1)))


def _chunks_for_retriever_topk(
    sample: Any,
    ranking_bundle: dict[str, Any],
    retriever: str,
    top_k: int,
) -> list[RetrievedChunk]:
    name = str(retriever).lower().strip()
    if name == "oracle":
        return retrieve_chunks(sample=sample, retriever="oracle", top_k=top_k)
    chunks = list(ranking_bundle.get("chunks", []))
    ranking = list(ranking_bundle.get("rankings", {}).get(name, []))
    return [
        RetrievedChunk(
            index=int(index),
            text=chunks[int(index)],
            score=float(score),
            passage_ids=extract_passage_ids(chunks[int(index)]),
            retriever=name,
        )
        for index, score in ranking[:top_k]
    ]


def _run_reader_conditions(
    config_path: Path,
    config: dict[str, Any],
    samples: list[Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    settings = config.get("retriever_family", {})
    retrievers = [
        str(item)
        for item in settings.get(
            "reader_retrievers",
            settings.get("retrievers", ["lexical", "oracle"]),
        )
    ]
    top_ks = [int(item) for item in settings.get("reader_top_k", [3, 8])]
    generation = config.get("generation", {})
    client: BaseModelClient = _make_client(config.get("model", {"provider": "mock"}))
    max_tokens = int(generation.get("max_tokens", 1024))
    temperature = float(generation.get("temperature", 0.0))

    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []

    for sample in _progress(samples, desc="reader samples"):
        ranking_bundle = _precompute_rankings_for_sample(
            sample=sample,
            retrievers=retrievers,
            chunk_size=int(settings.get("chunk_size", 220)),
            overlap=int(settings.get("overlap", 40)),
            dense_model_name=str(
                settings.get(
                    "dense_model_name",
                    "sentence-transformers/all-MiniLM-L6-v2",
                )
            ),
            rrf_k=int(settings.get("rrf_k", 60)),
            iterative_seed_k=int(settings.get("iterative_seed_k", 2)),
            iterative_expansion_words=int(settings.get("iterative_expansion_words", 96)),
            ce_rerank_model_name=str(
                settings.get("ce_rerank_model_name", "cross-encoder/ms-marco-MiniLM-L6-v2")
            ),
            ce_rerank_batch_size=int(settings.get("ce_rerank_batch_size", 32)),
            ce_rerank_device=settings.get("ce_rerank_device", None),
        )
        for retriever in retrievers:
            for top_k in top_ks:
                chunks = _chunks_for_retriever_topk(sample, ranking_bundle, retriever, top_k)
                context = "\n\n".join(chunk.text for chunk in chunks)
                prompt = direct_answer_prompt(
                    sample.question,
                    context,
                    task=f"RETRIEVER_FAMILY_{retriever}_K{top_k}",
                    reasoning_type=sample.reasoning_type,
                    answer_type=sample.answer_type,
                )
                raw = client.generate(prompt, max_tokens=max_tokens, temperature=temperature)
                prediction = parse_answer(raw, passage_text=prompt)
                method = f"retfam_{retriever}_k{top_k}"
                row = _metric_row(
                    sample=sample,
                    model_name=client.model_name,
                    method=method,
                    retriever=retriever,
                    top_k=top_k,
                    prediction=prediction,
                )
                rows.append(row)
                raw_rows.append(
                    {
                        "sample_id": sample.id,
                        "model_name": client.model_name,
                        "retriever": retriever,
                        "top_k": top_k,
                        "raw_response": raw,
                        "prompt": prompt if bool(config.get("logging", {}).get("save_full_prompts", False)) else "",
                    }
                )
    save_jsonl(raw_rows, output_dir / "reader_raw_responses.jsonl")
    return rows


def _metric_row(
    *,
    sample: Any,
    model_name: str,
    method: str,
    retriever: str,
    top_k: int,
    prediction: dict[str, Any],
) -> dict[str, Any]:
    predicted_answer = str(prediction.get("answer", ""))
    predicted_evidence_ids = [
        str(item) for item in prediction.get("evidence_ids", []) if str(item)
    ]
    strict_exact = exact_match(predicted_answer, sample.gold_answer)
    strict_f1 = token_f1(predicted_answer, sample.gold_answer)
    relaxed_exact = exact_match_relaxed(
        predicted_answer,
        sample.gold_answer,
        answer_type=sample.answer_type,
        reasoning_type=sample.reasoning_type,
    )
    relaxed_f1 = token_f1_relaxed(
        predicted_answer,
        sample.gold_answer,
        answer_type=sample.answer_type,
        reasoning_type=sample.reasoning_type,
    )
    evidence = evidence_scores(predicted_evidence_ids, sample.gold_evidence_ids)
    answer_correct = bool(strict_exact)
    return {
        "sample_id": sample.id,
        "model_name": model_name,
        "method": method,
        "retriever": retriever,
        "top_k": top_k,
        "source": sample.source,
        "reasoning_type": sample.reasoning_type,
        "answer_type": sample.answer_type,
        "context_length": sample.context_length,
        "evidence_position": sample.evidence_position,
        "evidence_density": sample.evidence_density,
        "distractor_similarity": sample.distractor_similarity,
        "gold_answer": sample.gold_answer,
        "predicted_answer": predicted_answer,
        "gold_evidence_ids": ";".join(sample.gold_evidence_ids),
        "predicted_evidence_ids": ";".join(predicted_evidence_ids),
        "cue_applicable": bool(sample.oracle_evidence),
        "exact_match_strict": strict_exact,
        "answer_f1_strict": strict_f1,
        "exact_match_relaxed": relaxed_exact,
        "answer_f1_relaxed": relaxed_f1,
        "exact_match": strict_exact,
        "answer_f1": strict_f1,
        **evidence,
        "citation_grounding": citation_grounding(predicted_evidence_ids, sample.gold_evidence_ids),
        "failure_type": diagnose_failure(
            sample.gold_evidence_ids,
            predicted_evidence_ids,
            answer_correct,
            sample.reasoning_type,
        ),
        "parse_error": str(prediction.get("parse_error", "")),
    }


def _compute_reader_oncu(reader_rows: list[dict[str, Any]], reference_metrics_path: Path) -> list[dict[str, Any]]:
    reference_rows = _read_csv(reference_metrics_path)
    reference_rows = [
        row for row in reference_rows if row.get("method") in {"no_evidence", "oracle"}
    ]
    combined = reference_rows + reader_rows
    rows = compute_cue_rows(combined, score_field="answer_f1_relaxed")
    for row in rows:
        method = str(row.get("long_method", ""))
        if method.startswith("retfam_"):
            parts = method.replace("retfam_", "").rsplit("_k", 1)
            row["retriever"] = parts[0]
            row["top_k"] = parts[1] if len(parts) > 1 else ""
        row["score_field"] = "answer_f1_relaxed"
    return [row for row in rows if str(row.get("long_method", "")).startswith("retfam_")]


def _summarize_retrieval(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["dataset_name"], row["retriever"], row["top_k"])].append(row)
    summary = []
    fields = [
        "retrieval_precision",
        "retrieval_recall",
        "retrieval_f1",
        "oracle_hit_rate",
        "full_chain_coverage",
        "distractor_id_rate",
        "retrieved_passage_count",
    ]
    for (dataset, retriever, top_k), items in sorted(groups.items()):
        out = {"dataset_name": dataset, "retriever": retriever, "top_k": top_k, "n": len(items)}
        for field in fields:
            out[field] = mean(float(item[field]) for item in items)
        summary.append(out)
    return summary


def _summarize_reader(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["source"], row["model_name"], row["retriever"], row["top_k"])].append(row)
    fields = [
        "exact_match_strict",
        "answer_f1_strict",
        "exact_match_relaxed",
        "answer_f1_relaxed",
        "evidence_precision",
        "evidence_recall",
        "evidence_f1",
        "citation_grounding",
    ]
    summary = []
    for (dataset, model, retriever, top_k), items in sorted(groups.items()):
        out = {
            "dataset_name": dataset,
            "model_name": model,
            "retriever": retriever,
            "top_k": top_k,
            "n": len(items),
            "parse_errors": sum(bool(item.get("parse_error")) for item in items),
        }
        for field in fields:
            out[field] = mean(float(item[field]) for item in items)
        summary.append(out)
    return summary


def _summarize_reader_oncu(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row.get("source"), row.get("model_name"), row.get("retriever"), row.get("top_k"))].append(row)
    summary = []
    for (dataset, model, retriever, top_k), items in sorted(groups.items()):
        valid = [item for item in items if str(item.get("cue_valid", "")).lower() == "true" or item.get("cue_valid") is True]
        clipped = [float(item["cue_clipped"]) for item in valid if str(item.get("cue_clipped", "")) not in {"", "nan"}]
        summary.append(
            {
                "dataset_name": dataset,
                "model_name": model,
                "retriever": retriever,
                "top_k": top_k,
                "valid_groups": len(clipped),
                "total_groups": len(items),
                "oncu_relaxed_f1": mean(clipped) if clipped else "",
            }
        )
    return summary


def _flatten_ids(chunks: list[Any]) -> list[str]:
    ids: list[str] = []
    seen = set()
    for chunk in chunks:
        for pid in chunk.passage_ids:
            if pid not in seen:
                ids.append(pid)
                seen.add(pid)
    return ids


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_path(config_path: Path, path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    project_root = config_path.parent
    # configs/ablations/*.yaml should resolve relative to the repository root.
    if config_path.parent.name == "ablations":
        project_root = config_path.parent.parent.parent
    return (project_root / candidate).resolve()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_format_cell(row.get(h, "")) for h in headers) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    main()
