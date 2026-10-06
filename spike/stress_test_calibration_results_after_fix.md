# Stress-test calibration spike (issue #3) — after the fix

Re-run on 2026-10-06 after change `fix-correctness-and-readme-gaps`, which recalibrated the checks and paired each with its own threat lever (Parallel Trends with `differential_trend`, Anticipation with `anticipation`). The original result is in `stress_test_calibration_results.md`.

Clean-world mean Identification Strength score (n=200): **92.2 / 100**

| Check | False-alarm rate (clean world) | Detection rate (threat = severe) |
|---|---|---|
| Parallel Trends | 14% | 100% |
| Anticipation | 8% | 97% |
| Spillovers | 8% | 100% |
| Serial Correlation | 0% | 100% |
| Heterogeneous Effects | 10% | 100% |
