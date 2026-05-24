# Long-Context ONCU Diagnostic Framework

`long-context-cue` is a reproducible Python framework for controlled diagnostic experiments on evidence utilization in long-context language models. It asks a narrower question than maximum context length: when task-relevant evidence is present inside a long input, how much of the oracle-evidence performance does the model retain? The primary metric is Oracle-Normalized Context Utilization (ONCU).

The package separates **core diagnostic conditions** from **auxiliary probes**. The core ONCU conditions are:

1. `no_evidence`: question-only lower reference.
2. `direct`: full long-context condition.
3. `retrieve_then_read`: deterministic evidence-narrowed condition.
4. `oracle`: gold-evidence upper reference.

The additional methods `cot`, `evidence_first`, and `evidence_first_verify` are auxiliary probes for failure analysis. They are retained to expose evidence-selection and evidence-sufficiency behavior, not as optimized prompting methods.

This project is **not** a prompt-engineering benchmark. Instruction templates are fixed by `diagnostic_v1_fixed`, are shared across models and datasets, and are not tuned per model, per dataset, or per failed example. Changes to backend configuration such as `num_ctx`, temperature, and output budget are treated as experimental controls rather than prompt optimization.

## Installation

Python 3.10 or newer is required.

```bash
cd long_context_cue
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

The non-editable dependency list is also recorded in `requirements.txt`.

## Generate Demo Data

```bash
python scripts/generate_demo_data.py
```

By default this writes 100 deterministic samples to `data/processed/controlled_benchmark.jsonl`. The JSONL schema stores the question, gold answer, oracle passage IDs and text, long context, distractors, context length, evidence position, evidence density, distractor similarity, and reasoning type. Context text uses neutral markers such as `[passage_id: p0001]`; it does not label visible passages as gold evidence or distractors.

Controlled demo factors are:

| Factor | Values |
| --- | --- |
| `context_length` | `4000`, `8000`, `16000`, `32000` |
| `evidence_position` | `front`, `middle`, `end`, `scattered` |
| `evidence_density` | `high`, `medium`, `low` |
| `distractor_similarity` | `none`, `low`, `high`, `conflicting` |
| `reasoning_type` | `single_hop`, `multi_hop`, `comparison`, `arithmetic`, `contradiction` |

The generator uses simple templates and whitespace-token length proxies. It is intentionally easy to extend with richer domain templates or dataset transforms.

## Dataset Construction

Controlled-ONCU is the main controlled dataset for the paper workflow. HotpotQA-ONCU adds real multi-hop QA validation with aligned supporting facts. RULER contributes established synthetic long-context validation from local generated task files. LongBench adds realistic long-context task validation. BABILong adds distributed-fact long-context reasoning validation.

Build the dataset components with:

```bash
python scripts/build_controlled_cue.py --output data/processed/controlled_cue.jsonl --num-per-cell 5 --seed 42

python scripts/build_hotpotqa_cue.py --output data/processed/hotpotqa_cue_500.jsonl --split validation --limit 500 --context-lengths 4000 8000 16000 --seed 42

python scripts/convert_ruler_to_cue.py --input data/raw/ruler/ --output data/processed/ruler_cue.jsonl

python scripts/build_longbench_cue.py --output data/processed/longbench_cue.jsonl --tasks narrativeqa qasper multifieldqa_en hotpotqa 2wikimqa musique --limit-per-task 100

