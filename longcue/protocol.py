from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

PROMPT_PROTOCOL_VERSION = "diagnostic_v1_fixed"


@dataclass(frozen=True)
class MethodSpec:
    name: str
    display_name: str
    family: str
    role: str
    core_diagnostic: bool
    description: str


METHOD_SPECS: dict[str, MethodSpec] = {
    "no_evidence": MethodSpec(
        name="no_evidence",
        display_name="No Evidence",
        family="diagnostic_baseline",
        role="question_only_lower_bound",
        core_diagnostic=True,
        description="Question-only condition used to estimate answer priors and parametric knowledge.",
    ),
    "direct": MethodSpec(
        name="direct",
        display_name="Full Context",
        family="diagnostic_condition",
        role="full_context_condition",
        core_diagnostic=True,
        description="Full long-context condition used to measure evidence utilization when all context is supplied.",
    ),
    "retrieve_then_read": MethodSpec(
        name="retrieve_then_read",
        display_name="Retrieved Evidence",
        family="diagnostic_condition",
        role="evidence_narrowed_condition",
        core_diagnostic=True,
        description="Deterministic evidence-narrowing condition that tests whether performance recovers when the effective context is shortened.",
    ),
    "oracle": MethodSpec(
        name="oracle",
        display_name="Oracle Evidence",
        family="diagnostic_baseline",
        role="oracle_evidence_upper_reference",
        core_diagnostic=True,
        description="Gold-evidence condition used as an upper reference for ONCU normalization.",
    ),
    "cot": MethodSpec(
        name="cot",
        display_name="Concise Reasoning Probe",
        family="auxiliary_probe",
        role="reasoning_style_probe",
        core_diagnostic=False,
        description="Fixed auxiliary probe for testing whether a reasoning-style instruction changes utilization. It is not tuned per model.",
    ),
    "evidence_first": MethodSpec(
        name="evidence_first",
        display_name="Evidence-Selection Probe",
        family="auxiliary_probe",
        role="evidence_selection_probe",
        core_diagnostic=False,
        description="Fixed auxiliary probe exposing intermediate evidence selection before answer generation.",
    ),
    "evidence_first_verify": MethodSpec(
        name="evidence_first_verify",
        display_name="Evidence-Sufficiency Probe",
        family="auxiliary_probe",
        role="evidence_sufficiency_probe",
        core_diagnostic=False,
        description="Fixed auxiliary probe checking whether verification/expansion exposes incomplete evidence selection.",
    ),
}


CORE_DIAGNOSTIC_METHODS: tuple[str, ...] = (
    "no_evidence",
    "direct",
    "retrieve_then_read",
    "oracle",
)

AUXILIARY_PROBE_METHODS: tuple[str, ...] = (
    "cot",
    "evidence_first",
    "evidence_first_verify",
)


def method_spec(method_name: str) -> MethodSpec:
    return METHOD_SPECS.get(
        method_name,
        MethodSpec(
            name=method_name,
            display_name=method_name,
            family="unknown",
            role="unknown",
            core_diagnostic=False,
            description="Unregistered method.",
        ),
    )


def prompt_fingerprint(text: str) -> str:
    """Stable short hash for auditing that templates remain fixed.

    This is a reproducibility aid, not a prompt-selection mechanism.
    """
    return sha256(text.encode("utf-8")).hexdigest()[:12]


def ensure_no_model_specific_methods(methods: Iterable[str]) -> None:
    unknown = sorted(set(methods).difference(METHOD_SPECS))
    if unknown:
        raise ValueError(f"Unknown diagnostic method(s): {unknown}")
