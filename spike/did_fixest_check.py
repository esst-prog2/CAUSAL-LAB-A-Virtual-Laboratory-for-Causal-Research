"""DiD and event study checked against R fixest, value by value.

Run from the repository root:  .venv/Scripts/python spike/did_fixest_check.py
Needs Rscript with the fixest package (set RSCRIPT, default R 4.6.1).

fixest is the reference implementation of fixed-effects regressions in R
(Bergé 2018). Its default clustered standard error is the convention the app
uses: CR1 with G/(G-1)(N-1)/(N-K), the unit dummies nested in the clusters not
counted in K, and a Student t with G - 1 degrees of freedom. The script writes
each dataset to a temporary CSV, fits it with fixest, and compares the
coefficient, standard error, 95% interval and p-value with the app's.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "causal_lab"))

from estimators.did import estimate_did  # noqa: E402
from estimators.event_study import estimate_event_study  # noqa: E402
from simulation_engine.dgp import VirtualWorldConfig, generate  # noqa: E402
from utils.real_data import load_card_krueger  # noqa: E402

RSCRIPT = os.environ.get("RSCRIPT", r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe")

R_CODE = r"""
suppressMessages(library(fixest))
args <- commandArgs(trailingOnly = TRUE)
out <- list()
for (f in args) {
  d <- read.csv(f)
  if ("rel_bucket" %in% names(d)) {
    m <- feols(Y ~ i(rel_bucket, ref = "ref") | unit + period, data = d, cluster = ~unit)
  } else {
    m <- feols(Y ~ D | unit + period, data = d, cluster = ~unit)
  }
  ct <- coeftable(m); ci <- confint(m)
  out[[basename(f)]] <- list(names = rownames(ct), est = unname(ct[, 1]), se = unname(ct[, 2]),
                             p = unname(ct[, 4]), lo = unname(ci[, 1]), hi = unname(ci[, 2]),
                             version = as.character(packageVersion("fixest")))
}
cat(jsonlite::toJSON(out, digits = NA, auto_unbox = TRUE))
"""


def event_study_frame(df: pd.DataFrame, window: int = 6, reference_period: int = -1) -> pd.DataFrame:
    """The design matrix the app builds (estimators/event_study.py), as a column fixest can read."""
    data = df.copy()
    adoption = data["unit"].map(data.loc[data["D"] == 1].groupby("unit")["period"].min())
    rel = np.where(data["treated_unit"] == 1, data["period"] - adoption, np.nan)
    rel = pd.Series(rel).clip(lower=-window, upper=window)
    bucket = rel.apply(lambda x: "ref" if pd.isna(x) else f"k{int(x):+d}")
    bucket[bucket == f"k{reference_period:+d}"] = "ref"
    data["rel_bucket"] = bucket.to_numpy()
    return data[["unit", "period", "Y", "rel_bucket"]]


def main() -> None:
    worlds = {
        "default": VirtualWorldConfig(seed=4),
        "staggered_heterogeneous": VirtualWorldConfig(seed=4, staggered_adoption=True, treatment_heterogeneity="medium"),
        "serial_correlation_60_units": VirtualWorldConfig(seed=4, serial_correlation="high", n_units=60),
        "few_clusters_12_units": VirtualWorldConfig(seed=7, n_units=12),
        "diverging_pretrends_low": VirtualWorldConfig(seed=42, differential_trend="low"),
    }
    cases: dict[str, tuple[str, pd.DataFrame]] = {}
    for name, cfg in worlds.items():
        df, _ = generate(cfg)
        cases[f"did_{name}"] = ("did", df)
    cases["did_card_krueger_1994"] = ("did", load_card_krueger())
    df_es, _ = generate(VirtualWorldConfig(seed=4))
    cases["event_study_default"] = ("es", df_es)

    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for key, (kind, df) in cases.items():
            path = Path(tmp) / f"{key}.csv"
            (event_study_frame(df) if kind == "es" else df[["unit", "period", "Y", "D"]]).to_csv(path, index=False)
            files.append(str(path))
        r_file = Path(tmp) / "fit.R"
        r_file.write_text(R_CODE, encoding="utf-8")
        proc = subprocess.run([RSCRIPT, str(r_file), *files], capture_output=True, text=True, check=True)
        ref = json.loads(proc.stdout)

    worst = dict(est=0.0, se=0.0, ci=0.0, p=0.0)
    print(f"fixest {next(iter(ref.values()))['version']}\n")
    print(f"{'dataset':38s} {'app estimate':>14s} {'fixest':>14s} {'app SE':>10s} {'fixest SE':>10s} {'max rel. diff':>14s}")
    for key, (kind, df) in cases.items():
        r = ref[f"{key}.csv"]
        if kind == "did":
            ours = estimate_did(df)
            pairs = [(ours.att, r["est"], ours.se, r["se"], ours.ci_low, r["lo"], ours.ci_high, r["hi"], ours.p_value, r["p"])]
        else:
            res = estimate_event_study(df_es, window=6)
            coefs = res.coefficients.set_index("rel_period")
            pairs = []
            for name, est, se, lo, hi, p in zip(r["names"], r["est"], r["se"], r["lo"], r["hi"], r["p"]):
                k = int(name.split("::")[1].replace("k", ""))
                row = coefs.loc[k]
                pairs.append((row.estimate, est, row.se, se, row.ci_low, lo, row.ci_high, hi, None, p))
        rel = 0.0
        for a, b, s, t, lo, rlo, hi, rhi, p, rp in pairs:
            worst["est"] = max(worst["est"], abs(a - b))
            worst["se"] = max(worst["se"], abs(s / t - 1))
            worst["ci"] = max(worst["ci"], abs(lo - rlo), abs(hi - rhi))
            if p is not None:
                worst["p"] = max(worst["p"], abs(p - rp))
            rel = max(rel, abs(s / t - 1), abs(a - b) / max(abs(b), 1e-12))
        a, b, s, t = pairs[0][:4]
        label = key if kind == "did" else f"{key} ({len(pairs)} coefficients)"
        print(f"{label:38s} {a:14.10f} {b:14.10f} {s:10.6f} {t:10.6f} {rel:14.2e}")
    print("\nLargest differences over all datasets:")
    print(f"  estimate (absolute)        {worst['est']:.2e}")
    print(f"  standard error (relative)  {worst['se']:.2e}")
    print(f"  95% interval bounds        {worst['ci']:.2e}")
    print(f"  p-value (DiD, absolute)    {worst['p']:.2e}")


if __name__ == "__main__":
    main()