python scripts/build_babilong_cue.py --output data/processed/babilong_cue.jsonl --configs 8k 16k 32k --tasks qa1 qa2 qa3 --limit-per-task 100
```

The LongBench builder first tries the Hugging Face dataset loader, then direct Hugging Face task data files when scripted loading is unavailable; if the per-task Parquet files are not reachable it also checks the official LongBench data archive. For a reproducible local fallback, place per-task files such as `narrativeqa.jsonl`, `qasper.jsonl`, or `hotpotqa.json` under a directory and pass it explicitly:

```bash
python scripts/build_longbench_cue.py --local-dir data/raw/LongBench --output data/processed/longbench_cue_small.jsonl --tasks narrativeqa qasper multifieldqa_en hotpotqa 2wikimqa musique --limit-per-task 20
```

Local LongBench files may live directly under `data/raw/LongBench/` or its `data/` subdirectory and may use `.jsonl` or `.json`.

Merge unified JSONL outputs with:

```bash
python scripts/merge_datasets.py --inputs data/processed/controlled_cue.jsonl data/processed/hotpotqa_cue_500.jsonl data/processed/ruler_cue.jsonl data/processed/longbench_cue.jsonl data/processed/babilong_cue.jsonl --output data/processed/all_oncu_benchmark.jsonl
```

Dataset statistics are available for any unified JSONL file:

```bash
python scripts/dataset_stats.py data/processed/controlled_cue.jsonl
```

CSV and Markdown statistics are written to `outputs/dataset_stats/`. The HotpotQA builder also writes a sibling `*.skipped.json` file with supporting-fact alignment skip counts.

Every component is converted to one internal schema with `source`, question and answer text, evidence and distractor lists when available, context controls or `unknown` markers, `answer_type`, and source metadata. Adapters that do not expose oracle evidence preserve an empty evidence list so the same runner can still score answer metrics and preserve provenance.

## Run Demo Experiment

```bash
python -m longcue.run_experiment --config configs/demo.yaml
```

The demo config uses `MockModelClient`, so it runs without external API calls. To generate data and run the demo in one step:

```bash
bash scripts/run_demo.sh
```

Experiments show a prediction progress bar by default, including the active method and sample ID while slower local or remote models are running. Set `progress.enabled` to `false` to disable it; if `tqdm` is unavailable, the runner falls back to ordinary logging.

```yaml
progress:
  enabled: true
```

For real model runs, keep answer-generation outputs small enough to stay inside the JSON contract:

```yaml
generation:
  max_tokens: 256
  temperature: 0.0
```

The evidence-first extractor may still use a larger internal budget so it can return the selected passage snippets before the answer step is constrained.

Raw response retention is configurable:

```yaml
logging:
  save_full_prompts: false
  save_intermediate: true
  compress_outputs: false
