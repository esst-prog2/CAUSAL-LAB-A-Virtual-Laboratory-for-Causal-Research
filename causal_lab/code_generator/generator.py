"""
Code Generator (CAUSAL LAB spec, Section 27).

Produces ready-to-run R, Python, and Stata scripts that reproduce the
DiD analysis configured in the app, so the researcher can leave
CAUSAL LAB and keep working in their own environment with full
reproducibility.

The code is identical in every language; only the comments and the
printed labels follow the interface language (locale keys gen.*).
"""
from __future__ import annotations

from dataclasses import dataclass

from utils.i18n import DEFAULT_LANGUAGE, t


@dataclass
class CodeGenParams:
    data_path: str = "data.csv"
    outcome_col: str = "Y"
    treatment_col: str = "D"
    unit_col: str = "unit"
    time_col: str = "period"
    cluster_col: str | None = None

    def cluster(self) -> str:
        return self.cluster_col or self.unit_col


MODEL = "Y_it = alpha_i + gamma_t + beta * D_it + epsilon_it"


def generate_python_code(p: CodeGenParams, lang: str = DEFAULT_LANGUAGE) -> str:
    return f'''"""
CAUSAL LAB — {t("gen.header_python", lang)}
{t("gen.model_name", lang)}
{t("gen.model", lang)}: {MODEL}
"""
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("{p.data_path}")
df["{p.unit_col}"] = df["{p.unit_col}"].astype("category")
df["{p.time_col}"] = df["{p.time_col}"].astype("category")

formula = "{p.outcome_col} ~ {p.treatment_col} + C({p.unit_col}) + C({p.time_col})"
model = smf.ols(formula, data=df)
fitted = model.fit(cov_type="cluster", cov_kwds={{"groups": df["{p.cluster()}"]}})

print(fitted.summary())
print("\\n{t("gen.att_label", lang)}:", fitted.params["{p.treatment_col}"])
print("{t("gen.se_label", lang)}:", fitted.bse["{p.treatment_col}"])
'''


def generate_r_code(p: CodeGenParams, lang: str = DEFAULT_LANGUAGE) -> str:
    return f'''# CAUSAL LAB - {t("gen.header_r", lang)}
# {t("gen.model_name", lang)}
# {t("gen.model", lang)}: {MODEL}

library(fixest)

df <- read.csv("{p.data_path}")

model <- feols(
  {p.outcome_col} ~ {p.treatment_col} | {p.unit_col} + {p.time_col},
  data = df,
  cluster = ~{p.cluster()}
)

summary(model)
'''


def generate_stata_code(p: CodeGenParams, lang: str = DEFAULT_LANGUAGE) -> str:
    return f'''* CAUSAL LAB - {t("gen.header_stata", lang)}
* {t("gen.model_name", lang)}
* {t("gen.model", lang)}: {MODEL}

* {t("gen.requires_reghdfe", lang)}:  ssc install reghdfe, replace
import delimited "{p.data_path}", clear

reghdfe {p.outcome_col} {p.treatment_col}, absorb({p.unit_col} {p.time_col}) vce(cluster {p.cluster()})
'''


def generate_all(p: CodeGenParams, lang: str = DEFAULT_LANGUAGE) -> dict[str, str]:
    return {
        "python": generate_python_code(p, lang),
        "r": generate_r_code(p, lang),
        "stata": generate_stata_code(p, lang),
    }
