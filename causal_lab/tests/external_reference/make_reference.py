"""Regenerate the datasets and reference values of test_external_reference.py.

Not needed to run the tests: its output (the CSV files and expected.json in
this folder) is committed. Re-run it only to change a dataset or a
reference package version. It needs the packages in
requirements-reference.txt and R with estimatr and Matching:

    python tests/external_reference/make_reference.py [path/to/Rscript]

References, one per estimator:
    RCT                 R estimatr: lm_robust (difference in means) and lm_lin, HC2
    IV                  R estimatr: iv_robust, HC0
    Regression disc.    rdrobust (Python port by its authors), fixed h, triangular kernel, HC1
    Matching            R Matching (Sekhon): Match, ATT, M = 1, Mahalanobis, bias adjustment
    Synthetic control   pysyncon: Synth with custom V (outcome in each pre-period)
    DML                 DoubleML (Python, by its authors): DoubleMLPLR, same folds and learners
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


def r_references() -> tuple[dict, dict]:
    run = subprocess.run([RSCRIPT, str(HERE / "reference.R"), str(HERE)],
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
    return {"rdd.estimate": float(fit.coef.iloc[0, 0]), "rdd.se": float(fit.se.iloc[0, 0]),
            "rdd.n_left": int(fit.N_h[0]), "rdd.n_right": int(fit.N_h[1])}


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
    return {"sc.estimate": float(synth.att(time_period=post)["att"]),
            **{f"sc.weight.{u}": float(weights[u]) for u in donors}}


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


def main() -> None:
    make_datasets()
    r_values, r_versions = r_references()
    expected = {**r_values, **rdd_reference(), **sc_reference(), **dml_reference()}
    expected["settings"] = {"rdd_bandwidth": RDD_BANDWIDTH, "sc_treatment_period": SC_TREATMENT_PERIOD,
                            "dml_seed": DML_SEED, "dml_folds": DML_FOLDS}
    expected["versions"] = {**{k if k == "R" else f"R {k}": v for k, v in r_versions.items()},
                            **{p: version(p) for p in ("rdrobust", "pysyncon", "DoubleML", "scikit-learn",
                                                       "numpy", "pandas")}}
    (HERE / "expected.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(expected, indent=2))


if __name__ == "__main__":
    main()
