## Why

After the cluster convention was aligned with the DiD (change 2026-10-25-align-stress-cluster-correction), Parallel Trends warned on 18–20% of threat-free Virtual Worlds at a nominal 10% level. A default world has 100 units, of which 30 are treated, and 10 pre-periods. The clustered Wald test of its q = 9 leads therefore over-rejects; counting the unit dummies had partly hidden this.

On 2026-10-25 the user asked for a correction. False-alarm rates on the same clean worlds:

| Variant | False alarms |
|---|---|
| Classical F | 10.5% (the noise is i.i.d.) |
| Hotelling F(q, G − q) | 14% |
| CR2 + Hotelling | 14% |
| Hotelling on the 30 treated clusters | 3% |
| Wild cluster restricted bootstrap | 10.4% (1,000 worlds) |

## What Changes

- The Parallel Trends p-value comes from the wild cluster restricted bootstrap of the clustered Wald statistic (Rademacher weights): exhaustive for G ≤ 9 units, otherwise 999 seeded draws. Any constant small-sample factor cancels, so the dummy-count convention no longer matters for this check.
- Fixed effects are removed by alternating projections, which is exact on unbalanced panels and needs no dense dummy matrix.
- With fewer than 5 units the check is N/A, because it could never warn at 10%.
- The verdict thresholds (0.10, 0.01) are unchanged.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `break-my-design-stress-test`: the parallel-trends requirement describes the bootstrap and the 5-unit minimum.

## Impact

- **Code:** `causal_lab/robustness_engine/stress_test.py`; one new locale key, `stress.pt.too_few_units`, in EN and FR.
- **Tests:** `tests/test_stress_hand_computed_regressions.py` (Parallel Trends section rewritten) and `tests/test_error_handling.py`.
- **Calibration spike** (`spike/stress_test_calibration_results_2026-10-25_bootstrap.md`):

  | | Before | After |
  |---|---|---|
  | Parallel Trends false alarms | 20% | 10% |
  | Parallel Trends detection (severe) | 100% | 100% |
  | Clean-world score | 90.8 | 92.8 |

- **Power** (500 worlds per level, `differential_trend`):

  | Level | Before | After |
  |---|---|---|
  | low | 22% | 14% |
  | medium | 54% | 37% |
  | high | 92% | 83% |
  | severe | 100% | 99.8% |

  The drop is power that came from over-rejection.
- **Runtime:** 0.06 s per check on a default world, 1.8 s on 2,000 units × 10 pre-periods.
- **Card & Krueger:** unchanged (one pre-period: N/A).
