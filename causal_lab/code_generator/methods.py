"""
Python, R and Stata scripts that reproduce a Causal Methods estimate with
the reference packages Causal Lab is tested against
(tests/test_external_reference.py), using the page's column mapping and
options. Each script says whether it gives Causal Lab's numbers exactly
(checked by running it: tests/test_method_code.py and the run log in
PLANNING_LOG), close numbers (and why), or could not be checked (Stata).
Comments follow the interface language (locale keys gen.m.*).
"""
from __future__ import annotations

from utils.i18n import DEFAULT_LANGUAGE, t, tf

PACKAGES = {      # method: (Python, R, Stata) reference
    "rct": ("statsmodels (HC2)", "estimatr", "regress, vce(hc2)"),
    "matching": ("numpy + scikit-learn (Abadie-Imbens, as Causal Lab)", "Matching", "teffects nnmatch"),
    "iv": ("linearmodels", "estimatr", "ivregress 2sls"),
    "rdd": ("rdrobust", "rdrobust", "rdrobust"),
    "synthetic_control": ("pysyncon", "Synth", "synth"),
    "dml": ("DoubleML", "DoubleML (mlr3 + ranger)", "ddml + pystacked"),
}
# What running each script on its method world gave, against Causal Lab
# (2026-10-25; tests/test_method_code.py re-checks the Python ones it can run):
#   exact      estimate and SE equal to 10 digits
#   sc         estimate within 0.01% (both optimizers stop at 1e-12 tolerances)
#   close      Synth in R: estimate within 0.1% (other optimizer)
#   differs    DoubleML in R: about one SE away (ranger forests and other folds)
#   unchecked  Stata: no Stata available to run it
STATUS = {        # method: (Python, R); Stata is always "unchecked"
    "rct": ("exact", "exact"), "matching": ("exact", "exact"), "iv": ("exact", "exact"),
    "rdd": ("exact", "exact"), "synthetic_control": ("sc", "close"), "dml": ("exact", "differs"),
}


def _list(cols) -> str:
    return "[" + ", ".join(repr(c) for c in cols) + "]"


def _r_vec(cols) -> str:
    return "c(" + ", ".join(f'"{c}"' for c in cols) + ")"


def _r_cat(lang: str, estimate: str, se: str) -> str:
    return (f'cat("{t("gen.m.estimate", lang)}:", sprintf("%.10f", {estimate}), "\\n")\n'
            f'cat("{t("gen.m.se", lang)}:", sprintf("%.10f", {se}), "\\n")\n')


def _header(method: str, language: str, lang: str, comment: str, m: dict | None = None) -> str:
    package = PACKAGES[method][("python", "r", "stata").index(language)]
    key = "unchecked" if language == "stata" else STATUS[method][("python", "r").index(language)]
    if language != "stata" and method == "synthetic_control" and (m or {}).get("covariates"):
        key = "sc_v"           # the importance V is searched; another optimizer can stop elsewhere
    status = t(f"gen.m.status.{key}", lang)
    lines = [f"CAUSAL LAB - {tf('gen.m.header', lang, method=t(f'method.{method}', lang))}",
             tf("gen.m.reference", lang, package=package), status]
    return "\n".join(f"{comment} {line}" for line in lines) + "\n"


# --------------------------------------------------------------------------
def _sc_python_fit(m) -> str:
    covs = list(m.get("covariates") or [])
    if covs:
        return f'''# Predictors: pre-treatment means of the covariates and of the outcome; V is searched
# to minimise the pre-treatment outcome error (Abadie, Diamond & Hainmueller 2010).
prep = Dataprep(foo=df, predictors={_list(covs)}, predictors_op="mean", dependent="{m["outcome"]}",
                unit_variable="{m["unit"]}", time_variable="{m["period"]}", treatment_identifier=treated,
                controls_identifier=donors, time_predictors_prior=pre,
                special_predictors=[("{m["outcome"]}", pre, "mean")], time_optimize_ssr=pre)
synth = Synth()
synth.fit(dataprep=prep, optim_method="Nelder-Mead", optim_initial="equal")
'''
    return f'''prep = Dataprep(foo=df, predictors=[], predictors_op="mean", dependent="{m["outcome"]}",
                unit_variable="{m["unit"]}", time_variable="{m["period"]}", treatment_identifier=treated,
                controls_identifier=donors, time_predictors_prior=pre,
                special_predictors=[("{m["outcome"]}", [p], "mean") for p in pre], time_optimize_ssr=pre)
# pysyncon divides each predictor by its standard deviation; V = sd^2 undoes it, so the
# weights minimise the plain sum of squared pre-treatment gaps, as in Causal Lab.
x0, x1 = prep.make_covariate_mats()
v = pd.concat([x0, x1], axis=1).std(axis=1).to_numpy() ** 2
synth = Synth()
synth.fit(dataprep=prep, custom_V=v)
'''


