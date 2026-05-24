from __future__ import annotations

import argparse
import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import yaml

from longcue.data.io import load_samples, save_jsonl
from longcue.evaluation.aggregate import (
    aggregate_metrics,
    robustness_drop_rows,
    write_csv,
    write_markdown_table,
)
from longcue.evaluation.answer_metrics import (
    exact_match,
    exact_match_relaxed,
    token_f1,
    token_f1_relaxed,
)
from longcue.evaluation.cue import compute_cue_rows
from longcue.evaluation.evidence_metrics import citation_grounding, evidence_scores
from longcue.evaluation.failure_diagnosis import diagnose_failure
from longcue.methods import METHOD_REGISTRY
from longcue.protocol import (
    PROMPT_PROTOCOL_VERSION,
    method_spec,
    prompt_fingerprint,
)
from longcue.models import MockModelClient, OllamaClient, OpenAICompatibleClient
from longcue.models.base import BaseModelClient
from longcue.utils.logging import setup_logging

try:  # pragma: no cover - exercised through progress helpers with monkeypatches.
    from tqdm.auto import tqdm as _tqdm
except ImportError:  # pragma: no cover - environment dependent fallback.
    _tqdm = None

try:  # pragma: no cover - import depends on optional tqdm availability.
    from tqdm.contrib.logging import logging_redirect_tqdm as _logging_redirect_tqdm
except ImportError:  # pragma: no cover - environment dependent fallback.
    _logging_redirect_tqdm = None


