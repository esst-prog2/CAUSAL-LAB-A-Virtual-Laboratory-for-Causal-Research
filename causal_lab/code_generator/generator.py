"""
Code Generator (CAUSAL LAB spec, Section 27).

Produces ready-to-run R, Python, and Stata scripts that reproduce the
DiD analysis configured in the app, so the researcher can leave
CAUSAL LAB and keep working in their own environment with full
reproducibility.
"""
from __future__ import annotations

from dataclasses import dataclass


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


def generate_python_code(p: CodeGenParams) -> str:
    return f'''"""
CAUSAL LAB — auto-generated Python script
Two-way fixed effects Difference-in-Differences
Model: Y_it = alpha_i + gamma_t + beta * D_it + epsilon_it
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
print("\\nATT estimate:", fitted.params["{p.treatment_col}"])
print("Cluster-robust SE:", fitted.bse["{p.treatment_col}"])
'''


def generate_r_code(p: CodeGenParams) -> str:
    return f'''# CAUSAL LAB - auto-generated R script
# Two-way fixed effects Difference-in-Differences
# Model: Y_it = alpha_i + gamma_t + beta * D_it + epsilon_it

library(fixest)

df <- read.csv("{p.data_path}")

model <- feols(
  {p.outcome_col} ~ {p.treatment_col} | {p.unit_col} + {p.time_col},
  data = df,
  cluster = ~{p.cluster()}
)

summary(model)
'''


def generate_stata_code(p: CodeGenParams) -> str:
    return f'''* CAUSAL LAB - auto-generated Stata script
* Two-way fixed effects Difference-in-Differences
* Model: Y_it = alpha_i + gamma_t + beta * D_it + epsilon_it

import delimited "{p.data_path}", clear

encode {p.unit_col}, gen(unit_id)
xtset unit_id {p.time_col}

reghdfe {p.outcome_col} {p.treatment_col}, absorb({p.unit_col} {p.time_col}) vce(cluster {p.cluster()})
'''


def generate_all(p: CodeGenParams) -> dict[str, str]:
    return {
        "python": generate_python_code(p),
        "r": generate_r_code(p),
        "stata": generate_stata_code(p),
    }
