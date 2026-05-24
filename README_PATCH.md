# Evidence-First patch

Copy these files over the same paths in your `long_context_cue` project.

Changed files:
- `longcue/utils/json_parser.py`
- `longcue/methods/evidence_first.py`
- `longcue/prompts/templates.py`
- `tests/test_evidence_first_canonical_text.py`

Main fix:
- Evidence-First now trusts only selected passage IDs from the model.
- Selected passage text is recovered from the original `long_context`, preventing hallucinated evidence text such as a model returning `p0001` with fabricated Toronto text.
- Evidence extraction/compression prompts now more strongly require jointly sufficient passages and warn against conflicting distractors.

Validation run by ChatGPT:
- `python -m pytest -q` -> 47 passed.
