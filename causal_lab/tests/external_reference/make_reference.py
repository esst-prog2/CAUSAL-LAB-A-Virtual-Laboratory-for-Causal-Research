"""Regenerate the datasets and reference values of test_external_reference.py.

Not needed to run the tests: its output (the CSV files and expected.json in
this folder) is committed. Re-run it only to change a dataset or a
reference package version. It needs the packages in
requirements-reference.txt, and R with estimatr, Matching and did plus
rdrobust 0.80 in a separate library (see reference.R):

    python tests/external_reference/make_reference.py <Rscript> <library with rdrobust 0.80>

References, one per estimator:
    RCT                 R estimatr: lm_robust (difference in means) and lm_lin, HC2
    IV                  R estimatr: iv_robust, HC0, with its first-stage F
    Regression disc.    rdrobust (Python port by its authors), fixed h, triangular kernel, HC1;
                        IK bandwidth from R rdrobust 0.80, bwselect = "IK"
    Matching            R Matching (Sekhon): Match, ATT, M = 1, Mahalanobis, bias adjustment
    Synthetic control   pysyncon: Synth with custom V (outcome in each pre-period)
    DML                 DoubleML (Python, by its authors): DoubleMLPLR, same folds and learners
    Callaway-Sant'Anna  R did (by its authors): att_gt with base_period = "universal", aggte
    Matrix games        Gambit: enummixed, logit_solve_lambda, logit_estimate (QRE by maximum likelihood)
    GMM                 linearmodels: IVGMM, robust weight, two steps (first-order conditions linear
                        in the parameters, so the same moments as Causal Lab's structural GMM)
"""
import csv
import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RSCRIPT = sys.argv[1] if len(sys.argv) > 1 else "Rscript"
OLD_RDROBUST_LIB = sys.argv[2] if len(sys.argv) > 2 else ""
RDD_BANDWIDTH = 0.4
SC_TREATMENT_PERIOD = 14
DML_SEED, DML_FOLDS = 0, 5