def _python(method, m, o, path, lang) -> str:
    head = _header(method, "python", lang, "#", m)
    est, se = t("gen.m.estimate", lang), t("gen.m.se", lang)
    if method == "rct":
        covs = list(m.get("covariates") or [])
        body = f'''import pandas as pd
import statsmodels.api as sm

df = pd.read_csv("{path}")[{_list([m["outcome"], m["treatment"]] + covs)}].dropna()
X = df[["{m["treatment"]}"]].astype(float)
'''
        if covs:
            body += f'''# Lin (2013): centred covariates and their interactions with the treatment
xc = df[{_list(covs)}] - df[{_list(covs)}].mean()
X = pd.concat([X, xc, xc.mul(df["{m["treatment"]}"], axis=0).add_prefix("D_x_")], axis=1)
'''
        body += f'''fit = sm.OLS(df["{m["outcome"]}"].astype(float), sm.add_constant(X, has_constant="add")).fit(cov_type="HC2")
print("{est}:", fit.params["{m["treatment"]}"])
print("{se}:", fit.bse["{m["treatment"]}"])
'''
    elif method == "matching":
        covs = list(m["covariates"])
        body = f'''import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

df = pd.read_csv("{path}")[{_list([m["outcome"], m["treatment"]] + covs)}].dropna().reset_index(drop=True)
y = df["{m["outcome"]}"].to_numpy(float)
d = df["{m["treatment"]}"].to_numpy(int)
x = df[{_list(covs)}].to_numpy(float)

# 1-NN Mahalanobis matching with replacement
cov = np.atleast_2d(np.cov(x, rowvar=False))
cov += np.eye(len(cov)) * 1e-9 * np.trace(cov)
z = x @ np.linalg.cholesky(np.linalg.inv(cov))
t_idx, c_idx = np.flatnonzero(d == 1), np.flatnonzero(d == 0)
nn = NearestNeighbors(n_neighbors=2).fit(z[c_idx])
match = c_idx[nn.kneighbors(z[t_idx], n_neighbors=1, return_distance=False)[:, 0]]

# Bias correction: regression of Y on X among matched controls, weighted by use
k = np.bincount(match, minlength=len(y))
used = np.flatnonzero(k > 0)
w = np.sqrt(k[used])
beta = np.linalg.lstsq(np.column_stack([np.ones(len(used)), x[used]]) * w[:, None], y[used] * w, rcond=None)[0]
mu0 = lambda rows: np.column_stack([np.ones(len(rows)), x[rows]]) @ beta
y0_hat = y[match] + mu0(t_idx) - mu0(match)
att = np.mean(y[t_idx] - y0_hat)

# Abadie-Imbens variance, sigma2 from each control's nearest other control
neighbour = c_idx[nn.kneighbors(z[c_idx], n_neighbors=2, return_distance=False)[:, 1]]
sigma2 = (y[c_idx] - y[neighbour]) ** 2 / 2
kc = k[c_idx]
se_att = np.sqrt(np.sum((y[t_idx] - y0_hat - att) ** 2) + np.sum(kc * (kc - 1) * sigma2)) / len(t_idx)
print("{est} (ATT):", att)
print("{se}:", se_att)
'''
    elif method == "iv":
        instruments, controls = list(m["instruments"]), list(m.get("controls") or [])
        body = f'''import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

df = pd.read_csv("{path}")[{_list([m["outcome"], m["treatment"]] + instruments + controls)}].dropna().astype(float)
fit = IV2SLS(df["{m["outcome"]}"], sm.add_constant(df[{_list(controls)}], has_constant="add"),
             df[["{m["treatment"]}"]], df[{_list(instruments)}]).fit(cov_type="robust")
print(fit.first_stage)
print("{est}:", fit.params["{m["treatment"]}"])
print("{se}:", fit.std_errors["{m["treatment"]}"])
'''
    elif method == "rdd":
        treatment = m.get("treatment")
        columns = [m["outcome"], m["running"]] + ([treatment] if treatment else [])
        fuzzy = f', fuzzy=df["{treatment}"].to_numpy(float)' if treatment else ""
        row = 2 if o.get("inference") == "robust" else 0           # rdrobust rows: Conventional, Bias-Corrected, Robust
        body = f'''import pandas as pd
from rdrobust import rdrobust

df = pd.read_csv("{path}")[{_list(columns)}].dropna()
fit = rdrobust(df["{m["outcome"]}"].to_numpy(float), df["{m["running"]}"].to_numpy(float), c={o["cutoff"]!r},
               h={o["bandwidth_used"]!r}, kernel="triangular", p=1, vce="hc1"{fuzzy})
print(fit)
print("{est} ({t("gen.m.conventional", lang)}):", float(fit.coef.iloc[0, 0]))
print("{se} ({t(f"gen.m.rdd_row.{row}", lang)}):", float(fit.se.iloc[{row}, 0]))
'''
    elif method == "synthetic_control":
        body = f'''import pandas as pd
from pysyncon import Dataprep, Synth

df = pd.read_csv("{path}")
treated, start = {o["treated_unit"]!r}, {o["treatment_period"]!r}
periods = sorted(df["{m["period"]}"].unique())
pre, post = [p for p in periods if p < start], [p for p in periods if p >= start]
donors = sorted(u for u in df["{m["unit"]}"].unique() if u != treated)
{_sc_python_fit(m)}print(synth.weights())
print("{est}:", synth.att(time_period=post)["att"])
'''
    elif method == "dml":
        covs = list(m["covariates"])
        body = f'''import pandas as pd
from doubleml import DoubleMLData, DoubleMLPLR
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

df = pd.read_csv("{path}")[{_list([m["outcome"], m["treatment"]] + covs)}].dropna().astype(float)
covariates = {_list(covs)}
folds = list(KFold(n_splits=5, shuffle=True, random_state=0).split(df[covariates]))
forest = RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=0, n_jobs=1)
plr = DoubleMLPLR(DoubleMLData(df, y_col="{m["outcome"]}", d_cols="{m["treatment"]}", x_cols=covariates),
                  ml_l=forest, ml_m=forest, n_folds=5, score="partialling out", draw_sample_splitting=False)
plr.set_sample_splitting(folds)
plr.fit()
print(plr.summary)
print("{est}:", float(plr.coef[0]))
print("{se}:", float(plr.se[0]))
'''
    else:
        raise KeyError(method)
    return head + "\n" + body


