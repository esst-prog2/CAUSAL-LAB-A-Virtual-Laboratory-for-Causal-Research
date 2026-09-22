## Why

The top-level `README.md`'s "The size" section (v0.1 scope) explicitly excludes event study, cross-method recommendation, a general "Break My Design" stress-test suite, code generation, and a bilingual interface — but `causal_lab/` already implements all five, confirmed by the `openspec/specs/` capability audit (`event-study-estimation`, `method-recommendation`, `break-my-design-stress-test`, `code-generation`, `internationalization`). The README's own section 5 names exactly this situation as its scope-creep tripwire: *"If I find myself building anything from the 'not this term' list before the four items above work reliably, that's the signal I've drifted."* The drift already happened. Leaving the README stale misrepresents what's actually delivered.

## What Changes

- Rewrite `README.md` section 3 ("The size") to describe the scope actually delivered: move event study, cross-method recommendation, the 5-check stress-test battery, code generation (Python/R/Stata), and the EN/FR interface from "Not this term" into the delivered-scope list. Keep genuinely unbuilt items (IV, RDD, matching, synthetic control, RCT, DML, report export, external data connectors, project persistence) under "Not this term."
- Add acceptance criteria to section 4 ("How we would know it works") for each newly-documented capability, grounded in the already-written specs (`openspec/specs/event-study-estimation`, `method-recommendation`, `break-my-design-stress-test`, `code-generation`, `internationalization`).
- Revisit section 5's "Scope creep" paragraph so it honestly reflects that the drift occurred and has now been reconciled, rather than continuing to describe an already-true situation as a hypothetical risk.
- No **BREAKING** changes — this is documentation only.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
(none — no system behavior changes; `openspec/specs/` already documents the true behavior of these capabilities. This change brings the project's human-readable pitch document into agreement with them.)

## Impact

- `README.md` only (sections 3, 4, and 5).
- No changes to `causal_lab/` code or to `openspec/specs/`.
