## Why

`tests/test_external_reference.py` (PR #10) showed that Causal Lab's matching estimator picks the same matches as R `Matching` and has the same Abadie-Imbens variance. Its bias-correction regression differs, though:
- Causal Lab fitted it on all controls;
- R `Matching`, Stata `nnmatch` and Abadie & Imbens (2011) fit it on the matched controls, weighted by use.

On the noisy reference dataset this gave a 0.04 SE gap. The user asked on 2026-10-25 to align with the references.

## What Changes

- The bias-correction regression uses the controls that serve as matches, weighted by the number of times each is used.

On 500 Matching worlds, the old and new conventions are statistically equivalent:

| | Bias | RMSE | Coverage |
|---|---|---|---|
| Old (all controls) | −0.0063 | 0.0922 | 96.8% |
| New (matched controls, weighted) | −0.0064 | 0.0937 | 95.8% |

The gain is exact reproducibility in R and Stata.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `matching-estimation`: the bias-correction regression sample, the coverage figures, and a new scenario that reproduces R Matching.

## Impact

- **Code:** `causal_lab/estimators/matching.py`.
- **Tests:** `tests/test_external_reference.py`. The noisy-data matching test now requires agreement to rounding instead of within 0.1 SE.
- **Results:** matching estimates change slightly on every dataset (0.04 SE on the reference dataset); the IPW estimate is unchanged.