# --------------------------------------------------------------------------
def _sc_r_fit(m) -> str:
    covs = list(m.get("covariates") or [])
    if covs:
        return f'''# Predictors: pre-treatment means of the covariates and of the outcome; synth() searches V.
prep <- dataprep(foo = df, predictors = {_r_vec(covs)}, predictors.op = "mean", dependent = "{m["outcome"]}",
                 unit.variable = "unit_num", unit.names.variable = "unit_name", time.variable = "{m["period"]}",
                 special.predictors = list(list("{m["outcome"]}", pre, "mean")),
                 treatment.identifier = treated, controls.identifier = setdiff(unique(df$unit_num), treated),
                 time.predictors.prior = pre, time.optimize.ssr = pre, time.plot = periods)
fit <- synth(prep)
'''
    return f'''prep <- dataprep(foo = df, predictors = NULL, dependent = "{m["outcome"]}", unit.variable = "unit_num",
                 unit.names.variable = "unit_name", time.variable = "{m["period"]}",
                 special.predictors = lapply(pre, function(p) list("{m["outcome"]}", p, "mean")),
                 treatment.identifier = treated, controls.identifier = setdiff(unique(df$unit_num), treated),
                 time.predictors.prior = pre, time.optimize.ssr = pre, time.plot = periods)
# Synth scales each predictor by its standard deviation; custom.v = sd^2 undoes it.
v <- apply(cbind(prep$X0, prep$X1), 1, sd)^2
fit <- synth(prep, custom.v = v)
'''


