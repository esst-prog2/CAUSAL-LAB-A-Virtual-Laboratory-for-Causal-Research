## Why

On 2026-10-31 the user asked for every estimation method to be rigorous.

Each estimator already matches a reference package, number for number. Their statistical behaviour had only been checked on 200 worlds (30 for DML). The size of each test was never measured, and the coverage of each confidence interval was never measured with its Monte Carlo error.

## What Changes

- **`spike/estimator_validation.py`:** 23 scenarios covering every method in its default world, the same world with a true effect of 0, and a small sample, plus RDD with robust inference, IV with a weak instrument, and Callaway & Sant'Anna. There are 1,000 worlds per scenario (200 for DML, 500 for Callaway & Sant'Anna), and every replication is stored.
- **RDD:** the app reports robust bias-corrected inference by default. The conventional interval covered 91.6% at n = 400; the robust one covers 93.8%.
- **IV:** the result gives the heteroskedasticity-robust Anderson-Rubin confidence set. With a weak instrument and strong endogeneity it covers 95.3%, against 90.1% for the 2SLS Wald interval; its size is 4.7%, against 9.9%. The weak-instrument warning points to it.
- **Synthetic control:** a warning when there are too few donors for the placebo test to reject at 5% (fewer than 19).
- **Callaway & Sant'Anna:** the result reports its smallest cohort. Below 5 units, the page and the report warn: the interval covered 91.4% and the size was 8.6%. A jackknife standard error was tried and was not significantly better.
- **Bibliography:** Anderson & Rubin (1949) and Andrews, Stock & Sun (2019), both checked against Crossref.
- **README:** the results and what changed.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `iv-estimation`: the Anderson-Rubin confidence set.
- `rdd-estimation`: robust inference by default in the app.
- `synthetic-control-estimation`: the few-donors warning.
- `staggered-did-estimation`: the small-cohort warning.

## Impact

New `tests/test_estimator_rigour.py`:
- the Anderson-Rubin set equals an independent statsmodels inversion, with one and with two instruments;
- the set is unbounded with a useless instrument;
- the RDD default is robust;
- the few-donors warning;
- the small-cohort warning.

The RDD page tests are updated for the new default.
