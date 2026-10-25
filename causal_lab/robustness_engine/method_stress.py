"""
"Break My Design" for the six Causal Methods.

Each method gets checks aimed at the threat its identification rests on,
each returning PASS, WARNING or N/A with a translatable message, and the same
Identification Strength score as the DiD stress test (100 * PASS / checks
that are not N/A). Tests use the 10% level, as the DiD checks do; the other
thresholds are rules of thumb, stated in each message. False-alarm and
detection rates on the method worlds are in spike/method_calibration_results.md.
The score is a diagnostic heuristic, not a proof.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from estimators.common import MethodResult
from estimators.rdd import estimate_rdd
from estimators.registry import run_method
from estimators.synthetic_control import estimate_synthetic_control
from robustness_engine.stress_test import NOT_APPLICABLE, PASS, WARNING, identification_strength
from utils.i18n import LocalizedError, Msg

LEVEL = 0.10
SMD_LIMIT = 0.1
MAX_OUTSIDE_SHARE = 0.05
SC_PLACEBO_LEVEL = 0.05
MIN_ARM = 30
WEAK_F = 10.0
EXTREME_PS = 0.95
MAX_EXTREME_SHARE = 0.05
DML_R2_LIMIT = 0.95
# Re-splitting the folds moves the estimate by a median 0.29 SE (90th percentile
# 0.56) on 40 default DML worlds of 600 observations: 0.75 SE fired on 5%.
DML_SEED_SHIFT = 0.75
CHECKS = {
    "rct": ("rct_balance", "rct_arm_size"),
    "matching": ("matching_overlap", "matching_balance", "matching_extreme_ps", "matching_ipw_agreement"),
    "iv": ("iv_weak_instrument", "iv_overidentification"),
    "rdd": ("rdd_manipulation", "rdd_bandwidth", "rdd_placebo_cutoffs"),
    "synthetic_control": ("sc_pre_fit", "sc_leave_one_out", "sc_in_time_placebo"),
    "dml": ("dml_overlap", "dml_seed_stability"),
}


@dataclass
class MethodCheck:
    slug: str
    verdict: str
    message: Msg
    statistic: float | None = None
    p_value: float | None = None


@dataclass
class MethodStressReport:
    method: str
    checks: list[MethodCheck] = field(default_factory=list)
    identification_strength: float | None = None
    n_computable: int = 0


def _check(slug, warn: bool, statistic=None, p_value=None, **params) -> MethodCheck:
    verdict = WARNING if warn else PASS
    return MethodCheck(slug, verdict, Msg(f"mstress.{slug}.{verdict.lower()}", **params), statistic, p_value)


def _na(slug, reason: str = "na", **params) -> MethodCheck:
    return MethodCheck(slug, NOT_APPLICABLE, Msg(f"mstress.{slug}.{reason}", **params))


def _wald_p(y: np.ndarray, x: np.ndarray) -> float:
    """p-value of the joint HC1 Wald test that every slope of y on x is zero."""
    fit = sm.OLS(y, sm.add_constant(x, has_constant="add")).fit(cov_type="HC1")
    k = x.shape[1]
    return float(np.asarray(fit.f_test(np.eye(k + 1)[1:]).pvalue))


# --------------------------------------------------------------------------
# RCT
# --------------------------------------------------------------------------
def _rct(df, m, result: MethodResult) -> list[MethodCheck]:
    d = result.details
    covariates = list(m.get("covariates") or [])
    data = df[[m["outcome"], m["treatment"]] + covariates].dropna()
    # A joint test, not a per-covariate |SMD| > 0.1 rule: in a truly randomized
    # sample of 500 that rule fired on 55% of worlds by chance alone.
    if covariates:
        p = _wald_p(data[m["treatment"]].to_numpy(float), data[covariates].to_numpy(float))
        balance = _check("rct_balance", p < LEVEL, p_value=p, p=p)
    else:
        balance = _na("rct_balance", "no_covariates")
    smallest = min(d["n_treated"], d["n_control"])
    arm = _check("rct_arm_size", smallest < MIN_ARM, statistic=smallest, n=smallest, minimum=MIN_ARM)
    return [balance, arm]


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------
def _matching(df, m, result: MethodResult) -> list[MethodCheck]:
    d = result.details
    ps = d["propensity"]
    treated, control = ps.loc[ps["treated"] == 1, "propensity"], ps.loc[ps["treated"] == 0, "propensity"]
    # A share, not "any treated unit outside": with logit tails one or two always
    # fall outside (94% of clean worlds).
    outside = int(((treated > control.max()) | (treated < control.min())).sum())
    share_out = outside / len(treated)
    overlap = _check("matching_overlap", share_out > MAX_OUTSIDE_SHARE, statistic=share_out, n=outside,
                     share=share_out, limit=MAX_OUTSIDE_SHARE)
    smd = float(d["balance"]["std_diff_after"].abs().max())
    balance = _check("matching_balance", smd > SMD_LIMIT, statistic=smd, smd=smd, limit=SMD_LIMIT)
    extreme = float(((ps["propensity"] > EXTREME_PS) | (ps["propensity"] < 1 - EXTREME_PS)).mean())
    extreme_ps = _check("matching_extreme_ps", extreme > MAX_EXTREME_SHARE, statistic=extreme, share=extreme,
                        cut=EXTREME_PS, limit=MAX_EXTREME_SHARE)
    if np.isfinite(d["ipw_se"]) and result.se:
        z = (result.estimate - d["ipw_att"]) / np.hypot(result.se, d["ipw_se"])
        p = float(2 * stats.norm.sf(abs(z)))
        agreement = _check("matching_ipw_agreement", p < LEVEL, statistic=z, p_value=p, matching=result.estimate,
                           ipw=d["ipw_att"], p=p)
    else:
        agreement = _na("matching_ipw_agreement")
    return [overlap, balance, extreme_ps, agreement]


# --------------------------------------------------------------------------
# IV
# --------------------------------------------------------------------------
def _iv(df, m, result: MethodResult) -> list[MethodCheck]:
    from linearmodels.iv import IV2SLS

    f = result.details["first_stage_f"]
    weak = _check("iv_weak_instrument", f < WEAK_F, statistic=f, f=f, threshold=WEAK_F)
    instruments, controls = list(m["instruments"]), list(m.get("controls") or [])
    if len(instruments) < 2:
        return [weak, _na("iv_overidentification", "just_identified")]
    data = df[[m["outcome"], m["treatment"]] + instruments + controls].dropna().astype(float)
    fit = IV2SLS(data[m["outcome"]], sm.add_constant(data[controls], has_constant="add"),
                 data[[m["treatment"]]], data[instruments]).fit(cov_type="robust")
    test = fit.wooldridge_overid           # heteroskedasticity-robust score test
    p = float(test.pval)
    return [weak, _check("iv_overidentification", p < LEVEL, statistic=float(test.stat), p_value=p, p=p,
                         df=int(test.df))]


# --------------------------------------------------------------------------
# RDD
# --------------------------------------------------------------------------
def _rdd(df, m, options, result: MethodResult) -> list[MethodCheck]:
    d = result.details
    man = d["manipulation"]
    manipulation = (_check("rdd_manipulation", man["p_value"] < LEVEL, p_value=man["p_value"],
                           below=man["count_below"], above=man["count_above"], p=man["p_value"])
                    if np.isfinite(man["p_value"]) else _na("rdd_manipulation"))
    # Hausman-type comparison of nested bandwidths: under no bias the smaller
    # bandwidth's estimate only adds noise, so Var(diff) ~ |se_small^2 - se_large^2|.
    # (A "shift > 1 SE" rule fired on 55% of clean worlds.)
    sens = d["sensitivity"].set_index("factor")
    p_values = []
    for small, large in ((0.5, 1.0), (1.0, 2.0)):
        est_s, est_l = sens.loc[small, "estimate"], sens.loc[large, "estimate"]
        var = abs(sens.loc[small, "se"] ** 2 - sens.loc[large, "se"] ** 2)
        if np.isfinite(est_s) and np.isfinite(est_l) and var > 0:
            p_values.append(float(2 * stats.norm.sf(abs(est_s - est_l) / np.sqrt(var))))
    if p_values:
        p = min(1.0, min(p_values) * len(p_values))         # Bonferroni over the two comparisons
        bandwidth = _check("rdd_bandwidth", p < LEVEL, p_value=p, p=p,
                           half=sens.loc[0.5, "estimate"], double=sens.loc[2.0, "estimate"])
    else:
        bandwidth = _na("rdd_bandwidth")
    # Placebo cutoffs at the median of the running variable on each side, using
    # only that side's data, so the true jump cannot enter the estimate.
    cutoff = d["cutoff"]
    data = df[[m["outcome"], m["running"]]].dropna()
    p_values = []
    for side in (data[data[m["running"]] < cutoff], data[data[m["running"]] >= cutoff]):
        try:
            placebo = estimate_rdd(side, m["outcome"], m["running"], float(side[m["running"]].median()))
            p_values.append(placebo.p_value)
        except (LocalizedError, ValueError, np.linalg.LinAlgError):
            continue
    if p_values:
        p = min(1.0, min(p_values) * len(p_values))         # Bonferroni over the two sides
        placebo_check = _check("rdd_placebo_cutoffs", p < LEVEL, p_value=p, p=p, k=len(p_values))
    else:
        placebo_check = _na("rdd_placebo_cutoffs")
    return [manipulation, bandwidth, placebo_check]


# --------------------------------------------------------------------------
# Synthetic control
# --------------------------------------------------------------------------
def _synthetic_control(df, m, options, result: MethodResult) -> list[MethodCheck]:
    d = result.details
    pre_values = d["paths"].loc[d["paths"]["period"] < d["treatment_period"], "treated"]
    sd = float(pre_values.std(ddof=0))
    fit = _check("sc_pre_fit", sd > 0 and d["pre_rmspe"] > 0.5 * sd, statistic=d["pre_rmspe"],
                 rmspe=d["pre_rmspe"], sd=sd)
    scale = max(d["pre_rmspe"], 1e-12)

    top = d["weights"].iloc[0]
    rest = df[df[m["unit"]] != top["donor"]]
    try:
        loo = estimate_synthetic_control(rest, m["unit"], m["period"], m["outcome"],
                                         options["treated_unit"], options["treatment_period"])
        change = abs(loo.estimate - result.estimate) / scale
        leave_one_out = _check("sc_leave_one_out", change > 2.0, statistic=change, donor=str(top["donor"]),
                               weight=float(top["weight"]), estimate=loo.estimate, change=change)
    except LocalizedError:
        leave_one_out = _na("sc_leave_one_out")

    # In-time placebo: pretend treatment started halfway through the
    # pre-period, judged by the method's own placebo-in-space p-value.
    # (A "gap > 2 pre-RMSPE" rule fired on 26% of clean worlds.) The cut is 5%,
    # not 10%: on 200 default worlds p < 0.10 fired on 17.5% and p < 0.05 on
    # 9.5% (rank 1 of 21 should be 4.8%), because the treated unit of that world
    # is not exchangeable with its donors.
    periods = sorted(df.loc[df[m["period"]] < options["treatment_period"], m["period"]].unique())
    if len(periods) >= 4:
        fake = periods[len(periods) // 2]
        pre_only = df[df[m["period"]] < options["treatment_period"]]
        placebo = estimate_synthetic_control(pre_only, m["unit"], m["period"], m["outcome"],
                                             options["treated_unit"], fake)
        in_time = _check("sc_in_time_placebo", placebo.p_value < SC_PLACEBO_LEVEL, p_value=placebo.p_value, period=fake,
                         effect=placebo.estimate, p=placebo.p_value)
    else:
        in_time = _na("sc_in_time_placebo")
    return [fit, leave_one_out, in_time]


# --------------------------------------------------------------------------
# DML
# --------------------------------------------------------------------------
def _dml(df, m, options, result: MethodResult) -> list[MethodCheck]:
    from estimators.dml import estimate_dml

    r2 = result.details["r2_treatment"]
    overlap = _check("dml_overlap", r2 > DML_R2_LIMIT, statistic=r2, r2=r2, limit=DML_R2_LIMIT)
    again = estimate_dml(df, m["outcome"], m["treatment"], m.get("covariates"), seed=1)
    shift = abs(again.estimate - result.estimate) / result.se
    stability = _check("dml_seed_stability", shift > DML_SEED_SHIFT, statistic=shift, first=result.estimate,
                       second=again.estimate, shift=shift)
    return [overlap, stability]


def run_method_stress_test(method: str, df: pd.DataFrame, mapping: dict, options: dict,
                           result: MethodResult | None = None) -> MethodStressReport:
    """The checks of `method`, reusing `result` when the estimate is already known."""
    result = result or run_method(method, df, mapping, options)
    if method == "rct":
        checks = _rct(df, mapping, result)
    elif method == "matching":
        checks = _matching(df, mapping, result)
    elif method == "iv":
        checks = _iv(df, mapping, result)
    elif method == "rdd":
        checks = _rdd(df, mapping, options, result)
    elif method == "synthetic_control":
        checks = _synthetic_control(df, mapping, options, result)
    elif method == "dml":
        checks = _dml(df, mapping, options, result)
    else:
        raise KeyError(method)
    return MethodStressReport(method=method, checks=checks, identification_strength=identification_strength(checks),
                              n_computable=sum(c.verdict != NOT_APPLICABLE for c in checks))
