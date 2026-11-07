"""The qualitative summary of the Break My Design checks, which replaced the score."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robustness_engine.method_stress import CHECKS, IDENTIFYING_CHECKS
from robustness_engine.stress_test import (CHECK_SLUGS, IDENTIFYING_CHECKS as DID_IDENTIFYING, INSUFFICIENT, NO_WARNING,
                                           NOT_APPLICABLE, PASS, WARNING, WARNING_RAISED, summary_of_checks)


def test_the_summary_of_checks_never_calls_a_design_valid():
    assert summary_of_checks([PASS, WARNING, NOT_APPLICABLE]) == WARNING_RAISED
    assert summary_of_checks([PASS, NOT_APPLICABLE]) == NO_WARNING
    assert summary_of_checks([NOT_APPLICABLE, NOT_APPLICABLE]) == INSUFFICIENT
    assert summary_of_checks([]) == INSUFFICIENT


def test_only_checks_aimed_at_the_identifying_assumption_count():
    assert set(DID_IDENTIFYING) < set(CHECK_SLUGS)
    assert not {"Serial Correlation", "Heterogeneous Effects"} & set(DID_IDENTIFYING)
    for method, slugs in IDENTIFYING_CHECKS.items():
        assert set(slugs) <= set(CHECKS[method]), method


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_check_summary: OK")
