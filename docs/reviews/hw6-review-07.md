# HW6 review 7 — Configuration and unsafe defaults

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 6 (`1bcc4bc`)
- **Criteria** (slide points copied by the user): defaults that silently do something other than asked; settings accepted without validation; inputs that can harm the running system; configuration that is undocumented or insecure.

## Scope and method

- **Searches** for constructs that can be unsafe with user input: `unsafe_allow_html`, `sympify` / `parse_expr`, `eval`, `exec`, `pickle`, `subprocess`, `os.system`. Also a check for any Streamlit configuration file (`.streamlit/config.toml`; none exists).
- **Probes:**
  - every configuration object and string-valued option reachable from the app or the public functions: `VirtualWorldConfig`, the `comparison` and `n_bootstrap` options of the robust DiD;
  - the free model editor, with large constants. Each probe was run under a `timeout`.
- **Files examined:** `theory_engine/game.py`, `ui/theory_page.py`, `simulation_engine/dgp.py`, `estimators/staggered_did.py`, `app.py` (widget bounds), `.gitignore`.

## Findings

| # | Finding | Severity | Evidence | Action |
|---|---|---|---|---|
| 7.1 | **The model editor can block the server.** Tokens are whitelisted, but sympy evaluates constants exactly while parsing, so `9**9**9` (a 369-million-digit integer) never returns. Streamlit runs every session in one Python process, so all users are blocked. | High | `timeout 20 python -c "parse_expression('9**9**9', …)"` → killed, exit 124 | **Fixed.** The text is first parsed without evaluation. The size of every constant sub-expression is bounded from its tree, without computing it. Above `MAX_CONSTANT_DIGITS = 1000` it is rejected with a translated error. The bound is agent-chosen and documented in the code: the catalogue uses exponents ≤ 2, and 1000 digits are instant. Re-probe: `9**9**9`, `x**(9**9**9)`, `exp(9**9**9)` and a 4-level tower are all refused in < 1 ms; `10**999*x`, `2^3*x` and `1/3*x` still parse |
| 7.2 | **Silent fallback in the robust DiD.** Any `comparison` other than `"never_treated"` ran the not-yet-treated comparison, while the result reported the misspelt value. `n_bootstrap = 1` gave a NaN SE without an error. | Medium | `estimate_staggered_did(df, comparison="never-treated").comparison` → `"never-treated"` | **Fixed.** Only `never_treated` and `not_yet_treated`, and `n_bootstrap ≥ 2`, are accepted; anything else raises an error naming the value |
| 7.3 | **Virtual World values clipped or crashing.** `n_units = 1` gave a world without a treated unit; `share_treated = 1.5` was clipped silently; `noise_sd = -1` crashed in numpy (`scale < 0`); `spillovers = "huge"` gave a bare `KeyError`. The app's widgets keep users inside valid bounds, but the functions are public and used by tests and the spike. | Low | probes listed in `test_config_safety.py` | **Fixed.** `generate` validates `n_units ≥ 2`, `0 < share_treated < 1`, `noise_sd > 0` and the seven threat levels (`THREAT_LEVEL_FIELDS`) |
| 7.4 | `unsafe_allow_html=True` on the Theory page (parameter name + description). | — | Names are checked against `^[A-Za-z][A-Za-z0-9_]*$` before any model is built (probe: `<img src=x onerror=…>` → `err.game_bad_name`); descriptions come from the catalogue only | **No change**, documented |
| 7.5 | Fixed seeds as defaults (`seed=0` for the bootstraps, `42` for the Virtual World). | — | Intentional: results are reproducible, as the specs require ("Reproducibility via seed") | **No change** |
| 7.6 | No `.streamlit/config.toml`, so Streamlit's defaults apply: XSRF protection on, 200 MB upload limit, headless off. | Low | `ls .streamlit` → none | **No change.** Choosing an upload limit is a deployment decision nobody has documented, so it is listed as a remaining risk rather than invented |

## Tests

- **New:** `tests/test_config_safety.py` (3 tests).
  - The editor test runs in a subprocess with a 30 s timeout, so a regression fails instead of hanging the suite.
  - It also checks that an ordinary expression gives the same result as before.
- **Regression evidence:** the unguarded code was observed to hang on `9**9**9` (exit 124 under `timeout`, before the fix). The guarded code refuses it in under 1 ms.
- **Results:**
  - `pytest` (whole repository): **118 passed** (119.5 s);
  - `openspec validate --specs`: **27 passed**; change `2026-10-16-hw6-safe-configuration` validated `--strict` and archived.

## Remaining risks

- The 1000-digit bound limits the size of constants, not the cost of symbolic work. A very long expression, or a huge symbolic exponent such as `x**1000` in a utility, can still make the solver slow; it does not hang at parse time.
- Upload size and other server settings use Streamlit defaults (7.6). For a public deployment, these should be set deliberately.
