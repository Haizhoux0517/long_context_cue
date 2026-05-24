from __future__ import annotations

"""Oracle-Normalized Context Utilization (ONCU).

The implementation is intentionally compatible with earlier CUE filenames and
columns. ONCU uses the same normalization formula, but the paper reports it as
an oracle-normalized diagnostic metric rather than as a generic context-
utilization score.
"""

from .cue import CUE_GROUP_FIELDS as ONCU_GROUP_FIELDS
from .cue import compute_cue as compute_oncu
from .cue import compute_cue_rows as compute_oncu_rows

__all__ = ["ONCU_GROUP_FIELDS", "compute_oncu", "compute_oncu_rows"]