def load(name: str) -> pd.DataFrame:
    """Read a dataset of this folder bit for bit. pandas' default CSV parser
    is not exact in every version (3.0.6 changed the last bit of 697 of the
    1,500 values of dml.csv), and random forests are sensitive to that."""
    def parse(value: str):
        for kind in (int, float):
            try:
                return kind(value)
            except ValueError:
                pass
        return value
    with open(HERE / f"{name}.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return pd.DataFrame({col: [parse(r[col]) for r in rows] for col in rows[0]})


def make_datasets() -> None:
    rng = np.random.default_rng(20261025)

    n = 300                       # RCT: heterogeneous effect, heteroskedastic noise
    x = rng.normal(size=n)
    d = rng.integers(0, 2, n)
    y = 1 + 2 * d + 1.5 * x + d * x + rng.normal(size=n) * (1 + d)
    pd.DataFrame(dict(Y=y, D=d, X=x)).to_csv(HERE / "rct.csv", index=False)

    n = 500                       # IV: D endogenous through u, one control W
    z, w, u = rng.normal(size=n), rng.normal(size=n), rng.normal(size=n)
    d = 0.8 * z + 0.5 * u + 0.3 * w + rng.normal(size=n)
    y = 1 + 2 * d + 0.7 * w + u * (1 + 0.5 * np.abs(z))
    pd.DataFrame(dict(Y=y, D=d, Z=z, W=w)).to_csv(HERE / "iv.csv", index=False)

    n = 2000                      # RDD: curved, jump of 1 at 0
    x = rng.uniform(-1, 1, n)
    y = 0.5 + 0.8 * x - 0.4 * x ** 2 + 1.0 * (x >= 0) + rng.normal(scale=0.5, size=n)
    pd.DataFrame(dict(Y=y, X=x)).to_csv(HERE / "rdd.csv", index=False)

    n = 400                       # Matching: selection on X1, X2
    x1, x2 = rng.normal(size=n), rng.normal(size=n)
    d = (rng.uniform(size=n) < 1 / (1 + np.exp(-(0.8 * x1 - 0.5 * x2)))).astype(int)
    noise = rng.normal(size=n)
    y = 1 + 2 * d + 1.5 * x1 - x2 + 0.5 * d * x1 + noise
    pd.DataFrame(dict(Y=y, D=d, X1=x1, X2=x2)).to_csv(HERE / "matching.csv", index=False)
    # Same design with controls exactly linear in X: every linear regression of Y
    # on X among controls, whatever its sample or weights, then recovers the same
    # coefficients, so the bias correction no longer depends on that choice.
    y_lin = 1 + 1.5 * x1 - x2 + d * (2 + 0.5 * x1 + noise)
    pd.DataFrame(dict(Y=y_lin, D=d, X1=x1, X2=x2)).to_csv(HERE / "matching_linear.csv", index=False)

    units, periods = 8, 20        # Synthetic control: two-factor model, unit u0 treated
    factors = rng.normal(size=(periods, 2)).cumsum(axis=0)
    loadings = rng.uniform(0, 1, size=(units, 2))
    panel = factors @ loadings.T + rng.normal(scale=0.2, size=(periods, units))
    panel[SC_TREATMENT_PERIOD:, 0] += 3
    pd.DataFrame([(f"u{u}", p, panel[p, u]) for u in range(units) for p in range(periods)],
                 columns=["unit", "period", "Y"]).to_csv(HERE / "sc.csv", index=False)

    n = 500                       # DML: non-linear confounding
    x = rng.normal(size=(n, 3))
    d = np.sin(x[:, 0]) + x[:, 1] ** 2 + rng.normal(size=n)
    y = 1.5 * d + np.cos(x[:, 0]) + x[:, 2] + rng.normal(size=n)
    pd.DataFrame(dict(Y=y, D=d, X1=x[:, 0], X2=x[:, 1], X3=x[:, 2])).to_csv(HERE / "dml.csv", index=False)

    # Callaway & Sant'Anna (drawn last, so the datasets above keep their values):
    # 60 units, periods 1..10, cohorts 4, 6, 8 and never treated (first = 0) of
    # unequal sizes (24, 15, 7, 14 units), so that weighting by cohort size matters;
    # effects growing with time since adoption.
    rows = []
    for unit in range(60):
        first = (4, 4, 4, 6, 6, 8, 0, 0)[unit % 8]
        unit_effect = rng.normal()
        for period in range(1, 11):
            treated = int(first > 0 and period >= first)
            effect = (1 + 0.3 * (period - first)) * treated
            rows.append((unit, period, first, treated, unit_effect + 0.2 * period + effect + rng.normal()))
    pd.DataFrame(rows, columns=["unit", "period", "first", "D", "Y"]).to_csv(HERE / "cs.csv", index=False)

    # Fuzzy RD (drawn after the above): 60% follow the cutoff rule, the rest take
    # the treatment at random; effect 2 of the treatment received.
    n = 3000
    x = rng.uniform(-1, 1, n)
    complier = rng.uniform(size=n) < 0.6
    d = np.where(complier, (x >= 0).astype(int), rng.integers(0, 2, n))
    y = 0.5 + 0.8 * x - 0.6 * x ** 2 + 2.0 * d + rng.normal(scale=0.5, size=n)
    pd.DataFrame(dict(Y=y, X=x, D=d)).to_csv(HERE / "rdd_fuzzy.csv", index=False)

    # Synthetic control with three covariates: Causal Lab's own world, seed 5.
    sys.path.insert(0, str(HERE.parent.parent))
    from simulation_engine.method_worlds import SyntheticControlWorldConfig, synthetic_control_world
    sc_cov, _ = synthetic_control_world(SyntheticControlWorldConfig(seed=5, n_covariates=3))
    sc_cov.to_csv(HERE / "sc_cov.csv", index=False)

    # Cournot duopoly markets (drawn last): demand 100 + 10 w - Q, firm costs
    # 10 + 5 r_i + u_i with u_i unobserved and heteroskedastic, equilibrium
    # quantities from the closed form q_i = (a - 2 c_i + c_j) / 3.
    n = 400
    w = rng.normal(size=n)
    r1, r2 = rng.normal(size=(2, n))
    u1, u2 = rng.normal(scale=3, size=(2, n)) * (1 + 0.5 * np.abs(w))
    a, c1, c2 = 100 + 10 * w, 10 + 5 * r1 + u1, 10 + 5 * r2 + u2
    pd.DataFrame(dict(w=w, r1=r1, r2=r2, q1=(a - 2 * c1 + c2) / 3, q2=(a - 2 * c2 + c1) / 3)).to_csv(
        HERE / "cournot_markets.csv", index=False)


def r_references() -> tuple[dict, dict]:
    run = subprocess.run([RSCRIPT, str(HERE / "reference.R"), str(HERE), OLD_RDROBUST_LIB],
                         capture_output=True, text=True, check=True)
    values, versions = {}, {}
    for line in run.stdout.splitlines():
        key, value = line.split("=", 1)
        if key.startswith("version."):
            versions[key.removeprefix("version.")] = value
        else:
            values[key] = float(value)
    return values, versions


def rdd_reference() -> dict:
    from rdrobust import rdrobust
    df = load("rdd")
    fit = rdrobust(df["Y"].to_numpy(), df["X"].to_numpy(), c=0, h=RDD_BANDWIDTH, kernel="triangular",
                   p=1, vce="hc1")
    out = {"rdd.estimate": float(fit.coef.iloc[0, 0]), "rdd.se": float(fit.se.iloc[0, 0]),
           "rdd.n_left": int(fit.N_h[0]), "rdd.n_right": int(fit.N_h[1]),
           # rows: Conventional, Bias-Corrected, Robust (b = h when only h is given)
           "rdd.robust.estimate_bc": float(fit.coef.iloc[1, 0]), "rdd.robust.se": float(fit.se.iloc[2, 0])}
    fz = load("rdd_fuzzy")
    fit = rdrobust(fz["Y"].to_numpy(float), fz["X"].to_numpy(float), c=0, h=RDD_BANDWIDTH, kernel="triangular",
                   p=1, vce="hc1", fuzzy=fz["D"].to_numpy(float))
    out.update({"rdd_fuzzy.estimate": float(fit.coef.iloc[0, 0]), "rdd_fuzzy.se": float(fit.se.iloc[0, 0]),
                "rdd_fuzzy.robust.estimate_bc": float(fit.coef.iloc[1, 0]),
                "rdd_fuzzy.robust.se": float(fit.se.iloc[2, 0])})
    return out


def sc_reference() -> dict:
    from pysyncon import Dataprep, Synth
    df = load("sc")
    donors = sorted(u for u in df["unit"].unique() if u != "u0")
    pre = list(range(SC_TREATMENT_PERIOD))
    prep = Dataprep(foo=df, predictors=[], predictors_op="mean", dependent="Y", unit_variable="unit",
                    time_variable="period", treatment_identifier="u0", controls_identifier=donors,
                    time_predictors_prior=pre, special_predictors=[("Y", [p], "mean") for p in pre],
                    time_optimize_ssr=pre)
    # pysyncon divides each predictor by its standard deviation across units
    # before applying V; V = sd^2 cancels that, leaving the plain sum of squared
    # pre-period gaps that Causal Lab minimizes.
    x0, x1 = prep.make_covariate_mats()
    v = pd.concat([x0, x1], axis=1).std(axis=1).to_numpy() ** 2
    synth = Synth()
    synth.fit(dataprep=prep, custom_V=v)
    weights = synth.weights(round=12)
    post = list(range(SC_TREATMENT_PERIOD, int(df["period"].max()) + 1))
    out = {"sc.estimate": float(synth.att(time_period=post)["att"]),
           **{f"sc.weight.{u}": float(weights[u]) for u in donors}}

    # With covariates, V is searched (Nelder-Mead from equal V, as Causal Lab's first
    # start). The problem is not convex, so only the pre-treatment fit is compared.
    cov = load("sc_cov")
    covs = ["X1", "X2", "X3"]
    donors = sorted(u for u in cov["unit"].unique() if u != "treated")
    pre = sorted(p for p in cov["period"].unique() if p < 20)
    prep = Dataprep(foo=cov, predictors=covs, predictors_op="mean", dependent="Y", unit_variable="unit",
                    time_variable="period", treatment_identifier="treated", controls_identifier=donors,
                    time_predictors_prior=pre, special_predictors=[("Y", pre, "mean")], time_optimize_ssr=pre)
    synth = Synth()
    synth.fit(dataprep=prep, optim_method="Nelder-Mead", optim_initial="equal")
    w = pd.Series(synth.weights(round=12)).reindex(donors).to_numpy()
    wide = cov.pivot(index="period", columns="unit", values="Y")
    gaps = wide["treated"].to_numpy()[:len(pre)] - wide[donors].to_numpy()[:len(pre)] @ w
    out.update({"sc_cov.pre_mspe": float(np.mean(gaps ** 2)),
                "sc_cov.estimate": float(synth.att(time_period=sorted(set(cov["period"]) - set(pre)))["att"])})
    return out


def dml_reference() -> dict:
    from doubleml import DoubleMLData, DoubleMLPLR
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import KFold
    df = load("dml")
    covariates = ["X1", "X2", "X3"]
    # Causal Lab's folds and learners (estimators/dml.py), passed explicitly.
    folds = list(KFold(n_splits=DML_FOLDS, shuffle=True, random_state=DML_SEED).split(df[covariates]))
    forest = RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=DML_SEED, n_jobs=1)
    plr = DoubleMLPLR(DoubleMLData(df, y_col="Y", d_cols="D", x_cols=covariates), ml_l=forest, ml_m=forest,
                      n_folds=DML_FOLDS, score="partialling out", draw_sample_splitting=False)
    plr.set_sample_splitting(folds)
    plr.fit()
    return {"dml.estimate": float(plr.coef[0]), "dml.se": float(plr.se[0])}