def _r(method, m, o, path, lang) -> str:
    head = _header(method, "r", lang, "#", m)
    if method == "rct":
        covs = list(m.get("covariates") or [])
        fit = (f'lm_lin({m["outcome"]} ~ {m["treatment"]}, covariates = ~ {" + ".join(covs)}, data = df, se_type = "HC2")'
               if covs else f'lm_robust({m["outcome"]} ~ {m["treatment"]}, data = df, se_type = "HC2")')
        body = f'''library(estimatr)

df <- na.omit(read.csv("{path}")[, {_r_vec([m["outcome"], m["treatment"]] + covs)}])
fit <- {fit}
summary(fit)
{_r_cat(lang, f'coef(fit)[["{m["treatment"]}"]]', f'fit$std.error[["{m["treatment"]}"]]')}'''
    elif method == "matching":
        covs = list(m["covariates"])
        body = f'''library(Matching)

df <- na.omit(read.csv("{path}")[, {_r_vec([m["outcome"], m["treatment"]] + covs)}])
fit <- Match(Y = df${m["outcome"]}, Tr = df${m["treatment"]}, X = as.matrix(df[, {_r_vec(covs)}]),
             estimand = "ATT", M = 1, Weight = 2, BiasAdjust = TRUE, ties = TRUE, Var.calc = 1)
summary(fit)
{_r_cat(lang, 'fit$est', 'fit$se')}'''
    elif method == "iv":
        instruments, controls = list(m["instruments"]), list(m.get("controls") or [])
        rhs = " + ".join([m["treatment"]] + controls)
        first = " + ".join(instruments + controls)
        body = f'''library(estimatr)

df <- na.omit(read.csv("{path}")[, {_r_vec([m["outcome"], m["treatment"]] + instruments + controls)}])
fit <- iv_robust({m["outcome"]} ~ {rhs} | {first}, data = df, se_type = "HC0", diagnostics = TRUE)
summary(fit)
{_r_cat(lang, f'coef(fit)[["{m["treatment"]}"]]', f'fit$std.error[["{m["treatment"]}"]]')}'''
    elif method == "rdd":
        treatment = m.get("treatment")
        columns = [m["outcome"], m["running"]] + ([treatment] if treatment else [])
        fuzzy = f", fuzzy = df${treatment}" if treatment else ""
        row = 3 if o.get("inference") == "robust" else 1
        body = f'''library(rdrobust)

df <- na.omit(read.csv("{path}")[, {_r_vec(columns)}])
fit <- rdrobust(df${m["outcome"]}, df${m["running"]}, c = {o["cutoff"]!r}, h = {o["bandwidth_used"]!r},
                kernel = "triangular", p = 1, vce = "hc1"{fuzzy})
summary(fit)   # {t("gen.m.conventional_row", lang)}
{_r_cat(lang, 'fit$coef[1]', f'fit$se[{row}]')}'''
    elif method == "synthetic_control":
        treated = o["treated_unit"]
        body = f'''library(Synth)

df <- read.csv("{path}")
df$unit_num <- as.numeric(factor(df${m["unit"]}))      # Synth needs numeric unit ids
df$unit_name <- as.character(df${m["unit"]})
treated <- unique(df$unit_num[df$unit_name == "{treated}"])
start <- {o["treatment_period"]!r}
periods <- sort(unique(df${m["period"]}))
pre <- periods[periods < start]
{_sc_r_fit(m)}gaps <- prep$Y1plot - prep$Y0plot %*% fit$solution.w
print(round(fit$solution.w, 4))
cat("{t("gen.m.estimate", lang)}:", mean(gaps[periods >= start]), "\\n")
'''
    elif method == "dml":
        covs = list(m["covariates"])
        body = f'''library(DoubleML)
library(mlr3)
library(mlr3learners)

df <- na.omit(read.csv("{path}")[, {_r_vec([m["outcome"], m["treatment"]] + covs)}])
data <- double_ml_data_from_data_frame(df, y_col = "{m["outcome"]}", d_cols = "{m["treatment"]}",
                                       x_cols = {_r_vec(covs)})
forest <- lrn("regr.ranger", num.trees = 200, min.node.size = 5)
set.seed(0)
plr <- DoubleMLPLR$new(data, ml_l = forest, ml_m = forest$clone(), n_folds = 5, score = "partialling out")
plr$fit()
print(plr)
{_r_cat(lang, 'plr$coef[[1]]', 'plr$se[[1]]')}'''
    else:
        raise KeyError(method)
    return head + "\n" + body