```

When `save_full_prompts` is false, raw JSONL records keep response text, parsed predictions, and compact intermediate metadata without full prompts or retrieved chunk text. When `compress_outputs` is true, raw and parsed prediction files are written as `.jsonl.gz`.

## Validate Fixed Diagnostic Protocol

Use the validator to check that YAML configs use the fixed diagnostic protocol, deterministic decoding, and explicit Ollama context-window settings:

```bash
python scripts/validate_diagnostic_protocol.py configs/controlled_qwen7b_100.yaml --require-core
```

Each run writes `protocol_manifest.json` under the output directory. The manifest records the fixed protocol version, method roles, generation settings, and retrieval settings so later model comparisons can be audited without treating prompts as tunable hyperparameters.

## Run Tests

```bash
pytest
```

Tests cover JSON extraction from noisy model text, answer normalization and metrics, evidence metrics, ONCU, diagnostic protocol metadata, failure diagnosis, and synthetic generation. They do not call paid or remote model APIs.

## Expected Outputs

For the demo config, outputs are written under `outputs/demo_run/`:

| Path | Content |
| --- | --- |
| `results/raw_model_responses.jsonl` | Raw responses, parsed predictions, and retained trace metadata |
| `results/parsed_predictions.jsonl` | Parsed answer JSON payloads |
| `results/per_sample_metrics.csv` | Answer, evidence, grounding, parse, and failure metrics per response |
| `results/aggregate_metrics.csv` | Aggregated means over controlled-variable groups |
| `results/oncu_metrics.csv` | Raw and clipped ONCU rows for long-context methods |
| `results/robustness_drop.csv` | Accuracy drop from no distractor to high/conflicting distractors |
| `tables/*.md` | Markdown tables for aggregate, ONCU, and robustness results |
| `logs/experiment.log` | Run log and JSON parse warnings |
| `resolved_config.json` | Config snapshot used by the run |

Answer metrics include strict columns (`exact_match_strict`, `answer_f1_strict`) and relaxed controlled-benchmark columns (`exact_match_relaxed`, `answer_f1_relaxed`). The legacy `exact_match` and `answer_f1` columns keep the strict behavior used by earlier runs.

Evidence-First raw intermediates retain selected passage IDs, the compressed evidence summary, the final answer, and verification results when verification runs. Inspect selected traces with:

```bash
python scripts/inspect_evidence_first.py --dataset data/processed/controlled_cue.jsonl --raw outputs/demo_run/results/raw_model_responses.jsonl --limit 5
```

## ONCU

Oracle-Normalized Context Utilization is computed as:

```text
ONCU = (Score_long - Score_no_evidence) / (Score_oracle - Score_no_evidence)
```

`Score_no_evidence` estimates question-only performance, `Score_oracle` estimates the attainable performance when minimal gold evidence is isolated, and `Score_long` measures performance when relevant evidence is embedded in a long context. The implementation writes raw ONCU and a clipped `[0, 1]` variant only when oracle evidence exists and oracle score is above no-evidence score. Invalid rows are retained with `cue_valid=false` and a `cue_invalid_reason`. ONCU rows are grouped by model, reasoning type, context length, evidence position, evidence density, distractor setting, and long-context method.

## Failure Diagnosis

Rule-based failure labels use gold evidence IDs, predicted evidence IDs, final answer correctness, and reasoning type:

| Label | Intended diagnosis |
| --- | --- |
| `evidence_localization_failure` | No evidence ID was selected |
| `evidence_selection_failure` | Wrong or distracting evidence IDs dominate |
| `evidence_integration_failure` | Multi-evidence tasks cite only partial gold evidence |
| `answer_conversion_failure` | Gold evidence is identified but final answer is wrong |
| `success` | Final answer is exact-match correct |

These labels are operational diagnostics, not a claim that evidence-ID rules fully explain model cognition.

## OpenAI-Compatible API

Use a config with:

```yaml
model:
  provider: openai_compatible
  model_name: your-model-name
```

Then set environment variables before running:

```bash
export OPENAI_COMPATIBLE_BASE_URL="https://your-provider.example/v1"
export OPENAI_COMPATIBLE_API_KEY="..."
python -m longcue.run_experiment --config configs/demo.yaml
```

API keys are never hardcoded. If the endpoint requires a nonstandard payload, subclass `BaseModelClient` in `longcue/models/`.

## Add A Model

1. Implement `BaseModelClient.generate()` in a new module under `longcue/models/`.
2. Add provider construction in `_make_client()` in `longcue/run_experiment.py`.
3. Keep the return value as raw text. Prompt methods and JSON parsing stay model-agnostic.
4. Add an offline test or use the existing mock client to test method logic separately from provider behavior.

An optional `OllamaClient` is already included for local endpoints exposing Ollama's chat API.

## Add A Dataset

Prepare JSONL records matching `BenchmarkSample` in `longcue/data/schema.py`. Passages with oracle annotations should have stable neutral passage IDs that can be cited and scored when the source exposes them. Long contexts should retain relevant passage text with neutral passage markers rather than revealing gold/distractor labels. Point `dataset_path` in a YAML config to the new JSONL file and keep controlled metadata populated for grouping.

## Assumptions And Limits

- The demo generator approximates tokens using whitespace units rather than provider tokenizers.
- Synthetic templates are deterministic and transparent; benchmark validity for an SCI paper should be established with stronger task construction, dataset documentation, and human or programmatic quality checks.
- Exact match and answer token F1 are intentionally simple baselines. Task-specific evaluators can be added next to `longcue/evaluation/`.
- Evidence diagnostics depend on model-reported neutral passage IDs stored in the `evidence_ids` output field. They should be interpreted together with raw traces and citation grounding scores.
