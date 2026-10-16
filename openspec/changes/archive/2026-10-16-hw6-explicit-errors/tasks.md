## 1. Explicit errors

- [x] 1.1 DiD: boolean → 0/1, text → error, no NaN fallback
- [x] 1.2 Upload: indicator and numeric column checks
- [x] 1.3 Stress test: narrow handlers, N/A on numerical failure, guard Serial Correlation
- [x] 1.4 Leave-one-out and matching bootstrap: narrow handlers; bootstrap count shown

## 2. Tests and records

- [x] 2.1 `test_error_handling.py`, AppTest for invalid upload, mutation checks
- [x] 2.2 Review record 05
