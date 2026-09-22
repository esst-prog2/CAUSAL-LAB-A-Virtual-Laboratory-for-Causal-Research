## 1. Rewrite "The size" (section 3)

- [ ] 1.1 Move event study, cross-method recommendation, the 5-check "Break My Design" battery, code generation (Python/R/Stata), and the EN/FR interface out of "Not this term" and into the delivered-scope list, phrased from `openspec/specs/event-study-estimation`, `method-recommendation`, `break-my-design-stress-test`, `code-generation`, and `internationalization`'s Purpose sections. Verify by re-reading the updated section against each spec's Purpose for accuracy.
- [ ] 1.2 Leave IV, RDD, matching, synthetic control, RCT, DML, report export, external data connectors, and project persistence under "Not this term" (none of these are implemented — confirmed by `openspec list --specs` having no corresponding capability). Verify no capability in `openspec/specs/` covers any of these.

## 2. Update acceptance criteria (section 4)

- [ ] 2.1 Add one acceptance criterion per newly-documented capability (event study, recommendation, stress test, code generation, i18n), each grounded in an actual requirement/scenario from its spec file rather than invented. Verify each new bullet traces to a specific requirement in `openspec/specs/<capability>/spec.md`.
- [ ] 2.2 Keep the existing three acceptance criteria (DiD coefficient recovery, missing-column error, parallel-trends violation detection) unchanged, except updating the missing-column criterion if `validate-upload-columns` has been applied by the time this change is written. Verify by checking `openspec list` for that change's status before editing.

## 3. Revisit "Scope creep" (section 5)

- [ ] 3.1 Reword the scope-creep paragraph to state, in the past tense, that this drift happened and has now been reconciled by this change, rather than leaving it phrased as a hypothetical future risk. Verify by reading the final paragraph: it should not claim the tripwire is still untripped.
- [ ] 3.2 Keep the paragraph's other two risk items (statistical correctness under review, real data availability) unchanged — they are unrelated to this change.

## 4. Close the loop

- [ ] 4.1 Re-read the full rewritten `README.md` top to bottom and verify sections 1-2 (demo, shape) still accurately describe the app given the expanded section 3 (no internal contradictions, e.g. the demo/shape sections should not still describe a DiD-only tool).
- [ ] 4.2 Archive this change (`openspec archive document-delivered-mvp-scope`) once the README is updated, and verify `openspec validate --specs` still passes (no spec files change, so this should be a no-op on specs).