def gambit_reference() -> dict:
    """Matrix games drawn here, with Gambit's extreme Nash equilibria (enummixed) and
    logit QREs (logit_solve_lambda). Generic games and games with tied payoffs."""
    import pygambit as gbt

    rng = np.random.default_rng(20261026)
    games = []
    for index in range(60):
        m, n = (int(v) for v in rng.integers(2, 5, size=2))
        if index % 2 == 0:
            a, b = rng.normal(size=(m, n)).round(6), rng.normal(size=(m, n)).round(6)
        else:
            a, b = rng.integers(0, 3, size=(m, n)).astype(float), rng.integers(0, 3, size=(m, n)).astype(float)
        g = gbt.Game.from_arrays(a, b)
        p1, p2 = list(g.players)

        def vec(profile, player):
            return [float(profile[player][s]) for s in player.strategies]
        equilibria = [vec(e, p1) + vec(e, p2) for e in gbt.nash.enummixed_solve(g, rational=False).equilibria]
        qre = {}
        if index % 2 == 0:                       # generic games only: no symmetry-induced bifurcation
            for lam in (1.0, 5.0):
                profile = gbt.qre.logit_solve_lambda(g, lam=[lam])[0].profile
                qre[str(lam)] = vec(profile, p1) + vec(profile, p2)
        games.append({"a": a.tolist(), "b": b.tolist(), "equilibria": equilibria, "qre": qre})
    return {"matrix_games": games}


