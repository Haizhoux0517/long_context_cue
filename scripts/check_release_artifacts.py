#!/usr/bin/env python3
"""Check release artifacts for the ONCU diagnostic paper repository.

Default mode checks released code, configs, scripts, and frozen result summaries.
Use --strict-data to require the processed JSONL inputs referenced by the paper.
Use --strict-clean to fail on stale root-level duplicate/revision documents that
can confuse reviewers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Artifact:
    path: str
    kind: str = "file"  # "file", "dir", "glob", or "absent"
    required: bool = True
    note: str = ""


def _exists(root: Path, artifact: Artifact) -> bool:
    target = root / artifact.path
    if artifact.kind == "file":
        return target.is_file()
    if artifact.kind == "dir":
        return target.is_dir()
    if artifact.kind == "glob":
        return any(root.glob(artifact.path))
    if artifact.kind == "absent":
        return not target.exists()
    raise ValueError(f"Unknown artifact kind: {artifact.kind}")


def _check_group(root: Path, title: str, artifacts: Iterable[Artifact]) -> tuple[int, int, list[str], list[dict[str, object]]]:
    missing_required = 0
    checked = 0
    lines: list[str] = [f"\n[{title}]"]
    artifact_records: list[dict[str, object]] = []

    for artifact in artifacts:
        checked += 1
        ok = _exists(root, artifact)

        if artifact.kind == "absent":
            status = "OK-ABSENT" if ok else ("STALE-PRESENT" if artifact.required else "OPTIONAL-PRESENT")
        else:
            status = "OK" if ok else ("MISSING" if artifact.required else "OPTIONAL-MISSING")

        lines.append(f"  {status:18s} {artifact.path}")
        if artifact.note:
            lines.append(f"    note: {artifact.note}")

        if artifact.required and not ok:
            missing_required += 1

        artifact_records.append(
            {
                "path": artifact.path,
                "kind": artifact.kind,
                "required": artifact.required,
                "ok": ok,
                "note": artifact.note,
            }
        )

    return checked, missing_required, lines, artifact_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Check release artifacts for the ONCU diagnostic repository.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument(
        "--strict-data",
        action="store_true",
        help="Require generated data/processed/*.jsonl runtime inputs to exist.",
    )
    parser.add_argument(
        "--strict-clean",
        action="store_true",
        help="Fail if stale root-level duplicate/revision documents are present.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / "longcue").is_dir() or not (root / "scripts").is_dir():
        print(f"ERROR: {root} does not look like the long_context_cue repository root.", file=sys.stderr)
        return 2

    groups: dict[str, list[Artifact]] = {
        "top-level reproducibility files": [
            Artifact("README.md"),
            Artifact("README_REPRODUCE.md"),
            Artifact("ARTIFACT_MANIFEST.md"),
            Artifact("requirements.txt"),
            Artifact("pyproject.toml"),
        ],
        "core package": [
            Artifact("longcue/run_experiment.py"),
            Artifact("longcue/protocol.py"),
            Artifact("longcue/evaluation/answer_metrics.py"),
            Artifact("longcue/evaluation/evidence_metrics.py"),
            Artifact("longcue/evaluation/oncu.py"),
            Artifact("longcue/evaluation/failure_diagnosis.py"),
            Artifact("longcue/methods/retrieve_then_read.py"),
            Artifact("longcue/models/ollama.py"),
        ],
        "dataset builders and adapters": [
            Artifact("scripts/build_controlled_cue.py"),
            Artifact("scripts/build_hotpotqa_cue.py"),
            Artifact("scripts/build_babilong_cue.py"),
            Artifact("longcue/data/controlled_generator.py"),
            Artifact("longcue/data/hotpotqa_adapter.py"),
            Artifact("longcue/data/babilong_adapter.py"),
        ],
        "validation and summary scripts": [
            Artifact("scripts/validate_diagnostic_protocol.py"),
            Artifact("scripts/recompute_oncu.py"),
            Artifact("scripts/bootstrap_sci200_final_ci.py"),
            Artifact("scripts/bootstrap_hotpotqa500_robustness_ci.py"),
            Artifact("scripts/bootstrap_babilong200_external_ci.py"),
            Artifact("scripts/summarize_sci200_failure_breakdown.py"),
            Artifact("scripts/check_release_artifacts.py"),
        ],
        "final 200-sample configs": [
            Artifact("configs/controlled_safe16k_qwen25_14b_200_core_final.yaml"),
            Artifact("configs/controlled_safe16k_qwen3_14b_200_core_final.yaml"),
            Artifact("configs/controlled_safe16k_gemma3_12b_200_core_final.yaml"),
            Artifact("configs/hotpotqa_qwen25_14b_200_core_final.yaml"),
            Artifact("configs/hotpotqa_qwen3_14b_200_core_final.yaml"),
            Artifact("configs/hotpotqa_gemma3_12b_200_core_final.yaml"),
        ],
        "HotpotQA robustness and ablation configs": [
            Artifact("configs/hotpotqa_qwen25_14b_500_core_robust.yaml"),
            Artifact("configs/hotpotqa_qwen3_14b_500_core_robust.yaml"),
            Artifact("configs/hotpotqa_gemma3_12b_500_core_robust.yaml"),
            Artifact("configs/hotpotqa_qwen25_14b_200_topk5_ablation.yaml"),
            Artifact("configs/hotpotqa_qwen25_14b_200_topk8_ablation.yaml"),
            Artifact("configs/hotpotqa_qwen3_14b_200_topk5_ablation.yaml"),
            Artifact("configs/hotpotqa_qwen3_14b_200_topk8_ablation.yaml"),
        ],
        "BABILong external configs": [
            Artifact("configs/babilong_qwen25_14b_200_external.yaml"),
            Artifact("configs/babilong_qwen3_14b_200_external.yaml"),
            Artifact("configs/babilong_gemma3_12b_200_external.yaml"),
        ],
        "final 200-sample frozen results": [
            Artifact("experiment_backups/sci200_final_3model_20260525", "dir"),
            Artifact("experiment_backups/sci200_final_3model_20260525/summary/sci200_answer_evidence_summary.csv"),
            Artifact("experiment_backups/sci200_final_3model_20260525/summary/sci200_oncu_relaxed_f1_summary.csv"),
            Artifact("experiment_backups/sci200_final_3model_20260525/ci/sci200_metric_bootstrap_ci.csv"),
            Artifact("experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_bootstrap_ci.csv"),
            Artifact("experiment_backups/sci200_final_3model_20260525/ci/sci200_oncu_ci_compact.csv"),
            Artifact("experiment_backups/sci200_final_3model_20260525/failure_analysis/sci200_failure_breakdown_contextual_compact.csv"),
            Artifact("experiment_backups/sci200_final_3model_20260525/*/protocol_manifest.json", "glob"),
            Artifact("experiment_backups/sci200_final_3model_20260525/*/resolved_config.json", "glob"),
        ],
        "HotpotQA-500 frozen results": [
            Artifact("experiment_backups/hotpotqa_500_robustness_20260525", "dir"),
            Artifact("experiment_backups/hotpotqa_500_robustness_20260525/hotpotqa_200_vs_500_robustness_summary.csv"),
            Artifact("experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_metric_bootstrap_ci.csv"),
            Artifact("experiment_backups/hotpotqa_500_robustness_20260525/ci/hotpotqa500_oncu_bootstrap_ci.csv"),
            Artifact("experiment_backups/hotpotqa_500_robustness_20260525/final_tables/hotpotqa_200_vs_500_with_ci.csv"),
        ],
        "BABILong-200 frozen results": [
            Artifact("experiment_backups/babilong_200_external_20260526", "dir"),
            Artifact("experiment_backups/babilong_200_external_20260526/babilong_200_external_summary.csv"),
            Artifact("experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv"),
            Artifact("experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv"),
        ],
    }

    if args.strict_data:
        groups["generated processed inputs"] = [
            Artifact("data/processed/controlled_oncu_200_safe16k.jsonl"),
            Artifact("data/processed/hotpotqa_cue_200.jsonl"),
            Artifact("data/processed/hotpotqa_cue_500.jsonl"),
            Artifact("data/processed/babilong_cue_200_external.jsonl"),
        ]

    stale_docs = [
        Artifact(
            "README_REPRODUCE_updated.md",
            "absent",
            required=args.strict_clean,
            note="Duplicate draft; merge into README_REPRODUCE.md and remove from release root.",
        ),
        Artifact(
            "README_PATCH.md",
            "absent",
            required=args.strict_clean,
            note="Historical patch note; move to docs/archive/ or remove from release root.",
        ),
        Artifact(
            "README_DIAGNOSTIC_REFACTOR.md",
            "absent",
            required=args.strict_clean,
            note="Historical refactor note; move to docs/archive/ or remove from release root.",
        ),
    ]
    groups["root cleanliness warnings"] = stale_docs

    historical_backups = [
        Artifact(
            "experiment_backups/core_2x2_qwen25_qwen3_20260524",
            "dir",
            required=False,
            note="Historical intermediate backup, not a final paper artifact.",
        ),
        Artifact(
            "experiment_backups/sci200_partial_qwen25_20260525",
            "dir",
            required=False,
            note="Historical partial backup, not a final paper artifact.",
        ),
        Artifact(
            "experiment_backups/sci200_qwen_family_20260525",
            "dir",
            required=False,
            note="Historical Qwen-family backup, not a final paper artifact.",
        ),
    ]
    groups["historical backup warnings"] = historical_backups

    total_checked = 0
    total_missing = 0
    output_lines: list[str] = [f"Checking release artifacts under: {root}"]
    json_groups: dict[str, dict[str, object]] = {}

    for title, artifacts in groups.items():
        checked, missing, lines, records = _check_group(root, title, artifacts)
        total_checked += checked
        total_missing += missing
        output_lines.extend(lines)
        json_groups[title] = {
            "checked": checked,
            "missing_required": missing,
            "artifacts": records,
        }

    summary = {
        "root": str(root),
        "strict_data": bool(args.strict_data),
        "strict_clean": bool(args.strict_clean),
        "checked": total_checked,
        "missing_required": total_missing,
        "ok": total_missing == 0,
        "groups": json_groups,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("\n".join(output_lines))
        print("\n[summary]")
        print(f"  checked: {total_checked}")
        print(f"  missing required: {total_missing}")
        print("  result:", "PASS" if total_missing == 0 else "FAIL")
        if not args.strict_data:
            print("\nNote: generated data/processed/*.jsonl inputs were not required. Use --strict-data to require them.")
        if not args.strict_clean:
            print("Note: root-level duplicate/revision documents are warnings only. Use --strict-clean to fail on them.")

    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
