#!/usr/bin/env python3
"""Export a blind human-validation sample for failure-taxonomy auditing.

This script samples failed predictions from existing ONCU experiment artifacts and
creates blind annotation CSV files for two independent annotators. It is designed
for the JAIR reviewer-facing validation of the rule-based failure taxonomy.

Default output directory:
    experiment_backups/failure_taxonomy_human_validation_20260530

Typical use:
    python scripts/export_failure_taxonomy_audit.py \
      --sample-size 300 \
      --seed 42

The script tries to be robust to small schema differences across experiment
outputs. It searches for per_sample_metrics.csv files under outputs/**/results/
and joins parsed_predictions.jsonl and data/processed/*.jsonl when available.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

LABELS = [
    "localization",
    "selection",
    "integration",
    "conversion",
    "parse_format",
    "ambiguous",
]

METHOD_ALIASES = {
    "direct": "full_context",
    "full": "full_context",
    "full_context": "full_context",
    "retrieve_then_read": "retrieved_evidence",
    "retrieved": "retrieved_evidence",
    "retrieved_evidence": "retrieved_evidence",
    "oracle": "oracle_evidence",
    "oracle_evidence": "oracle_evidence",
    "no_evidence": "no_evidence",
}

FAILURE_LABEL_ALIASES = {
    "success": "success",
    "correct": "success",
    "evidence_localization_failure": "localization",
    "localization_failure": "localization",
    "localization": "localization",
    "evidence_selection_failure": "selection",
    "selection_failure": "selection",
    "selection": "selection",
    "evidence_integration_failure": "integration",
    "integration_failure": "integration",
    "integration": "integration",
    "answer_conversion_failure": "conversion",
    "conversion_failure": "conversion",
    "conversion": "conversion",
    "parse_failure": "parse_format",
    "parse": "parse_format",
    "format_failure": "parse_format",
    "parse_format": "parse_format",
    "unparseable": "parse_format",
}

QUESTION_KEYS = ["question", "query", "input_question", "prompt_question"]
GOLD_ANSWER_KEYS = ["gold_answer", "answer", "answers", "target", "label"]
SAMPLE_ID_KEYS = ["sample_id", "id", "qid", "example_id"]
MODEL_KEYS = ["model_name", "model", "generator", "llm"]
DATASET_KEYS = ["dataset_name", "dataset", "source", "task", "benchmark"]
METHOD_KEYS = ["method", "condition", "prompt_condition"]
FAILURE_KEYS = ["failure_type", "failure_label", "diagnostic_label"]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                obj["__source_jsonl"] = str(path)
                obj["__line_no"] = line_no
                rows.append(obj)
    return rows


def _first_present(row: dict[str, Any] | pd.Series, keys: Iterable[str], default: Any = "") -> Any:
    for key in keys:
        if key in row:
            val = row[key]
            if pd.isna(val) if not isinstance(val, (list, dict, tuple)) else False:
                continue
            if val is not None and val != "":
                return val
    return default


def _as_string(value: Any, max_chars: int | None = None) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    elif isinstance(value, (list, tuple)):
        text = "; ".join(_as_string(v) for v in value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if max_chars is not None and len(text) > max_chars:
        return text[: max_chars - 20].rstrip() + " ... [truncated]"
    return text


def _as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, tuple):
        return [str(v) for v in value]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except json.JSONDecodeError:
            pass
        # Accept p0001,p0002 or ['p0001', 'p0002']-like strings.
        s = s.strip("[]")
        parts = [p.strip().strip("'\"") for p in re.split(r"[,;]", s)]
        return [p for p in parts if p]
    return [str(value)]


def _normalize_method(value: Any) -> str:
    raw = _as_string(value).strip().lower()
    return METHOD_ALIASES.get(raw, raw or "unknown")


def _normalize_failure_label(value: Any) -> str:
    raw = _as_string(value).strip().lower().replace("-", "_").replace(" ", "_")
    return FAILURE_LABEL_ALIASES.get(raw, raw or "unknown")


def _infer_run_dir(metrics_path: Path) -> Path:
    # Expected: outputs/<run>/results/per_sample_metrics.csv
    if metrics_path.parent.name == "results":
        return metrics_path.parent.parent
    return metrics_path.parent


def _load_processed_samples(root: Path) -> dict[str, dict[str, Any]]:
    """Load all data/processed JSONL samples and index them by id/sample_id."""
    index: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "data" / "processed").glob("*.jsonl")):
        for obj in _read_jsonl(path):
            sid = _first_present(obj, SAMPLE_ID_KEYS, "")
            if sid:
                obj = dict(obj)
                obj["__processed_file"] = str(path)
                index[str(sid)] = obj
    return index


def _load_predictions_for_run(run_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:
    pred_path = run_dir / "results" / "parsed_predictions.jsonl"
    if not pred_path.exists():
        return {}
    idx: dict[tuple[str, str], dict[str, Any]] = {}
    for obj in _read_jsonl(pred_path):
        sid = str(_first_present(obj, SAMPLE_ID_KEYS, ""))
        method = _normalize_method(_first_present(obj, METHOD_KEYS, ""))
        if not sid or not method:
            continue
        idx[(sid, method)] = obj
    return idx


def _guess_answer(pred: dict[str, Any]) -> str:
    for key in ["answer", "predicted_answer", "prediction", "final_answer"]:
        if key in pred and pred[key] not in (None, ""):
            return _as_string(pred[key], max_chars=None)
    nested = pred.get("parsed") or pred.get("output")
    if isinstance(nested, dict):
        return _guess_answer(nested)
    return ""


def _guess_explanation(pred: dict[str, Any], max_chars: int) -> str:
    for key in ["explanation", "rationale", "reasoning", "analysis", "model_explanation"]:
        if key in pred and pred[key] not in (None, ""):
            return _as_string(pred[key], max_chars=max_chars)
    nested = pred.get("parsed") or pred.get("output")
    if isinstance(nested, dict):
        return _guess_explanation(nested, max_chars=max_chars)
    return ""


def _guess_evidence_ids(pred: dict[str, Any]) -> list[str]:
    for key in ["evidence_ids", "predicted_evidence_ids", "citations", "supporting_passages"]:
        if key in pred:
            ids = _as_list(pred[key])
            if ids:
                return ids
    nested = pred.get("parsed") or pred.get("output")
    if isinstance(nested, dict):
        return _guess_evidence_ids(nested)
    return []


def _passage_map(sample: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for key in ["passages", "context_passages", "documents", "ctxs", "paragraphs"]:
        val = sample.get(key)
        if isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    pid = _first_present(item, ["passage_id", "id", "pid", "doc_id"], f"p{i:04d}")
                    text = _first_present(item, ["text", "content", "passage", "paragraph"], "")
                    title = _first_present(item, ["title", "name"], "")
                    body = f"{title}: {text}" if title else _as_string(text)
                    mapping[str(pid)] = _as_string(body)
                else:
                    mapping[f"p{i:04d}"] = _as_string(item)
    # Parse string contexts with [passage_id: p0001] markers.
    context = _first_present(sample, ["context", "full_context", "long_context", "input_context"], "")
    if isinstance(context, str) and "passage_id" in context:
        pattern = re.compile(r"\[passage_id:\s*([^\]]+)\](.*?)(?=\[passage_id:\s*[^\]]+\]|$)", re.S)
        for match in pattern.finditer(context):
            pid = match.group(1).strip()
            text = re.sub(r"\s+", " ", match.group(2)).strip()
            if pid and text:
                mapping[pid] = text
    return mapping


def _evidence_ids_from_sample(sample: dict[str, Any]) -> list[str]:
    for key in [
        "gold_evidence_ids",
        "oracle_evidence_ids",
        "evidence_ids",
        "supporting_evidence_ids",
        "supporting_passage_ids",
    ]:
        if key in sample:
            ids = _as_list(sample[key])
            if ids:
                return ids
    # Some datasets store evidence as dicts/lists.
    for key in ["oracle_evidence", "gold_evidence", "supporting_facts"]:
        val = sample.get(key)
        if isinstance(val, list):
            ids: list[str] = []
            for item in val:
                if isinstance(item, dict):
                    pid = _first_present(item, ["passage_id", "id", "pid", "doc_id"], "")
                    if pid:
                        ids.append(str(pid))
                elif isinstance(item, str):
                    ids.append(item)
            if ids:
                return ids
    return []


def _texts_for_ids(sample: dict[str, Any], ids: list[str], max_chars: int) -> str:
    if not ids:
        return ""
    mapping = _passage_map(sample)
    parts = []
    for pid in ids:
        text = mapping.get(pid, "")
        if text:
            parts.append(f"{pid}: {text}")
        else:
            parts.append(f"{pid}: [text not found in processed sample]")
    return _as_string(" || ".join(parts), max_chars=max_chars)


def _sample_question(sample: dict[str, Any], max_chars: int) -> str:
    return _as_string(_first_present(sample, QUESTION_KEYS, ""), max_chars=max_chars)


def _sample_gold_answer(sample: dict[str, Any], max_chars: int) -> str:
    return _as_string(_first_present(sample, GOLD_ANSWER_KEYS, ""), max_chars=max_chars)


def _load_all_metric_rows(root: Path) -> pd.DataFrame:
    paths = sorted(root.glob("outputs/*/results/per_sample_metrics.csv"))
    if not paths:
        raise FileNotFoundError(
            "No outputs/*/results/per_sample_metrics.csv files found. Run this script at the repo root after experiments finish."
        )
    frames = []
    for path in paths:
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            print(f"[WARN] Could not read {path}: {exc}")
            continue
        if df.empty:
            continue
        run_dir = _infer_run_dir(path)
        df = df.copy()
        df["__metrics_file"] = str(path)
        df["__run_dir"] = str(run_dir)
        df["__run_name"] = run_dir.name
        frames.append(df)
    if not frames:
        raise RuntimeError("No readable per-sample metrics found.")
    return pd.concat(frames, ignore_index=True, sort=False)


def _build_candidate_pool(root: Path, max_text_chars: int, include_no_evidence: bool) -> pd.DataFrame:
    metrics = _load_all_metric_rows(root)
    processed = _load_processed_samples(root)
    prediction_cache: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}

    rows: list[dict[str, Any]] = []
    for _, r in metrics.iterrows():
        row = r.to_dict()
        sid = str(_first_present(row, SAMPLE_ID_KEYS, ""))
        if not sid:
            continue
        method = _normalize_method(_first_present(row, METHOD_KEYS, ""))
        if method == "no_evidence" and not include_no_evidence:
            continue
        failure = _normalize_failure_label(_first_present(row, FAILURE_KEYS, ""))
        if failure == "success":
            continue
        if failure not in LABELS:
            # Unknown labels are not safe for a fixed human codebook.
            continue
        run_dir = str(row.get("__run_dir", ""))
        if run_dir not in prediction_cache:
            prediction_cache[run_dir] = _load_predictions_for_run(Path(run_dir))
        pred = prediction_cache[run_dir].get((sid, method), {})
        sample = processed.get(sid, {})

        dataset = _as_string(_first_present(row, DATASET_KEYS, ""))
        if not dataset:
            dataset = _infer_dataset_from_run_name(_as_string(row.get("__run_name", "")))
        model = _as_string(_first_present(row, MODEL_KEYS, ""))
        if not model:
            model = _infer_model_from_run_name(_as_string(row.get("__run_name", "")))

        pred_answer = _as_string(
            _first_present(row, ["predicted_answer", "prediction", "answer"], ""),
            max_chars=max_text_chars,
        )
        if not pred_answer:
            pred_answer = _as_string(_guess_answer(pred), max_chars=max_text_chars)
        pred_evidence_ids = _as_list(
            _first_present(row, ["predicted_evidence_ids", "evidence_ids", "citation_ids"], "")
        )
        if not pred_evidence_ids:
            pred_evidence_ids = _guess_evidence_ids(pred)

        gold_evidence_ids = _evidence_ids_from_sample(sample)
        rows.append(
            {
                "dataset": dataset or "unknown",
                "model_name": model or "unknown",
                "condition": method,
                "sample_id": sid,
                "rule_failure_label": failure,
                "question": _sample_question(sample, max_text_chars),
                "gold_answer": _sample_gold_answer(sample, max_text_chars),
                "predicted_answer": pred_answer,
                "gold_evidence_ids": json.dumps(gold_evidence_ids, ensure_ascii=False),
                "predicted_evidence_ids": json.dumps(pred_evidence_ids, ensure_ascii=False),
                "gold_evidence_text": _texts_for_ids(sample, gold_evidence_ids, max_text_chars),
                "predicted_evidence_text": _texts_for_ids(sample, pred_evidence_ids, max_text_chars),
                "model_explanation": _guess_explanation(pred, max_chars=max_text_chars),
                "metrics_file": row.get("__metrics_file", ""),
                "run_name": row.get("__run_name", ""),
                "row_hash": _row_hash(row),
            }
        )
    if not rows:
        raise RuntimeError("No failed predictions were found after filtering.")
    return pd.DataFrame(rows)


def _infer_dataset_from_run_name(name: str) -> str:
    lower = name.lower()
    if "twowiki" in lower or "2wiki" in lower:
        return "2wikimultihopqa"
    if "hotpot" in lower:
        return "hotpotqa"
    if "controlled" in lower or "scaling" in lower:
        return "controlled"
    if "babilong" in lower:
        return "babilong"
    return name or "unknown"


def _infer_model_from_run_name(name: str) -> str:
    lower = name.lower()
    if "qwen25" in lower or "qwen2.5" in lower:
        return "qwen2.5:14b"
    if "qwen3" in lower:
        return "qwen3:14b"
    if "gemma3" in lower:
        return "gemma3:12b"
    return "unknown"


def _row_hash(row: dict[str, Any]) -> str:
    fields = [str(row.get(k, "")) for k in ["sample_id", "method", "failure_type", "__run_name"]]
    return hashlib.sha1("|".join(fields).encode("utf-8")).hexdigest()[:12]


def _stratified_round_robin_sample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    df = df.copy()
    df["stratum"] = (
        df["dataset"].astype(str)
        + "|"
        + df["model_name"].astype(str)
        + "|"
        + df["condition"].astype(str)
        + "|"
        + df["rule_failure_label"].astype(str)
    )
    groups: dict[str, list[int]] = {}
    for stratum, sub in df.groupby("stratum", sort=True):
        indices = list(sub.index)
        rng.shuffle(indices)
        groups[stratum] = indices

    selected: list[int] = []
    strata = list(groups.keys())
    rng.shuffle(strata)
    while len(selected) < min(n, len(df)):
        made_progress = False
        for s in list(strata):
            if len(selected) >= min(n, len(df)):
                break
            if groups[s]:
                selected.append(groups[s].pop())
                made_progress = True
        if not made_progress:
            break
    sampled = df.loc[selected].copy()
    sampled = sampled.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    sampled.insert(0, "audit_id", [f"FTAX-{i:04d}" for i in range(1, len(sampled) + 1)])
    return sampled.drop(columns=["stratum"], errors="ignore")


def _write_codebook(path: Path) -> None:
    content = """# Failure Taxonomy Human-Validation Codebook

