# Planning Log

Running log of decisions, scope changes, and next steps for Causal Lab. Newest entry on top.

---

## 2026-09-22

**Synced repo.** Local and GitHub had diverged: GitHub had a README edit (`84ec95b`), local had a commit restoring the `causal_lab/` directory (`cdb8521`) after it was accidentally deleted in `d3e94f6`. Merged the two (merge commit `8590748`), no conflicts, pushed to `origin/main`. Repo is back in sync.

**Noted scope drift.** `causal_lab/` already contains an `event_study.py` estimator, a `code_generator/`, a `robustness_engine/`, and `locales/en.json` + `fr.json` — all items the README's "Not this term" list (section 3) explicitly excludes from v1 (event study, code generation, general stress-test suite, bilingual interface). Worth deciding whether these are early scaffolding to keep or should be trimmed/flagged until their turn.

**Started this log.** Kept at the repo root so planning history travels with the code instead of living only in chat.

**Next:**
- Decide: keep the out-of-scope modules as untested scaffolding, or strip them until the README says it's their term.
- Confirm the "First useful version does" checklist in README section 3 against what actually runs today (upload → plot → parallel-trends check → DiD estimate → synthetic comparison).
