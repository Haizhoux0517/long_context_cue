#!/usr/bin/env python3
"""Run RULER-lite external answer-performance validation with Ollama.

This script evaluates full-context and retrieved-context conditions.  It does
not compute ONCU because RULER-lite is used as an external validation setting,
not as an oracle-normalized benchmark.

Outputs:
    <output_dir>/predictions.jsonl
    <output_dir>/per_sample_metrics.csv
    <output_dir>/run_manifest.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import string
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


_WORD_RE = re.compile(r"[A-Za-z0-9\-]+")


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def normalize_answer(x: object) -> str:
    text = str(x or "").strip().lower()
    text = text.replace("_", " ")
    # Keep hyphen inside synthetic codes but remove other punctuation.
    allowed = set(string.ascii_lowercase + string.digits + " -")
    text = "".join(ch if ch in allowed else " " for ch in text)
    return " ".join(text.split())


def token_f1(pred: object, gold: object) -> float:
    p = normalize_answer(pred).split()
    g = normalize_answer(gold).split()
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    pc = Counter(p)
    gc = Counter(g)
    common = sum((pc & gc).values())
    if common == 0:
        return 0.0
    precision = common / max(1, len(p))
    recall = common / max(1, len(g))
    return 2 * precision * recall / max(1e-12, precision + recall)


def exact_match(pred: object, gold: object) -> float:
    return float(normalize_answer(pred) == normalize_answer(gold))


def split_passages(context: str) -> List[str]:
    parts = [p.strip() for p in str(context).split("\n\n") if p.strip()]
    return parts or [str(context)]


def lexical_score(query: str, passage: str) -> float:
    q_terms = _WORD_RE.findall(query.lower())
    p_terms = _WORD_RE.findall(passage.lower())
    if not q_terms or not p_terms:
        return 0.0
    p_counts = Counter(p_terms)
    score = 0.0
    for term in q_terms:
        if term in p_counts:
            # Light IDF-like boost for synthetic identifiers and numbers.
            boost = 3.0 if any(ch.isdigit() for ch in term) or "-" in term else 1.0
            score += boost * min(3, p_counts[term])
    return score / math.sqrt(len(p_terms))


def retrieve_context(sample: Dict[str, object], top_k: int = 3) -> str:
    question = str(sample["question"])
    passages = split_passages(str(sample["context"]))
    scored = [(lexical_score(question, p), i, p) for i, p in enumerate(passages)]
    scored.sort(key=lambda x: (-x[0], x[1]))

    selected = [p for score, _, p in scored[:top_k] if score > 0]
    if not selected:
        selected = [p for _, _, p in scored[:top_k]]
    return "\n\n".join(selected)


def build_prompt(sample: Dict[str, object], condition: str, top_k: int) -> str:
    if condition == "full_context":
        context = str(sample["context"])
    elif condition == "retrieved_context":
        context = retrieve_context(sample, top_k=top_k)
    else:
        raise ValueError(f"Unsupported condition: {condition}")

    return f"""You are evaluating a long-context question-answering example.

Instructions:
- Answer using only the provided context.
- Return ONLY a valid JSON object.
- The JSON object must have exactly these keys: "answer", "explanation".
- The answer should be concise. If the question asks for a code or number, return only that code or number in "answer".

Question:
{sample['question']}

Context:
{context}

