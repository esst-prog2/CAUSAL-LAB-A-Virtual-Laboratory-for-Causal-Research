## 1. Implementation

- [x] 1.1 Compare both conventions on 500 Matching worlds (bias, RMSE, coverage, SE/SD).
- [x] 1.2 Fit the bias regression on the matched controls weighted by use in `estimators/matching.py`.

## 2. Tests and specification

- [x] 2.1 Require agreement to rounding with R Matching on both reference datasets.
- [x] 2.2 Update the nearest-neighbour matching requirement. Verify with `openspec validate matching-bias-regression-matched-controls --strict`.
