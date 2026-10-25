"""Monte Carlo evaluation of the six Causal Methods."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from estimators.registry import WORLDS, run_method, virtual_options
from simulation_engine.method_monte_carlo import run_method_monte_carlo
from utils.i18n import LocalizedError


def _raises_key(key, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except LocalizedError as exc:
        assert exc.msg.key == key, exc.msg.key
    else:
        raise AssertionError(f"expected {key}")


def test_summary_equals_a_loop_written_out():
    config = WORLDS["iv"].config_cls(seed=10)
    mc = run_method_monte_carlo("iv", config, n_reps=4, base_seed=10)
    errors, covered = [], []
    for r in range(4):
        df, truth = WORLDS["iv"].generate(replace(config, seed=10 + r))
        res = run_method("iv", df, dict(truth["roles"]), virtual_options("iv", truth))
        errors.append(res.estimate - truth["true_effect"])
        covered.append(res.ci_low <= truth["true_effect"] <= res.ci_high)
    assert np.allclose(mc.errors, errors, rtol=0, atol=1e-12)
    assert abs(mc.bias - np.mean(errors)) < 1e-12 and abs(mc.rmse - np.sqrt(np.mean(np.square(errors)))) < 1e-12
    assert mc.coverage == np.mean(covered) and mc.n_failed == 0


def test_rct_is_unbiased_and_calibrated():
    mc = run_method_monte_carlo("rct", WORLDS["rct"].config_cls(), n_reps=150)
    assert abs(mc.bias) < 3 * mc.rmse / np.sqrt(150), mc.bias
    assert 0.90 <= mc.coverage <= 0.99, mc.coverage
    assert 0.8 <= mc.se_ratio <= 1.25, mc.se_ratio
    assert mc.rejection_rate > 0.95                   # true effect 1.0 with n = 500


def test_weak_instrument_shows_up_as_bias_and_poor_coverage():
    strong = run_method_monte_carlo("iv", WORLDS["iv"].config_cls(instrument_strength=1.0), n_reps=60)
    weak = run_method_monte_carlo("iv", WORLDS["iv"].config_cls(instrument_strength=0.05), n_reps=60)
    assert abs(weak.bias) > abs(strong.bias) and weak.rmse > 3 * strong.rmse


def test_synthetic_control_has_no_coverage_but_a_rejection_rate():
    mc = run_method_monte_carlo("synthetic_control", WORLDS["synthetic_control"].config_cls(), n_reps=5)
    assert mc.coverage is None and mc.avg_ci_length is None and mc.se_ratio is None
    assert 0.0 <= mc.rejection_rate <= 1.0


def test_refusals_are_counted_and_too_many_stop_the_run():
    config = WORLDS["synthetic_control"].config_cls(n_donors=1)       # the estimator needs 2 donors
    _raises_key("err.mc_failed", run_method_monte_carlo, "synthetic_control", config, n_reps=3)
    _raises_key("err.mc_reps", run_method_monte_carlo, "rct", WORLDS["rct"].config_cls(), n_reps=1)


def test_progress_is_reported_for_every_replication():
    seen = []
    run_method_monte_carlo("rdd", WORLDS["rdd"].config_cls(), n_reps=3, progress=lambda d, n: seen.append((d, n)))
    assert seen == [(1, 3), (2, 3), (3, 3)]


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_method_monte_carlo: OK")
