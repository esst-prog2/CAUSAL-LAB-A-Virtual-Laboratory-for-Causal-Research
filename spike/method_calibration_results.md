# Causal Methods calibration

## Monte Carlo on the default worlds

| Method | Replications | Bias | RMSE | 95% CI coverage | SE / SD | Rejects no effect (5%) |
|---|---|---|---|---|---|---|
| rct | 200 | +0.0034 | 0.0930 | 94.0% | 0.926 | 100.0% |
| matching | 200 | -0.0097 | 0.0940 | 96.0% | 1.063 | 100.0% |
| iv | 200 | +0.0265 | 0.4198 | 94.0% | 1.003 | 66.0% |
| rdd | 200 | -0.0083 | 0.0746 | 94.5% | 0.947 | 100.0% |
| synthetic_control | 200 | -0.0071 | 0.2325 | — | — | 98.5% |
| dml | 30 | -0.0143 | 0.0409 | 93.3% | 0.921 | 100.0% |

## Break My Design: warning rate per check

| Method | World | Replications | Check | Warning | N/A | Mean score |
|---|---|---|---|---|---|---|
| rct | default | 200 | rct_balance | 11.0% | 0.0% | 94.5 |
| rct | default | 200 | rct_arm_size | 0.0% | 0.0% | 94.5 |
| rct | n = 40 | 200 | rct_balance | 23.0% | 0.0% | 38.5 |
| rct | n = 40 | 200 | rct_arm_size | 100.0% | 0.0% | 38.5 |
| matching | default | 200 | matching_overlap | 6.0% | 0.0% | 98.0 |
| matching | default | 200 | matching_balance | 1.0% | 0.0% | 98.0 |
| matching | default | 200 | matching_extreme_ps | 0.0% | 0.0% | 98.0 |
| matching | default | 200 | matching_ipw_agreement | 1.0% | 0.0% | 98.0 |
| matching | confounding 3 | 200 | matching_overlap | 93.5% | 0.0% | 16.5 |
| matching | confounding 3 | 200 | matching_balance | 100.0% | 0.0% | 16.5 |
| matching | confounding 3 | 200 | matching_extreme_ps | 100.0% | 0.0% | 16.5 |
| matching | confounding 3 | 200 | matching_ipw_agreement | 40.5% | 0.0% | 16.5 |
| iv | default | 200 | iv_weak_instrument | 0.0% | 0.0% | 100.0 |
| iv | default | 200 | iv_overidentification | 0.0% | 100.0% | 100.0 |
| iv | instrument strength 0.3 | 200 | iv_weak_instrument | 69.0% | 0.0% | 31.0 |
| iv | instrument strength 0.3 | 200 | iv_overidentification | 0.0% | 100.0% | 31.0 |
| rdd | default | 200 | rdd_manipulation | 8.0% | 0.0% | 89.0 |
| rdd | default | 200 | rdd_bandwidth | 13.5% | 0.0% | 89.0 |
| rdd | default | 200 | rdd_placebo_cutoffs | 11.5% | 0.0% | 89.0 |
| rdd | curvature 5 | 200 | rdd_manipulation | 12.0% | 0.0% | 82.7 |
| rdd | curvature 5 | 200 | rdd_bandwidth | 26.5% | 0.0% | 82.7 |
| rdd | curvature 5 | 200 | rdd_placebo_cutoffs | 13.5% | 0.0% | 82.7 |
| synthetic_control | default | 200 | sc_pre_fit | 2.0% | 0.0% | 95.8 |
| synthetic_control | default | 200 | sc_leave_one_out | 1.0% | 0.0% | 95.8 |
| synthetic_control | default | 200 | sc_in_time_placebo | 9.5% | 0.0% | 95.8 |
| synthetic_control | noise 3 | 200 | sc_pre_fit | 97.5% | 0.0% | 65.5 |
| synthetic_control | noise 3 | 200 | sc_leave_one_out | 0.0% | 0.0% | 65.5 |
| synthetic_control | noise 3 | 200 | sc_in_time_placebo | 6.0% | 0.0% | 65.5 |
| dml | default | 20 | dml_overlap | 0.0% | 0.0% | 97.5 |
| dml | default | 20 | dml_seed_stability | 5.0% | 0.0% | 97.5 |
