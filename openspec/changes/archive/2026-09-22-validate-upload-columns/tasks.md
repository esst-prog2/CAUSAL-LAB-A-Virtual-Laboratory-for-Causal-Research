## 1. Validation helper

- [x] 1.1 Add `causal_lab/utils/validation.py` with `REQUIRED_COLUMNS = ("unit", "period", "Y", "D", "treated_unit")` and `missing_required_columns(df) -> list[str]`, returning the required columns absent from `df.columns` in `REQUIRED_COLUMNS` order.
- [x] 1.2 Add `causal_lab/tests/test_validation.py` (following the existing `sys.path.insert` + plain-function style used in `tests/test_did.py`) covering: all five columns present returns `[]`; one missing column is reported; multiple missing columns are all reported, in `REQUIRED_COLUMNS` order. Verify by running the test file directly (`python causal_lab/tests/test_validation.py`), matching how the existing tests are run.

## 2. Wire validation into the upload handler

- [x] 2.1 In `causal_lab/app.py`'s CSV upload block (Virtual Lab page), import `REQUIRED_COLUMNS`/`missing_required_columns` from `utils.validation` and call `missing_required_columns(up_df)` right after a successful `pd.read_csv`, before any `st.session_state.uploaded_df`/`virtual_df` assignment.
- [x] 2.2 When columns are missing, show `st.error` naming every missing column (and the full expected column list) and do NOT assign `st.session_state.uploaded_df` or `st.session_state.virtual_df` — the previously active dataset, if any, stays active. Verify by reading the modified block: the missing-columns branch must contain no `st.session_state` writes.
- [x] 2.3 When no columns are missing, keep the existing behavior unchanged: set `uploaded_df`, clear `virtual_df`, show the existing success message with row count and detected columns. Verify with a manual `streamlit run causal_lab/app.py` smoke test: upload a CSV with all five columns (succeeds as before) and one missing `D` (shows the new named error, dataset unchanged).

## 3. Close the loop on the spec

- [x] 3.1 Run the full existing test suite (`causal_lab/tests/test_dgp.py`, `test_did.py`, `test_recommendation.py`, plus the new `test_validation.py`) and verify all pass.
- [x] 3.2 Once implemented and tested, sync or archive this change (`openspec archive validate-upload-columns`) so `openspec/specs/real-world-data-upload/spec.md` reflects the renamed, modified requirement, and verify `openspec validate --specs` still passes.
