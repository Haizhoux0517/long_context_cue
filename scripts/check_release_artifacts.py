#!/usr/bin/env python3
"""Check release artifacts for the ONCU diagnostic paper repository.

Default mode checks released code, configs, scripts, frozen result summaries,
and auxiliary summary/config artifacts referenced by the paper.
Use --strict-data to require the released processed JSONL inputs. Generated
auxiliary inputs are rebuilt from released builders before rerunning those audits.
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
    parser.add_argument(
        "--strict-longbench",
        action="store_true",
        help="Require optional LongBench generated inputs/results after those exploratory runs are completed.",
    )
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
            Artifact("DATA_LICENSES.md"),
            Artifact("RUNTIME_REPRODUCIBILITY_RECORD.md"),
            Artifact("runtime_reproducibility_record.json"),
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
            Artifact("longcue/methods/retrievers.py"),
            Artifact("longcue/methods/ce_reranker.py"),
            Artifact("longcue/models/ollama.py"),
        ],
        "dataset builders and adapters": [
            Artifact("scripts/build_controlled_cue.py"),
            Artifact("scripts/build_controlled_scaling_cue.py"),
            Artifact("scripts/build_hotpotqa_cue.py"),
            Artifact("scripts/build_2wiki_cue.py"),
            Artifact("scripts/build_babilong_cue.py"),
            Artifact("scripts/build_ruler_lite.py"),
            Artifact("longcue/data/controlled_generator.py"),
            Artifact("longcue/data/hotpotqa_adapter.py"),
            Artifact("longcue/data/twowiki_adapter.py"),
            Artifact("longcue/data/babilong_adapter.py"),
            Artifact("longcue/data/ruler_adapter.py"),
        ],
        "validation and summary scripts": [
            Artifact("scripts/export_runtime_record.py"),
            Artifact("scripts/validate_diagnostic_protocol.py"),
            Artifact("scripts/recompute_oncu.py"),
            Artifact("scripts/recompute_twowiki500_tables.py"),
            Artifact("scripts/run_retriever_family_ablation.py"),
            Artifact("scripts/prepare_retriever_family_oncu_sensitivity.py"),
            Artifact("scripts/summarize_reader_facing_retriever_results.py"),
            Artifact("scripts/prepare_ce_rerank_sensitivity.py"),
            Artifact("scripts/summarize_ce_rerank_five_model.py"),
            Artifact("scripts/run_ruler_lite_external.py"),
            Artifact("scripts/summarize_ruler_lite_external.py"),
            Artifact("scripts/summarize_controlled_scaling.py"),
            Artifact("scripts/statistical_modeling.py"),
            Artifact("scripts/metric_comparison_summary.py"),
            Artifact("scripts/export_failure_taxonomy_audit.py"),
            Artifact("scripts/summarize_failure_taxonomy_audit.py"),
            Artifact("scripts/bootstrap_sci200_final_ci.py"),
            Artifact("scripts/bootstrap_hotpotqa500_robustness_ci.py"),
            Artifact("scripts/bootstrap_babilong200_external_ci.py"),
            Artifact("scripts/summarize_sci200_failure_breakdown.py"),
            Artifact("scripts/check_release_artifacts.py"),
        ],
        "controlled scaling configs": [
            Artifact("configs/scaling/controlled_scaling_qwen25_14b_3200.yaml"),
            Artifact("configs/scaling/controlled_scaling_qwen3_14b_3200.yaml"),
            Artifact("configs/scaling/controlled_scaling_gemma3_12b_3200.yaml"),
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
        "2WikiMultiHopQA JAIR-extension configs": [
            Artifact("configs/twowiki_qwen25_14b_500_core.yaml"),
            Artifact("configs/twowiki_qwen3_14b_500_core.yaml"),
            Artifact("configs/twowiki_gemma3_12b_500_core.yaml"),
        ],
        "retriever-family ablation configs": [
            Artifact("configs/ablations/retriever_family_hotpotqa_qwen25.yaml"),
            Artifact("configs/ablations/retriever_family_twowiki_qwen25.yaml"),
        ],
        "model-family extension configs": [
            Artifact("configs/model_family_extension/*.yaml", "glob"),
        ],
        "retriever-family ONCU sensitivity configs": [
            Artifact("configs/retriever_family_oncu_sensitivity/*.yaml", "glob"),
        ],
        "reader-facing retriever configs": [
            Artifact("configs/ablations/reader_facing_retfam_*.yaml", "glob"),
        ],
        "cross-encoder reranking summary/config artifacts": [
            Artifact("RUN_CE_RERANK_CONFIG_LIST.sh"),
            Artifact("configs/rerank_sensitivity/ce_reader_facing/*.yaml", "glob"),
            Artifact("configs/rerank_sensitivity/config_lists/*.txt", "glob"),
            Artifact("experiment_backups/rerank_sensitivity_20260602/five_model_ce_rerank_summary/five_model_ce_rerank_all_rows.csv"),
            Artifact("experiment_backups/rerank_sensitivity_20260602/five_model_ce_rerank_summary/five_model_ce_rerank_best_answer_rows.csv"),
            Artifact("experiment_backups/rerank_sensitivity_20260602/five_model_ce_rerank_summary/five_model_ce_rerank_best_answer_table.tex"),
            Artifact("experiment_backups/rerank_sensitivity_20260602/five_model_ce_rerank_summary/five_model_ce_rerank_best_oncu_rows.csv"),
        ],
        "LongBench external validation configs": [
            Artifact("configs/longbench_qwen25_14b_300_external.yaml"),
            Artifact("configs/longbench_qwen3_14b_300_external.yaml"),
            Artifact("configs/longbench_gemma3_12b_300_external.yaml"),
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
        "2WikiMultiHopQA-500 frozen results": [
            Artifact("experiment_backups/twowiki_500_validation_20260527", "dir"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/summary/twowiki_condition_summary.csv"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/summary/twowiki_oncu_relaxed_f1_summary.csv"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/ci/twowiki_oncu_relaxed_f1_bootstrap_ci.csv"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/failure_analysis/twowiki_failure_breakdown_long.csv"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/final_tables/twowiki_main_results_table.tex"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/final_tables/twowiki_oncu_results_table.tex"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/final_tables/twowiki_failure_breakdown_table.tex"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/per_model/*/protocol_manifest.json", "glob"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/per_model/*/resolved_config.json", "glob"),
            Artifact("experiment_backups/twowiki_500_validation_20260527/per_model/*/per_sample_metrics.csv", "glob"),
        ],
        "BABILong-200 frozen results": [
            Artifact("experiment_backups/babilong_200_external_20260526", "dir"),
            Artifact("experiment_backups/babilong_200_external_20260526/babilong_200_external_summary.csv"),
            Artifact("experiment_backups/babilong_200_external_20260526/ci/babilong200_metric_bootstrap_ci.csv"),
            Artifact("experiment_backups/babilong_200_external_20260526/final_tables/babilong200_external_ci_compact.csv"),
        ],
        "statistical modeling support artifacts": [
            Artifact("experiment_backups/statistical_modeling_20260530", "dir"),
            Artifact("experiment_backups/statistical_modeling_20260530/statistical_effects_summary.csv"),
            Artifact("experiment_backups/statistical_modeling_20260530/statistical_effects_table.tex"),
            Artifact("experiment_backups/statistical_modeling_20260530/statistical_regression_summary.csv"),
            Artifact("experiment_backups/statistical_modeling_20260530/statistical_regression_table.tex"),
            Artifact("experiment_backups/statistical_modeling_20260530/statistical_modeling_manifest.json"),
        ],
        "model-family extension frozen results": [
            Artifact("model_family_extension_for_paper.tar.gz"),
            Artifact("experiment_backups/model_family_extension_20260601", "dir"),
            Artifact("experiment_backups/model_family_extension_20260601/*/protocol_manifest.json", "glob"),
            Artifact("experiment_backups/model_family_extension_20260601/*/resolved_config.json", "glob"),
            Artifact("experiment_backups/model_family_extension_20260601/*/results/per_sample_metrics.csv", "glob"),
            Artifact("experiment_backups/model_family_extension_20260601/*/results/cue_metrics.csv", "glob"),
            Artifact("experiment_backups/model_family_extension_20260601/*/results/aggregate_metrics.csv", "glob"),
        ],
        "matched retriever-family ONCU sensitivity frozen results": [
            Artifact("experiment_backups/retriever_family_oncu_sensitivity_20260602", "dir"),
            Artifact("experiment_backups/retriever_family_oncu_sensitivity_20260602/*/protocol_manifest.json", "glob"),
            Artifact("experiment_backups/retriever_family_oncu_sensitivity_20260602/*/resolved_config.json", "glob"),
            Artifact("experiment_backups/retriever_family_oncu_sensitivity_20260602/*/results/per_sample_metrics.csv", "glob"),
            Artifact("experiment_backups/retriever_family_oncu_sensitivity_20260602/*/results/cue_metrics.csv", "glob"),
            Artifact("experiment_backups/retriever_family_oncu_sensitivity_20260602/*/results/aggregate_metrics.csv", "glob"),
        ],
        "retriever-only and reader-facing audit summaries": [
            Artifact("reader_facing_summary_for_paper.tar.gz"),
            Artifact("experiment_backups/retriever_family_ablation_20260527/*/retrieval_only_per_sample.csv", "glob"),
            Artifact("experiment_backups/retriever_family_ablation_20260527/*/retrieval_only_summary.csv", "glob"),
            Artifact("experiment_backups/reader_facing_retriever_family_20260530/reader_facing_condition_summary.csv"),
            Artifact("experiment_backups/reader_facing_retriever_family_20260530/reader_facing_joined_summary.csv"),
            Artifact("experiment_backups/reader_facing_retriever_family_20260530/reader_facing_winners.csv"),
            Artifact("experiment_backups/reader_facing_retriever_family_20260530/reader_facing_retfam_results_table.tex"),
        ],
        "controlled scaling and RULER-lite auxiliary summaries": [
            Artifact("experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_oncu_by_length_position.csv"),
            Artifact("experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_regression.csv"),
            Artifact("experiment_backups/controlled_scaling_20260527/summary/controlled_scaling_summary_manifest.json"),
            Artifact("experiment_backups/ruler_lite_external_20260530_final/ruler_lite_condition_summary.csv"),
            Artifact("experiment_backups/ruler_lite_external_20260530_final/ruler_lite_model_summary.csv"),
        ],
        "failure taxonomy and metric-comparison audits": [
            Artifact("experiment_backups/failure_taxonomy_human_validation_20260530/failure_taxonomy_final_summary.csv"),
            Artifact("experiment_backups/failure_taxonomy_human_validation_20260530/failure_taxonomy_human_validation_table.tex"),
            Artifact("experiment_backups/failure_taxonomy_human_validation_20260530/failure_taxonomy_final_manifest.json"),
            Artifact("experiment_backups/metric_comparison_20260530/metric_comparison_condition_summary.csv"),
            Artifact("experiment_backups/metric_comparison_20260530/metric_comparison_case_studies.csv"),
            Artifact("experiment_backups/metric_comparison_20260530/metric_comparison_manifest.json"),
        ],
    }

    if args.strict_data:
        groups["released processed inputs"] = [
            Artifact("data/processed/controlled_oncu_200_safe16k.jsonl"),
            Artifact("data/processed/hotpotqa_cue_200.jsonl"),
            Artifact("data/processed/hotpotqa_cue_500.jsonl"),
            Artifact("data/processed/twowiki_cue_500.jsonl"),
            Artifact("data/processed/babilong_cue_200_external.jsonl"),
        ]

    if args.strict_longbench:
        groups["optional LongBench generated inputs"] = [
            Artifact("data/processed/longbench_cue_300_external.jsonl"),
        ]
        groups["optional LongBench completed outputs"] = [
            Artifact("outputs/longbench_qwen25_14b_300_external/results/per_sample_metrics.csv"),
            Artifact("outputs/longbench_qwen3_14b_300_external/results/per_sample_metrics.csv"),
            Artifact("outputs/longbench_gemma3_12b_300_external/results/per_sample_metrics.csv"),
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
        "strict_longbench": bool(args.strict_longbench),
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
            print("\nNote: released data/processed/*.jsonl inputs were not required. Use --strict-data to require them.")
            print("Generated auxiliary inputs, such as controlled_scaling_3200.jsonl and ruler_lite_240.jsonl, are rebuilt by released builder scripts before rerunning those audits.")
        if not args.strict_clean:
            print("Note: root-level duplicate/revision documents are warnings only. Use --strict-clean to fail on them.")

    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