JSON answer:
"""


def _extract_json_object(text: str) -> Optional[Dict[str, object]]:
    if not isinstance(text, str):
        return None
    s = text.strip()

    # Strip common fenced-code wrappers.
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        s = fence_match.group(1).strip()

    # Try direct parse first.
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Fall back to the first balanced-ish object span.
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = s[start : end + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            return None
    return None


def parse_model_output(text: str) -> Tuple[str, str, bool]:
    obj = _extract_json_object(text)
    if obj is None:
        return "", "", True
    answer = obj.get("answer", "")
    explanation = obj.get("explanation", "")
    return str(answer), str(explanation), False


def ollama_generate(
    *,
    model: str,
    prompt: str,
    ollama_url: str,
    temperature: float,
    num_ctx: int,
    num_predict: int,
    timeout: int,
) -> str:
    effective_num_predict = max(num_predict, 256) if str(model).startswith("qwen3") else num_predict

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": num_ctx,
            "num_predict": effective_num_predict,
        },
    }

    # Qwen3 in Ollama can place generated tokens in the auxiliary "thinking"
    # field and leave "response" empty when thinking is enabled. For this
    # short-answer JSON evaluation, disable thinking so the answer appears in
    # the normal response field.
    if str(model).startswith("qwen3"):
        payload["think"] = False

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        ollama_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            obj = json.loads(raw)
            return str(obj.get("response", ""))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed for model={model}: {exc}") from exc

def existing_keys(predictions_path: Path) -> set[Tuple[str, str, str]]:
    keys: set[Tuple[str, str, str]] = set()
    if not predictions_path.exists():
        return keys
    with predictions_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            keys.add((str(row["model_name"]), str(row["condition"]), str(row["sample_id"])))
    return keys


def append_jsonl(path: Path, row: Dict[str, object]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_metrics_csv(predictions_path: Path, metrics_path: Path) -> None:
    fields = [
        "model_name",
        "condition",
        "sample_id",
        "dataset_name",
        "task_name",
        "task_category",
        "context_length",
        "evidence_position",
        "gold_answer",
        "predicted_answer",
        "exact_match",
        "answer_f1",
        "parse_failure",
    ]
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with predictions_path.open("r", encoding="utf-8") as fin, metrics_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()
        for line in fin:
            if not line.strip():
                continue
            row = json.loads(line)
            writer.writerow({k: row.get(k, "") for k in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/ruler_lite_240.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/ruler_lite_external"))
    parser.add_argument("--models", nargs="+", default=["qwen2.5:14b", "qwen3:14b", "gemma3:12b"])
    parser.add_argument("--conditions", nargs="+", default=["full_context", "retrieved_context"])
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--ollama-url", default="http://localhost:11434/api/generate")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--num-predict", type=int, default=128)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    samples = load_jsonl(args.input)
    if args.limit is not None:
        samples = samples[: args.limit]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output_dir / "predictions.jsonl"
    metrics_path = args.output_dir / "per_sample_metrics.csv"

    seen = existing_keys(predictions_path) if args.resume else set()
    total = len(samples) * len(args.models) * len(args.conditions)
    done = 0
    started = time.time()

    for model in args.models:
        for condition in args.conditions:
            for sample in samples:
                key = (model, condition, str(sample["sample_id"]))
                if key in seen:
                    done += 1
                    continue

                prompt = build_prompt(sample, condition, top_k=args.top_k)
                raw_output = ollama_generate(
                    model=model,
                    prompt=prompt,
                    ollama_url=args.ollama_url,
                    temperature=args.temperature,
                    num_ctx=args.num_ctx,
                    num_predict=args.num_predict,
                    timeout=args.timeout,
                )
                pred_answer, explanation, parse_failure = parse_model_output(raw_output)
                gold = sample["gold_answer"]

                out = {
                    "model_name": model,
                    "condition": condition,
                    "sample_id": sample["sample_id"],
                    "dataset_name": sample.get("dataset_name", "ruler_lite_external"),
                    "task_name": sample["task_name"],
                    "task_category": sample["task_category"],
                    "context_length": sample["context_length"],
                    "evidence_position": sample["evidence_position"],
                    "question": sample["question"],
                    "gold_answer": gold,
                    "predicted_answer": pred_answer,
                    "explanation": explanation,
                    "raw_output": raw_output,
                    "exact_match": exact_match(pred_answer, gold),
                    "answer_f1": token_f1(pred_answer, gold),
                    "parse_failure": int(parse_failure),
                }
                append_jsonl(predictions_path, out)

                done += 1
                if done % 10 == 0 or done == total:
                    elapsed = time.time() - started
                    rate = done / max(1e-9, elapsed)
                    print(f"Progress {done}/{total} ({done/total:.1%}), {rate:.2f} pred/s, model={model}, condition={condition}", flush=True)

    write_metrics_csv(predictions_path, metrics_path)

    manifest = {
        "input": str(args.input),
        "output_dir": str(args.output_dir),
        "models": args.models,
        "conditions": args.conditions,
        "top_k": args.top_k,
        "num_samples": len(samples),
        "num_predictions_expected": total,
        "ollama_url": args.ollama_url,
        "temperature": args.temperature,
        "num_ctx": args.num_ctx,
        "num_predict": args.num_predict,
        "role": "External answer-performance validation; not ONCU.",
    }
    (args.output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote predictions to {predictions_path}")
    print(f"Wrote metrics to {metrics_path}")
    print(f"Wrote manifest to {args.output_dir / 'run_manifest.json'}")


if __name__ == "__main__":
    main()
