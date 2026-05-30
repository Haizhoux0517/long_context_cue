# Failure Taxonomy Human-Validation Codebook

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