Annotators should assign exactly one label to each failed prediction. Do not use the rule-based label or aggregate experiment results when annotating.

## Labels

- `localization`: The predicted evidence does not include the needed supporting evidence.
- `selection`: The predicted evidence includes some relevant evidence but misses required support, includes distractors, or gives an incomplete evidence chain.
- `integration`: The predicted evidence contains the required evidence, but the answer fails because the model does not combine the evidence correctly.
- `conversion`: The predicted evidence supports the answer, but the final response has the wrong entity, number, format, comparison direction, or normalized answer form.
- `parse_format`: The output is not reliably interpretable under the structured answer/evidence contract.
- `ambiguous`: More than one failure mode is plausible, or the available fields are insufficient to assign a confident single label.

## Recommended procedure

1. Read the question and gold answer.
2. Inspect the predicted answer.
3. Compare the gold evidence text and predicted evidence text.
4. Assign the earliest clear bottleneck only when confident.
5. Use `ambiguous` for boundary cases instead of forcing a label.

## Confidence

Use `high`, `medium`, or `low`. Add a short note for low-confidence decisions.
"""
    path.write_text(content, encoding="utf-8")

def _write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def export_audit(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    out_dir = (root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pool = _build_candidate_pool(
        root=root,
        max_text_chars=args.max_text_chars,
        include_no_evidence=args.include_no_evidence,
    )
    sampled = _stratified_round_robin_sample(pool, n=args.sample_size, seed=args.seed)

    key_cols = list(sampled.columns)
    blind_cols = [c for c in key_cols if c != "rule_failure_label"]
    blind = sampled[blind_cols].copy()

    annotator_a = blind.copy()
    annotator_a["human_label_annotator_a"] = ""
    annotator_a["confidence_annotator_a"] = ""
    annotator_a["notes_annotator_a"] = ""

    annotator_b = blind.copy()
    annotator_b["human_label_annotator_b"] = ""
    annotator_b["confidence_annotator_b"] = ""
    annotator_b["notes_annotator_b"] = ""

    _write_csv(out_dir / "failure_taxonomy_audit_sample_blind.csv", blind)
    _write_csv(out_dir / "failure_taxonomy_audit_sample_key.csv", sampled)
    _write_csv(out_dir / "failure_taxonomy_annotator_a.csv", annotator_a)
    _write_csv(out_dir / "failure_taxonomy_annotator_b.csv", annotator_b)
    _write_codebook(out_dir / "failure_taxonomy_annotation_codebook.md")

    stratum_summary = (
        sampled.groupby(["dataset", "model_name", "condition", "rule_failure_label"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["dataset", "model_name", "condition", "rule_failure_label"])
    )
    _write_csv(out_dir / "failure_taxonomy_audit_strata.csv", stratum_summary)

    manifest = {
        "task": "failure_taxonomy_human_validation_export",
        "sample_size_requested": args.sample_size,
        "sample_size_exported": int(len(sampled)),
        "seed": args.seed,
        "include_no_evidence": bool(args.include_no_evidence),
        "labels": LABELS,
        "outputs": [
            "failure_taxonomy_audit_sample_blind.csv",
            "failure_taxonomy_audit_sample_key.csv",
            "failure_taxonomy_annotator_a.csv",
            "failure_taxonomy_annotator_b.csv",
            "failure_taxonomy_annotation_codebook.md",
            "failure_taxonomy_audit_strata.csv",
        ],
    }
    (out_dir / "failure_taxonomy_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Wrote failure-taxonomy human-validation audit files to {out_dir}")
    print(f"candidate failed predictions: {len(pool)}")
    print(f"exported audit sample: {len(sampled)}")
    print(f"strata represented: {len(stratum_summary)}")


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument(
        "--output-dir",
        default="experiment_backups/failure_taxonomy_human_validation_20260530",
        help="Output directory relative to repo root.",
    )
    parser.add_argument("--sample-size", type=int, default=300, help="Number of failed predictions to sample.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible sampling.")
    parser.add_argument(
        "--max-text-chars",
        type=int,
        default=1800,
        help="Maximum characters retained for question/evidence/explanation fields.",
    )
    parser.add_argument(
        "--include-no-evidence",
        action="store_true",
        help="Include no-evidence failed predictions. Default excludes them because the taxonomy validates contextual failures.",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    export_audit(args)


if __name__ == "__main__":
    main()
