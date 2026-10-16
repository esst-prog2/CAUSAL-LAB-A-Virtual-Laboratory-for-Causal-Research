## 1. Stress test

- [x] 1.1 N/A verdict for non-computable checks; score over computable checks only, None if there are none
- [x] 1.2 Explicit keyword-only `ids_encode_neighbourhood` in `run_stress_test`; app passes True only for a Virtual World
- [x] 1.3 Serial Correlation N/A below three periods
- [x] 1.4 Break My Design page: N/A shown as info, score basis "k of 5", message when no score

## 2. Estimators and data

- [x] 2.1 DiD clustered SE without the nested unit dummies; exact test against a hand-written CR1 sandwich
- [x] 2.2 PanelOLS reference configured without effect counting (`auto_df=False`)
- [x] 2.3 Card & Krueger unit = store row; test of 410 stores and SE ≈ 1.36
- [x] 2.4 Robust DiD drops and counts incomplete units; the app shows the count

## 3. Locales and docs

- [x] 3.1 EN/FR keys for N/A, new messages, score basis, dropped units
- [x] 3.2 README known limitations and review record 03
