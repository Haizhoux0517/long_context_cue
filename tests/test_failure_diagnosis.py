from longcue.evaluation.failure_diagnosis import diagnose_failure


def test_failure_diagnosis_categories() -> None:
    assert diagnose_failure(["e1"], [], False, "single_hop") == "evidence_localization_failure"
    assert diagnose_failure(["e1"], ["d1"], False, "single_hop") == "evidence_selection_failure"
    assert (
        diagnose_failure(["e1", "e2"], ["e1"], False, "multi_hop")
        == "evidence_integration_failure"
    )
    assert (
        diagnose_failure(["e1"], ["e1"], False, "single_hop")
        == "answer_conversion_failure"
    )
    assert diagnose_failure(["e1"], ["e1"], True, "single_hop") == "success"