def qre_estimate_reference() -> dict:
    """Gambit's maximum likelihood logit QRE on 40 generic games, with choice
    counts drawn from a QRE at lambda 0.5, 2 or 5 (300 choices per player)."""
    import pygambit as gbt

    rng = np.random.default_rng(11)
    out = []
    for _ in range(40):
        m, n = (int(v) for v in rng.integers(2, 5, size=2))
        a, b = rng.normal(size=(m, n)).round(6), rng.normal(size=(m, n)).round(6)
        g = gbt.Game.from_arrays(a, b)
        p1, p2 = list(g.players)
        profile = gbt.qre.logit_solve_lambda(g, lam=[float(rng.choice([0.5, 2.0, 5.0]))])[0].profile
        x = np.array([float(profile[p1][s]) for s in p1.strategies])
        y = np.array([float(profile[p2][s]) for s in p2.strategies])
        rc, cc = rng.multinomial(300, x / x.sum()), rng.multinomial(300, y / y.sum())
        data = g.mixed_strategy_profile(rational=False)
        for player, counts in ((p1, rc), (p2, cc)):
            for k, s in enumerate(player.strategies):
                data[s] = float(counts[k])
        fit = gbt.qre.logit_estimate(data)
        out.append({"a": a.tolist(), "b": b.tolist(), "row_counts": rc.tolist(), "col_counts": cc.tolist(),
                    "lam": float(fit.lam), "log_like": float(fit.log_like)})
    return {"qre_estimates": out}


def gmm_reference() -> dict:
    """Firm 1's first-order condition 100 + 10 w - 10 - (2 q1 + q2) - 5 r1 = u1, i.e.
    5 r1 = A0 + A1 w - B (2 q1 + q2) - u1: linear IV with 2 q1 + q2 endogenous,
    instruments const, w, r1, r2 (one overidentifying restriction)."""
    from linearmodels.iv import IVGMM

    df = load("cournot_markets")
    df = df.assign(y=5 * df["r1"], const=1.0, x=2 * df["q1"] + df["q2"])
    res = IVGMM(df["y"], df[["const", "w"]], df[["x"]], df[["r1", "r2"]], weight_type="robust").fit(cov_type="robust")
    sign = np.array([1.0, 1.0, -1.0])                 # coefficient on 2 q1 + q2 is -B
    return {"gmm.estimates": (res.params.to_numpy() * sign).tolist(), "gmm.se": res.std_errors.to_numpy().tolist(),
            "gmm.j": float(res.j_stat.stat)}


def main() -> None:
    make_datasets()
    r_values, r_versions = r_references()
    expected = {**r_values, **rdd_reference(), **sc_reference(), **dml_reference(), **gambit_reference(),
                **qre_estimate_reference(), **gmm_reference()}
    expected["settings"] = {"rdd_bandwidth": RDD_BANDWIDTH, "sc_treatment_period": SC_TREATMENT_PERIOD,
                            "dml_seed": DML_SEED, "dml_folds": DML_FOLDS}
    expected["versions"] = {**{k if k == "R" else f"R {k}": v for k, v in r_versions.items()},
                            **{p: version(p) for p in ("rdrobust", "pysyncon", "DoubleML", "pygambit", "linearmodels",
                                                       "scikit-learn",
                                                       "numpy", "pandas")}}
    (HERE / "expected.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(expected, indent=2))


if __name__ == "__main__":
    main()
