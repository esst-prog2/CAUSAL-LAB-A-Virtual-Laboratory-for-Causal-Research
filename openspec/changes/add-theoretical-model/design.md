## Context

The app is a single Streamlit script plus pure-Python engines. Pages added by the previous change live in `causal_lab/ui/`, and estimators return dataclasses. There is no symbolic-math dependency yet. Tests are plain functions run with `python tests/test_x.py`. See proposal.md for motivation and specs/ for the behavior contract.

## Goals / Non-Goals

**Goals:**
- One engine (`theory_engine/game.py`) serves both catalogue and custom models, so the editor is not a second-class path.
- No equilibrium is ever shown without a unilateral-deviation check.

**Non-Goals:**
- Mixed-strategy equilibria, sequential/extensive-form games (Stackelberg, bargaining), dynamic games, and estimating structural parameters by maximum likelihood or GMM. Calibration here is moment matching through explicit parameter sources.
- Multidimensional strategies: each agent has one scalar strategy.
- Simulating datasets from a model. The model consumes data; it does not generate it.

## Decisions

**Symbolic layer: sympy.**
- Utilities are sympy expressions. FOCs are `diff(U_i, s_i)`, shown with `sympy.latex`.
- A best response is attempted with `sympy.solve(FOC, s_i)` only when the FOC's numerator (after `together`) is a polynomial in `s_i` of degree ≤ 3. Otherwise `solve` can run for minutes; in that case the page says the best response is computed numerically.
- Rejected alternative: hand-writing FOCs per catalogue model. That would not work for the editor, and errors would creep in.

**Safe editor parsing.**
- A tokenizer whitelist runs before any parsing. Identifiers must be declared parameters, strategy names, or one of `log, exp, sqrt, Abs, Min, Max`. `__`, `.` outside numeric literals, `[`, `]`, quotes, `lambda`, `;` and `:` are rejected.
- Only then is `sympy.parse_expr` called, with `local_dict` holding the declared symbols and functions, a minimal `global_dict` (`Integer`, `Float`, `Rational`, `Symbol`) and `convert_xor`, so `^` means a power.
- Rejected alternative: bare `sympify`, which calls `eval` on arbitrary input.

**Solution method per model.**
- Each model has a `smooth` flag and an optional `closed_form` (strategy → expression in the parameters).
- Non-smooth models (Downs, Niskanen) use the closed form, which is still passed through the deviation check.
- Smooth models are solved numerically. Their closed form, when present, is shown and checked in the tests, not trusted at runtime. This keeps one code path for catalogue and editor models.

**Numerical solver.**
- `sympy.lambdify` turns each utility into a numpy function of the strategy vector. Parameters are substituted first, and NaN/inf values are mapped to −inf.
- Best response: a 64-point grid over [lo, hi], then `scipy.optimize.minimize_scalar(method="bounded")` refined within the best grid cell. The grid search makes corners and non-concave payoffs safe.
- Iteration: Gauss–Seidel best-response updates for up to 200 rounds, then damped Jacobi updates (λ = 0.5) for up to 300 more.
- Starting points: the box midpoint plus 7 seeded uniform draws. Results within 1e-4·(range) of each other are merged.
- Verification: for each agent, a 400-point grid plus a bounded refinement around the best point. The profile is accepted if the best deviation gain is ≤ 1e-6·(1 + |U_i|).

**Comparative statics.** Central finite difference with h = 1e-4·max(1, |θ|), re-solving from the current equilibrium as a single start. This follows the same branch when there are several equilibria, works identically for closed-form and numeric models, and avoids differentiating a Piecewise expression.

**Catalogue specifications** (the closed forms are used in the tests):
- **Downs.** Vote share of A is `(1 + sign(|xB − m| − |xA − m|))/2`. Equilibrium: xA = xB = m.
- **Probabilistic voting** (Lindbeck–Weibull, uniform shocks). Vote share of A is `1/2 + Σ_g n_g φ_g[(xB − b_g)² − (xA − b_g)²]/N`. Equilibrium: x = Σ n_g φ_g b_g / Σ n_g φ_g.
- **Tullock contest** (r = 1). U_i = V_i x_i/Σx − x_i. Symmetric: x* = (n−1)V/n². With n = 2: x1 = V1²V2/(V1+V2)².
- **Niskanen.** B(Q) = aQ − bQ²/2 and C(Q) = cQ + dQ²/2. The bureau maximizes B subject to B ≥ C: Q_B = min(a/b, 2(a−c)/(b+d)). The sponsor optimum is Q* = (a−c)/(b+d).
- **Public good.** U_i = α log(w_i − g_i) + (1−α) log(Σg), with g_i ∈ [0, w_i]. Symmetric interior: g = w(1−α)/((1−α) + αn).
- **Cournot.** P = a − bQ. Interior: q_i = (a − (n+1)c_i + Σc_j)/((n+1)b).
- **Bertrand, differentiated.** q_i = a − b p_i + d p_j. p1 = (2b(a + b c1) + d(a + b c2))/(4b² − d²).

**Calibration.**
- `ParameterSource(kind, value | stat, column, filter_column, filter_value | y, x, coef)` is evaluated on a DataFrame subset.
- `detect_structure(df, unit_col, period_col)` implements the spec's classification.
- `solve_by_scope` loops over the units of computation, warm-starting each solve from the previous unit's equilibrium, so a per-period path stays on one branch.

**Predictions.**
- Δ comes from manual input, or from the parameter's source evaluated on treated rows minus control rows.
- The prediction re-solves at θ + Δ and reports the exact difference; the marginal derivative is reported too.
- The verdict rules follow the spec.
- Causal estimates are read from `st.session_state.method_data[*]["result"]` (`MethodResult`).

**Page.** `ui/theory_page.py` with `st.tabs` for the three steps. State is kept in `st.session_state.theory`. The editor uses plain text inputs, which `AppTest` can drive, rather than `st.data_editor`.

## Risks / Trade-offs

- [Best-response iteration may cycle (e.g., some Bertrand/Cournot variants with many firms)] → Damped Jacobi fallback and multi-start. If nothing verifies, the page says so instead of guessing.
- [Grid-based verification can miss a narrow profitable deviation] → It combines a 400-point grid with a bounded local refinement. The tolerance is relative. This is documented as a numerical check, not a proof.
- [Multiple equilibria make comparative statics ambiguous] → Warm-starting keeps the branch. All equilibria found are listed, and predictions use the one the researcher selects.
- [Calibration by moments is crude compared with structural estimation] → Stated as a non-goal. Every calibrated value is shown next to its source, so the researcher can judge it.
- [sympy is a new dependency (~6 MB, pure Python)] → Widely used, with no compiled parts.
