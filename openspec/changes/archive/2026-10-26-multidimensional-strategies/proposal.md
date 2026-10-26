## Why

Multidimensional strategies were in README section 3's "Not this term" list. On 2026-10-26 the user asked for a broad project.

## What Changes

- `theory_engine/multidim.py`: `VectorGame`, `solve_vector_equilibrium` and `build_vector_game`. The scalar `Game` is unchanged because Stackelberg and calibration depend on it. The solver:
  - finds each best response on a grid over the agent's box, refined by L-BFGS-B with the exact gradient;
  - iterates best responses from several starts;
  - polishes the result with Newton on the KKT conditions;
  - reports a profile only if a deviation check over the whole box passes.
- `theory_engine/vector_catalogue.py`: three models, each with a closed form.
- `ui/multidim_page.py`: a new "Several strategy variables" kind on the Theory page, with catalogue and editor. The 2-D voting model gets a chart of ideal points and platforms.
- Messages in English and French.
- README fix: the report-export dependency note had drifted to the end of the last theory bullet, because each PR anchored its insertion at the end of the previous bullet. It is moved back to the report-export bullet.

## Capabilities

### New Capabilities
- `multidimensional-games`

### Modified Capabilities
(none)

## Impact

New `tests/test_multidim.py`:
- closed forms;
- sympy's exact solution of the first-order conditions;
- a KKT corner of a non-concave agent;
- a global best response with two peaks;
- the scalar Tullock contest;
- no pure equilibrium;
- editor errors;
- the page.

Mutation check: 5 of 5 mutants caught (polish, deviation check, gradient sign, grid mapping, corner closed form).
