"""Sensitivity to violations of parallel trends (estimators/honest_did.py,
Rambachan & Roth 2023, Delta^SD(M)): the worst-case bias is exact, M = 0 is
the linear-extrapolation estimator, the interval keeps its coverage at the
worst case, and on worlds with a linear pre-trend it recovers the effect the
plain DiD misses. spike/honest_did_validation.py runs the larger version."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest
from scipy import optimize

from estimators.did import estimate_did
from estimators.event_study import estimate_event_study
from estimators.honest_did import (_max_bias, _Problem, _second_difference_basis, breakdown_m, critical_value,
                                   flci, problem_from_panel, sensitivity)
from simulation_engine.demo_study import SEED_BASE, design
from simulation_engine.dgp import generate
from utils.i18n import LocalizedError


def _world(level: str, r: int = 0):
    cfg = replace(design("differential_trend", level), seed=SEED_BASE + r)
    df, truth = generate(cfg)
    return df, truth, problem_from_panel(df, cfg.treatment_period)


def test_the_coefficients_are_those_of_the_event_study():
    df, _, problem = _world("low")
    es = estimate_event_study(df, fixed_treatment_period=10, window=10_000)
    coef = es.coefficients.set_index("rel_period")["estimate"]
    order = list(problem.pre) + list(problem.post)
    assert np.max(np.abs(coef.loc[order].to_numpy() - problem.beta)) < 1e-10


def test_critical_value_is_the_folded_normal_quantile():
    assert abs(critical_value(0.0) - 1.959964) < 1e-5
    t = 1.3
    c = critical_value(t)
    from scipy import stats
    assert abs(stats.norm.cdf(c - t) - stats.norm.cdf(-c - t) - 0.95) < 1e-10


def test_worst_case_bias_equals_the_linear_program():
    rng = np.random.default_rng(0)
    for _ in range(10):
        n_pre, n_post = rng.integers(2, 6), rng.integers(1, 5)
        pre, post = np.arange(-n_pre - 1, -1, dtype=float), np.arange(n_post, dtype=float)
        l = rng.random(n_post)
        l /= l.sum()
        g = pre + 1
        w = rng.normal(size=n_pre)
        w += g * (-(l @ (post + 1)) - w @ g) / (g @ g)          # remove linear trends
        problem = _Problem(pre, post, np.zeros(n_pre + n_post), np.eye(n_pre + n_post), l)
        periods = np.concatenate([pre, [-1.0], post])
        n = len(periods)
        a = np.zeros((n - 2, n))
        for i in range(1, n - 1):
            a[i - 1, i - 1:i + 2] = (1, -2, 1)
        bounds = [(-1e6, 1e6)] * n
        bounds[n_pre] = (0, 0)
        lp = optimize.linprog(-np.concatenate([w, [0], l]), A_ub=np.vstack([a, -a]), b_ub=np.full(2 * (n - 2), 0.3),
                              bounds=bounds, method="highs")
        assert abs(_max_bias(problem, w, 0.3) - (-lp.fun)) < 1e-8
        assert _max_bias(problem, w + 0.1, 0.3) == np.inf or abs((w + 0.1) @ g + l @ (post + 1)) < 1e-12


def test_m_zero_is_the_minimum_variance_linear_extrapolation():
    _, _, problem = _world("low")
    r = flci(problem, 0.0)
    # Closed form: minimise v' W v over w with g'w = -l'(post + 1), W the working covariance;
    # the standard error is then that of the chosen estimator under the estimated covariance.
    n_pre = len(problem.pre)
    s_pp, s_pq = problem.sigma_work[:n_pre, :n_pre], problem.sigma_work[:n_pre, n_pre:]
    g = problem.pre + 1
    target = -float(problem.l @ (problem.post + 1))
    inv = np.linalg.inv(s_pp)
    lam = (target + g @ inv @ s_pq @ problem.l) / (g @ inv @ g)
    w = inv @ (lam * g - s_pq @ problem.l)
    v = np.concatenate([w, problem.l])
    assert abs(r.estimate - v @ problem.beta) < 1e-6
    assert abs(r.se - np.sqrt(v @ problem.sigma @ v)) < 1e-6
    assert r.max_bias == 0 and abs((r.ci_high - r.ci_low) / 2 - 1.959964 * r.se) < 1e-5


def test_coverage_at_the_worst_case_is_95_percent():
    _, truth, problem = _world("none")
    rng = np.random.default_rng(1)
    n_pre = len(problem.pre)
    b = _second_difference_basis(n_pre, len(problem.post))
    for m in (0.02, 0.05):
        r = flci(problem, m)
        w = np.array([r.weights_pre[int(k)] for k in problem.pre])
        c = np.concatenate([w, [0.0], problem.l])
        delta = np.delete(b @ (m * np.sign(b.T @ c)), n_pre)
        tau = np.full(len(problem.post), truth["true_att"])
        beta = delta + np.concatenate([np.zeros(n_pre), tau])
        draws = rng.multivariate_normal(beta, problem.sigma, 20_000) @ np.concatenate([w, problem.l])
        covered = np.mean(np.abs(draws - problem.l @ tau) <= (r.ci_high - r.ci_low) / 2)
        assert abs(covered - 0.95) < 0.006, (m, covered)                    # 4 Monte Carlo SEs


def test_linear_pre_trends_are_handled_where_the_did_fails():
    did_cover = honest_cover = 0
    n = 200
    for r in range(n):
        df, truth, problem = _world("medium", r)
        att = truth["true_att"]
        did = estimate_did(df)
        did_cover += did.ci_low <= att <= did.ci_high
        h = flci(problem, 0.0)
        honest_cover += h.ci_low <= att <= h.ci_high
    assert did_cover == 0                      # the study: 0% coverage at medium
    assert honest_cover >= 0.91 * n            # 95% nominal; 0.91 is 2.6 Monte Carlo SEs below


def test_grid_breakdown_and_refusals():
    df, _, _ = _world("none")
    table = sensitivity(df, 10)
    assert list(table.columns) == ["M", "estimate", "se", "max_bias", "ci_low", "ci_high"]
    assert table["M"].iloc[0] == 0 and (np.diff(table["ci_high"] - table["ci_low"]) > 0).all()
    m = breakdown_m(table)
    assert m is None or m >= 0
    with pytest.raises(LocalizedError):
        problem_from_panel(df.iloc[1:], 10)                     # unbalanced
    with pytest.raises(LocalizedError):
        problem_from_panel(df[df["period"] >= 8], 10)            # one pre-period besides the reference
