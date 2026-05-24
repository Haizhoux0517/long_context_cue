"""Fixed diagnostic condition and auxiliary probe runners.

These runners are not optimized per model. Core ONCU experiments use
no_evidence, direct/full-context, retrieve_then_read, and oracle conditions;
reasoning/evidence-first variants are auxiliary probes for failure diagnosis.
"""

from collections.abc import Callable
from typing import Any

from .cot import run as run_cot
from .direct import run as run_direct
from .evidence_first import run as run_evidence_first
from .evidence_first_verify import run as run_evidence_first_verify
from .no_evidence import run as run_no_evidence
from .oracle import run as run_oracle
from .retrieve_then_read import run as run_retrieve_then_read

MethodRunner = Callable[..., dict[str, Any]]

METHOD_REGISTRY: dict[str, MethodRunner] = {
    "no_evidence": run_no_evidence,
    "oracle": run_oracle,
    "direct": run_direct,
    "cot": run_cot,
    "retrieve_then_read": run_retrieve_then_read,
    "evidence_first": run_evidence_first,
    "evidence_first_verify": run_evidence_first_verify,
}

__all__ = ["METHOD_REGISTRY", "MethodRunner"]
