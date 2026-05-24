from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from longcue.protocol import CORE_DIAGNOSTIC_METHODS, METHOD_SPECS, PROMPT_PROTOCOL_VERSION


FORBIDDEN_CONFIG_KEYS = {
    "prompt",
    "prompts",
    "prompt_template",
    "template_override",
    "model_specific_prompt",
}


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def _walk_forbidden(obj: Any, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_str = str(key)
            here = f"{prefix}.{key_str}" if prefix else key_str
            if key_str in FORBIDDEN_CONFIG_KEYS:
                hits.append(here)
            hits.extend(_walk_forbidden(value, here))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            hits.extend(_walk_forbidden(value, f"{prefix}[{i}]"))
    return hits


def validate(path: Path, *, require_core: bool = False) -> list[str]:
    cfg = _load(path)
    issues: list[str] = []

    methods = cfg.get("methods", [])
    if not isinstance(methods, list) or not methods:
        issues.append("methods must be a non-empty list")
    else:
        unknown = sorted(set(map(str, methods)).difference(METHOD_SPECS))
        if unknown:
            issues.append(f"unknown methods: {unknown}")
        if require_core:
            missing = [m for m in CORE_DIAGNOSTIC_METHODS if m not in methods]
            if missing:
                issues.append(f"missing core diagnostic methods: {missing}")

    generation = cfg.get("generation", {}) or {}
    if float(generation.get("temperature", 0.0)) != 0.0:
        issues.append("generation.temperature should be 0.0 for deterministic diagnostics")

    model = cfg.get("model", {}) or {}
    if str(model.get("provider", "")).lower() == "ollama" and "num_ctx" not in model:
        issues.append("Ollama configs should set model.num_ctx explicitly to avoid backend truncation ambiguity")

    forbidden = _walk_forbidden(cfg)
    if forbidden:
        issues.append("config contains prompt/template override keys: " + ", ".join(forbidden))

    protocol = cfg.get("protocol", {}) or {}
    if protocol and str(protocol.get("version", PROMPT_PROTOCOL_VERSION)) != PROMPT_PROTOCOL_VERSION:
        issues.append(f"protocol.version should be {PROMPT_PROTOCOL_VERSION}")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate fixed diagnostic protocol configs.")
    parser.add_argument("configs", nargs="+", help="YAML config paths")
    parser.add_argument("--require-core", action="store_true", help="Require no/full/retrieval/oracle methods")
    args = parser.parse_args()

    failed = False
    for raw in args.configs:
        path = Path(raw)
        issues = validate(path, require_core=args.require_core)
        if issues:
            failed = True
            print(f"[FAIL] {path}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[OK] {path}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