# --------------------------------------------------------------------------
def _stata(method, m, o, path, lang) -> str:
    head = _header(method, "stata", lang, "*")
    load = f'import delimited "{path}", clear'
    if method == "rct":
        covs = list(m.get("covariates") or [])
        if covs:
            centred = "\n".join(f"summarize {c}, meanonly\ngenerate c_{c} = {c} - r(mean)" for c in covs)
            body = f'''{load}
* Lin (2013): centred covariates interacted with the treatment
{centred}
regress {m["outcome"]} i.{m["treatment"]}##c.({" ".join("c_" + c for c in covs)}), vce(hc2)
'''
        else:
            body = f'''{load}
regress {m["outcome"]} i.{m["treatment"]}, vce(hc2)
'''
    elif method == "matching":
        covs = " ".join(m["covariates"])
        body = f'''{load}
teffects nnmatch ({m["outcome"]} {covs}) ({m["treatment"]}), atet nneighbor(1) metric(mahalanobis) ///
    biasadj({covs}) vce(robust, nn(1))
'''
    elif method == "iv":
        controls = " ".join(m.get("controls") or [])
        body = f'''{load}
ivregress 2sls {m["outcome"]} {controls} ({m["treatment"]} = {" ".join(m["instruments"])}), vce(robust)
estat firststage
'''
    elif method == "rdd":
        body = f'''{load}
* ssc install rdrobust
rdrobust {m["outcome"]} {m["running"]}, c({o["cutoff"]!r}) h({o["bandwidth_used"]!r}) kernel(triangular) p(1) vce(hc1){f" fuzzy({m['treatment']})" if m.get("treatment") else ""}
'''
    elif method == "synthetic_control":
        covs = list(m.get("covariates") or [])
        lags = (" ".join(covs + [m["outcome"]]) if covs
                else " ".join(f'{m["outcome"]}({p})' for p in o["pre_periods"]))
        body = f'''{load}
* ssc install synth ; {t("gen.m.stata_numeric_units", lang)}
encode {m["unit"]}, generate(unit_num)
tsset unit_num {m["period"]}
* {tf("gen.m.stata_trunit", lang, unit=o["treated_unit"], code=o["treated_code"])}
synth {m["outcome"]} {lags}, trunit({o["treated_code"]}) trperiod({o["treatment_period"]!r})
'''
    elif method == "dml":
        covs = " ".join(m["covariates"])
        body = f'''{load}
* ssc install ddml ; ssc install pystacked
ddml init partial, kfolds(5)
ddml E[Y|X]: pystacked {m["outcome"]} {covs}, type(reg) method(rf)
ddml E[D|X]: pystacked {m["treatment"]} {covs}, type(reg) method(rf)
ddml crossfit
ddml estimate, robust
'''
    else:
        raise KeyError(method)
    return head + "\n" + body


def code_options(method: str, df, mapping: dict, options: dict, result) -> dict:
    """The page's options plus what the scripts need from the data and the
    estimate: the RDD bandwidth actually used, and for synthetic control the
    pre-treatment periods and the treated unit's code after Stata's encode
    (alphabetical order of the unit labels, from 1)."""
    # Native Python values: under NumPy 2 repr(np.int64(20)) is "np.int64(20)",
    # which would end up in the generated code.
    out = {k: _native(v) for k, v in options.items()}
    if method == "rdd":
        out["bandwidth_used"] = float(result.details["bandwidth"])
    if method == "synthetic_control":
        out["pre_periods"] = sorted(_native(p) for p in df[mapping["period"]].unique()
                                    if p < options["treatment_period"])
        labels = sorted({str(u) for u in df[mapping["unit"]].unique()})
        out["treated_code"] = labels.index(str(options["treated_unit"])) + 1
    return out


def _native(value):
    return value.item() if hasattr(value, "item") and not isinstance(value, (list, dict)) else value


def generate_method_code(method: str, mapping: dict, options: dict, data_path: str = "data.csv",
                         lang: str = DEFAULT_LANGUAGE) -> dict[str, str]:
    """{"python": ..., "r": ..., "stata": ...} for `method`; `options` as
    returned by code_options."""
    return {"python": _python(method, mapping, options, data_path, lang),
            "r": _r(method, mapping, options, data_path, lang),
            "stata": _stata(method, mapping, options, data_path, lang)}
