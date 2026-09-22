# Planning Log

One line per decision about this project — a requirement, a number, a name, a tool. Newest entry on top. Lines are never rewritten; corrections get a new line.

---

- 2026-09-22: Uploaded CSVs will require exactly 5 fixed columns (unit, period, Y, D, treated_unit) with no column-mapping UI; missing columns must be named in an upload-time error instead of failing later — decided by: user
- 2026-09-22: Change `validate-upload-columns` scaffolded via `openspec new change` with proposal.md, a delta spec on real-world-data-upload, and tasks.md (design.md skipped: no cross-cutting/dependency/perf complexity applies); implementation not yet started — decided by: Claude
- 2026-09-22: openspec/specs/ populated with 12 capability spec files (research-design-wizard, causal-diagnosis, method-recommendation, virtual-world-generation, monte-carlo-evaluation, real-world-data-upload, did-estimation, event-study-estimation, break-my-design-stress-test, robustness-battery, code-generation, internationalization) reverse-engineered from the current causal_lab/ code, all passing `openspec validate --specs` — decided by: user
- 2026-09-22: OpenSpec CLI (`@fission-ai/openspec`) v1.13.0 installed globally via npm and initialized in this repo (`openspec/` + `.claude/` skills/commands for spec-driven change workflow), Node.js 24.19.0 LTS installed first via winget since it was missing — decided by: user
- 2026-09-22: Repo history reconciled by merging `origin/main` (GitHub README edit) into local `main` and pushing — decided by: user
- 2026-09-22: Project keeps a planning log; one line per decision (date, what, who), append-only, never rewritten — decided by: user
