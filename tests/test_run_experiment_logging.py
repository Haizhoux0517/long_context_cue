from pathlib import Path

import yaml

import longcue.run_experiment as run_experiment_module
from longcue.data.babilong_adapter import convert_babilong_record
from longcue.data.controlled_generator import ControlledCUEGenerator
from longcue.data.io import load_jsonl, save_samples
from longcue.data.longbench_adapter import convert_longbench_record
from longcue.run_experiment import run_experiment


def test_runner_omits_full_prompts_when_disabled(tmp_path: Path) -> None:
    dataset_path = save_samples(
        ControlledCUEGenerator(
            num_per_cell=1,
            context_lengths=(4000,),
            evidence_positions=("front",),
            distractor_similarities=("none",),
            reasoning_types=("single_hop",),
        ).generate(),
        tmp_path / "dataset.jsonl",
    )
    config = {
        "dataset_path": str(dataset_path),
        "output_dir": str(tmp_path / "run"),
        "model": {"provider": "mock", "model_name": "mock"},
        "generation": {"max_tokens": 64, "temperature": 0.0},
        "methods": ["no_evidence", "oracle", "direct"],
        "evaluation": {"compute_cue": True, "compute_failure_types": True},
        "logging": {
            "save_full_prompts": False,
            "save_intermediate": True,
            "compress_outputs": False,
        },
        "progress": {"enabled": False},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    artifacts = run_experiment(config_path)
    records = load_jsonl(artifacts["raw"])
    assert records
    assert all("prompt" not in record for record in records)
    assert all("raw_response" in record for record in records)


def test_mixed_mock_run_has_no_parse_errors(tmp_path: Path) -> None:
    controlled = ControlledCUEGenerator(
        num_per_cell=1,
        context_lengths=(4000,),
        evidence_positions=("front",),
        distractor_similarities=("none",),
        reasoning_types=("single_hop",),
    ).generate()[0]
    longbench = convert_longbench_record(
        {
            "input": "Who found the map?",
            "context": "Mira found the map in the archive.",
            "answers": ["Mira"],
        },
        task="narrativeqa",
        index=0,
    )
    babilong = convert_babilong_record(
        {
            "input": "Mary moved to the garden.",
            "question": "Where is Mary?",
            "target": "garden",
        },
        config="8k",
        task="qa1",
        index=0,
    )
    assert longbench is not None
    assert babilong is not None
    dataset_path = save_samples(
        [controlled, longbench, babilong], tmp_path / "mixed.jsonl"
    )
    config = {
        "dataset_path": str(dataset_path),
        "output_dir": str(tmp_path / "mixed_run"),
        "model": {"provider": "mock", "model_name": "mock"},
        "generation": {"max_tokens": 64, "temperature": 0.0},
        "methods": [
            "no_evidence",
            "oracle",
            "direct",
            "cot",
            "retrieve_then_read",
            "evidence_first",
            "evidence_first_verify",
        ],
        "evaluation": {"compute_cue": True, "compute_failure_types": True},
        "logging": {"save_full_prompts": False, "save_intermediate": True},
        "progress": {"enabled": False},
    }
    config_path = tmp_path / "mixed.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    artifacts = run_experiment(config_path)
    metric_rows = load_jsonl(artifacts["predictions"])
    assert len(metric_rows) == 21
    assert all(not row.get("parse_error") for row in metric_rows)
    raw_rows = load_jsonl(artifacts["raw"])
    evidence_first_row = next(row for row in raw_rows if row["method"] == "evidence_first")
    assert set(evidence_first_row["intermediate"]) >= {
        "selected_evidence_ids",
        "evidence_summary",
        "final_answer",
    }
    verification_row = next(
        row for row in raw_rows if row["method"] == "evidence_first_verify"
    )
    assert "verification_result" in verification_row["intermediate"]


def test_runner_progress_tracks_prediction_count(tmp_path: Path, monkeypatch) -> None:
    dataset_path = save_samples(
        ControlledCUEGenerator(
            num_per_cell=1,
            context_lengths=(4000,),
            evidence_positions=("front",),
            distractor_similarities=("none",),
            reasoning_types=("single_hop",),
        ).generate(),
        tmp_path / "progress_dataset.jsonl",
    )
    config = {
        "dataset_path": str(dataset_path),
        "output_dir": str(tmp_path / "progress_run"),
        "model": {"provider": "mock", "model_name": "mock"},
        "generation": {"max_tokens": 64, "temperature": 0.0},
        "methods": ["no_evidence", "oracle", "direct"],
        "evaluation": {"compute_cue": True, "compute_failure_types": True},
        "progress": {"enabled": True},
    }
    config_path = tmp_path / "progress.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    class FakeProgress:
        instances = []

        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            self.n = 0
            self.contexts = []
            self.closed = False
            self.instances.append(self)

        def set_postfix(self, context, refresh=True) -> None:
            del refresh
            self.contexts.append(context)

        def update(self, count: int) -> None:
            self.n += count

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(run_experiment_module, "_tqdm", FakeProgress)
    monkeypatch.setattr(run_experiment_module, "_logging_redirect_tqdm", None)
    run_experiment(config_path)

    progress = FakeProgress.instances[0]
    assert progress.kwargs["total"] == 3
    assert progress.n == 3
    assert progress.closed is True
    assert progress.contexts[-1]["method"] == "direct"
    assert progress.contexts[-1]["sample_id"].startswith("controlled_")


def test_runner_continues_when_tqdm_is_missing(tmp_path: Path, monkeypatch) -> None:
    dataset_path = save_samples(
        ControlledCUEGenerator(
            num_per_cell=1,
            context_lengths=(4000,),
            evidence_positions=("front",),
            distractor_similarities=("none",),
            reasoning_types=("single_hop",),
        ).generate(),
        tmp_path / "fallback_dataset.jsonl",
    )
    config = {
        "dataset_path": str(dataset_path),
        "output_dir": str(tmp_path / "fallback_run"),
        "model": {"provider": "mock", "model_name": "mock"},
        "generation": {"max_tokens": 64, "temperature": 0.0},
        "methods": ["direct"],
        "progress": {"enabled": True},
    }
    config_path = tmp_path / "fallback.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    monkeypatch.setattr(run_experiment_module, "_tqdm", None)
    artifacts = run_experiment(config_path)

    assert artifacts["per_sample"].exists()
