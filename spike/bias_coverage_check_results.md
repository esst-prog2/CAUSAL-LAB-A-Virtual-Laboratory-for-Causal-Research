# Does the 10% and 90% rule depend on precision?

From `spike/bias_coverage_check.py`: 1000 worlds per cell, the app's world and estimator, seeds from 20261029. Monte Carlo SE of a coverage near 0.9 is about 0.01.

## A bias of exactly 10% of the effect (0.05), added to the estimates of clean worlds

| Units | Model SE | Empirical SE | Bias / SE | Coverage, simulated | Coverage, normal formula |
|---|---|---|---|---|---|
| 100 | 0.0967 | 0.0975 | 0.517 | 0.922 | 0.935 |
| 400 | 0.0486 | 0.0485 | 1.029 | 0.828 | 0.827 |

## A real threat: anticipation at "high"

The bias does not shrink with the sample, so coverage falls as the SE falls.

| Units | Bias (MCSE) | Share of the effect | Model SE | Coverage (MCSE) | Width of the 95% CI |
|---|---|---|---|---|---|
| 100 | +0.0561 (0.0031) | 11.2% | 0.0967 | 0.915 (0.009) | 0.384 |
| 400 | +0.0601 (0.0015) | 12.0% | 0.0486 | 0.769 (0.013) | 0.191 |

## A true effect of zero, where relative bias does not exist

Judge absolute bias and the size of the test (rejection rate, nominal 5%).

| Units | Bias (MCSE) | Coverage (MCSE) | Rejection rate of H0: effect = 0 |
|---|---|---|---|
| 100 | -0.0039 (0.0031) | 0.949 (0.007) | 0.051 |
| 400 | +0.0001 (0.0015) | 0.950 (0.007) | 0.050 |