def run_experiment(config_path: str | Path) -> dict[str, Path]:
    config_file = Path(config_path)
    config = _load_config(config_file)
    dataset_path = _resolve_path(config_file, str(config["dataset_path"]))
    output_dir = _resolve_path(config_file, str(config["output_dir"]))
    results_dir = output_dir / "results"
    tables_dir = output_dir / "tables"
    logs_dir = output_dir / "logs"
    logger = setup_logging(logs_dir)
    client = _make_client(config["model"])
    generation = config.get("generation", {})
    evaluation_config = config.get("evaluation", {})
    logging_config = config.get("logging", {})
    progress_config = config.get("progress", {})
    samples = load_samples(dataset_path)
    method_names = list(config.get("methods", []))
    unknown_methods = sorted(set(method_names).difference(METHOD_REGISTRY))
    if unknown_methods:
        raise ValueError(f"Unknown methods: {unknown_methods}")
    logger.info("Loaded %d samples from %s", len(samples), dataset_path)
    logger.info("Running methods: %s", ", ".join(method_names))

    raw_records: list[dict[str, Any]] = []
    metric_records: list[dict[str, Any]] = []
    total_predictions = len(samples) * len(method_names)
    progress_bar = _make_progress_bar(
        total_predictions,
        enabled=bool(progress_config.get("enabled", True)),
        logger=logger,
    )
    try:
        with _progress_logging_context(progress_bar, logger):
            for sample in samples:
                for method_name in method_names:
                    _set_progress_context(progress_bar, method_name, sample.id)
                    output = METHOD_REGISTRY[method_name](
                        sample=sample,
                        client=client,
                        max_tokens=int(generation.get("max_tokens", 256)),
                        temperature=float(generation.get("temperature", 0.0)),
                        logger=logger,
                        retrieval=config.get("retrieval", {}),
                    )
                    raw_record = _raw_record(
                        sample_id=sample.id,
                        model_name=client.model_name,
                        sample=sample,
                        output=output,
                        save_full_prompts=bool(logging_config.get("save_full_prompts", False)),
                        save_intermediate=bool(logging_config.get("save_intermediate", True)),
                    )
                    raw_records.append(raw_record)
                    metric_records.append(
                        _evaluate_output(
                            sample=sample,
                            model_name=client.model_name,
                            method_name=method_name,
                            output=output,
                            compute_failure_types=bool(
                                evaluation_config.get("compute_failure_types", True)
                            ),
                        )
                    )
                    if progress_bar is not None:
                        progress_bar.update(1)
    finally:
        if progress_bar is not None:
            progress_bar.close()

    aggregate_rows = aggregate_metrics(metric_records)
    robustness_rows = robustness_drop_rows(metric_records)
    cue_rows = (
        compute_cue_rows(metric_records)
        if bool(evaluation_config.get("compute_cue", True))
        else []
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "resolved_config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    _write_protocol_manifest(output_dir, config, method_names)
    jsonl_suffix = ".jsonl.gz" if bool(logging_config.get("compress_outputs", False)) else ".jsonl"
    artifacts = {
        "raw": save_jsonl(raw_records, results_dir / f"raw_model_responses{jsonl_suffix}"),
        "predictions": save_jsonl(
            (record["prediction"] | {"sample_id": record["sample_id"], "method": record["method"]}
             for record in raw_records),
            results_dir / f"parsed_predictions{jsonl_suffix}",
        ),
        "per_sample": write_csv(metric_records, results_dir / "per_sample_metrics.csv"),
        "aggregate_csv": write_csv(aggregate_rows, results_dir / "aggregate_metrics.csv"),
        "aggregate_md": write_markdown_table(
            aggregate_rows, tables_dir / "aggregate_metrics.md"
        ),
        "cue_csv": write_csv(cue_rows, results_dir / "cue_metrics.csv"),
        "cue_md": write_markdown_table(cue_rows, tables_dir / "cue_metrics.md"),
        "robustness_csv": write_csv(
            robustness_rows, results_dir / "robustness_drop.csv"
        ),
        "robustness_md": write_markdown_table(
            robustness_rows, tables_dir / "robustness_drop.md"
        ),
    }
    logger.info("Wrote %d per-sample metric rows to %s", len(metric_records), results_dir)
    _print_summary(metric_records, cue_rows, output_dir)
    return artifacts


def _make_progress_bar(total_predictions: int, *, enabled: bool, logger: Any) -> Any | None:
    if not enabled:
        return None
    if _tqdm is None:
        logger.info("tqdm is not installed; progress bar disabled.")
        return None
    return _tqdm(
        total=total_predictions,
        desc="Running predictions",
        unit="pred",
        dynamic_ncols=True,
    )


def _set_progress_context(progress_bar: Any | None, method_name: str, sample_id: str) -> None:
    if progress_bar is None:
        return
    progress_bar.set_postfix(
        {"method": method_name, "sample_id": sample_id},
        refresh=True,
    )


def _progress_logging_context(progress_bar: Any | None, logger: Any) -> Any:
    if progress_bar is not None and _logging_redirect_tqdm is not None:
        return _logging_redirect_tqdm(loggers=[logger])
    return nullcontext()


def _evaluate_output(
    sample: Any,
    model_name: str,
    method_name: str,
    output: dict[str, Any],
    compute_failure_types: bool,
) -> dict[str, Any]:
    prediction = output["prediction"]
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
    answer_correct = bool(strict_exact)
    scores = evidence_scores(predicted_evidence_ids, sample.gold_evidence_ids)
    cue_applicable = bool(sample.oracle_evidence) and bool(
        sample.metadata.get("cue_applicable", bool(sample.oracle_evidence))
    )
    return {
        "sample_id": sample.id,
        "model_name": model_name,
        "method": method_name,
        **_method_metadata(method_name),
        **_sample_metadata(sample),
        "gold_answer": sample.gold_answer,
        "predicted_answer": predicted_answer,
        "gold_evidence_ids": ";".join(sample.gold_evidence_ids),
        "predicted_evidence_ids": ";".join(predicted_evidence_ids),
        "cue_applicable": cue_applicable,
        "exact_match_strict": strict_exact,
        "answer_f1_strict": strict_f1,
        "exact_match_relaxed": relaxed_exact,
        "answer_f1_relaxed": relaxed_f1,
        # Backward-compatible answer columns retain the legacy strict metric behavior.
        "exact_match": strict_exact,
        "answer_f1": strict_f1,
        **scores,
        "citation_grounding": citation_grounding(
            predicted_evidence_ids, sample.gold_evidence_ids
        ),
        "failure_type": (
            diagnose_failure(
                sample.gold_evidence_ids,
                predicted_evidence_ids,
                answer_correct,
                sample.reasoning_type,
            )
            if compute_failure_types
            else ""
        ),
        "parse_error": str(prediction.get("parse_error", "")),
    }


def _method_metadata(method_name: str) -> dict[str, Any]:
    spec = method_spec(method_name)
    return {
        "method_display_name": spec.display_name,
        "method_family": spec.family,
        "method_role": spec.role,
        "core_diagnostic": spec.core_diagnostic,
    }


def _sample_metadata(sample: Any) -> dict[str, Any]:
    return {
        "source": sample.source,
        "reasoning_type": sample.reasoning_type,
        "answer_type": sample.answer_type,
        "context_length": sample.context_length,
        "evidence_position": sample.evidence_position,
        "evidence_density": sample.evidence_density,
        "distractor_similarity": sample.distractor_similarity,
    }


def _raw_record(
    *,
    sample_id: str,
    model_name: str,
    sample: Any,
    output: dict[str, Any],
    save_full_prompts: bool,
    save_intermediate: bool,
) -> dict[str, Any]:
    record = {
        "sample_id": sample_id,
        "model_name": model_name,
        **_sample_metadata(sample),
        "method": output["method"],
        **_method_metadata(str(output["method"])),
        "prompt_protocol_version": PROMPT_PROTOCOL_VERSION,
        "prompt_hash": prompt_fingerprint(str(output.get("prompt", ""))),
        "raw_response": output["raw_response"],
        "prediction": output["prediction"],
    }
    if save_full_prompts:
        record["prompt"] = output.get("prompt", "")
    if save_intermediate:
        record["intermediate"] = _filter_intermediate(
            output.get("intermediate", {}), save_full_prompts=save_full_prompts
        )
    return record


def _filter_intermediate(intermediate: Any, *, save_full_prompts: bool) -> Any:
    if isinstance(intermediate, dict):
        filtered = {}
        for key, value in intermediate.items():
            if not save_full_prompts and key.endswith("_prompt"):
                continue
            if not save_full_prompts and key == "retrieved_chunks" and isinstance(value, list):
                filtered["retrieved_chunk_count"] = len(value)
                filtered["retrieved_chunk_char_lengths"] = [len(str(chunk)) for chunk in value]
                continue
            filtered[key] = _filter_intermediate(
                value, save_full_prompts=save_full_prompts
            )
        return filtered
    if isinstance(intermediate, list):
        return [
            _filter_intermediate(value, save_full_prompts=save_full_prompts)
            for value in intermediate
        ]
    return intermediate


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return payload


def _resolve_path(config_path: Path, path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    config_relative = config_path.parent / candidate
    if config_relative.exists():
        return config_relative.resolve()
    return (Path.cwd() / candidate).resolve()


def _write_protocol_manifest(output_dir: Path, config: dict[str, Any], method_names: list[str]) -> None:
    manifest = {
        "protocol_version": PROMPT_PROTOCOL_VERSION,
        "purpose": "Diagnostic evaluation protocol. Templates are fixed across models and datasets; results should not be interpreted as prompt optimization.",
        "methods": [
            {
                "name": name,
                "display_name": method_spec(name).display_name,
                "family": method_spec(name).family,
                "role": method_spec(name).role,
                "core_diagnostic": method_spec(name).core_diagnostic,
                "description": method_spec(name).description,
            }
            for name in method_names
        ],
        "generation": config.get("generation", {}),
        "retrieval": config.get("retrieval", {}),
    }
    (output_dir / "protocol_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8"
    )


def _make_client(model_config: dict[str, Any]) -> BaseModelClient:
    provider = str(model_config.get("provider", "mock")).lower()
    model_name = str(model_config.get("model_name", "mock"))
    if provider == "mock":
        return MockModelClient(model_name=model_name)
    if provider in {"openai_compatible", "openai-compatible"}:
        return OpenAICompatibleClient(
            model_name=model_name,
            base_url=model_config.get("base_url"),
        )
    if provider == "ollama":
        return OllamaClient(
            model_name=model_name,
            base_url=model_config.get("base_url"),
            timeout=float(model_config.get("timeout", 600.0)),
            num_ctx=(int(model_config["num_ctx"]) if "num_ctx" in model_config else None),
        )
    raise ValueError(f"Unsupported model provider: {provider}")


def _print_summary(
    metric_records: list[dict[str, Any]], cue_rows: list[dict[str, Any]], output_dir: Path
) -> None:
    if metric_records:
        average_accuracy = sum(record["exact_match"] for record in metric_records) / len(
            metric_records
        )
        print(
            f"Completed {len(metric_records)} predictions. "
            f"Mean exact match={average_accuracy:.3f}."
        )
    print(f"Computed {len(cue_rows)} ONCU rows.")
    print(f"Results saved under {output_dir}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run long-context ONCU diagnostic experiments.")
    parser.add_argument("--config", required=True, help="Path to YAML experiment config.")
    args = parser.parse_args()
    run_experiment(args.config)


if __name__ == "__main__":
    main()
