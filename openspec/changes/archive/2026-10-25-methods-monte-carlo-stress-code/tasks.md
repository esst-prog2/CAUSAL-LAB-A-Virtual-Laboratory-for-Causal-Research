## 1. Implementation

- [x] 1.1 Shared method registry; the methods page uses it.
- [x] 1.2 Monte Carlo per method (the IPW bootstrap is skipped in it).
- [x] 1.3 Break My Design per method, calibrated on the method worlds (`spike/method_calibration.py`).
- [x] 1.4 Python, R and Stata code per method; each script run and its agreement written in its header.
- [x] 1.5 Tabs on the Causal Methods page; world config saved in project files; EN and FR messages.
- [x] 1.6 DiD Python script: nested fixed-effects correction.

## 2. Verification

- [x] 2.1 New test files, run in the project venv and in a venv with every reference package; mutants caught.
- [x] 2.2 Validate with `openspec validate methods-monte-carlo-stress-code --strict`.
