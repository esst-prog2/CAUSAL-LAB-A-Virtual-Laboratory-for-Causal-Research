# HW6 review 8 — Repository hygiene and data safety

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 7 (`c115d61`)
- **Criteria** (from the user's instructions): no secrets, credentials, private datasets or personal information in the working tree **or in the history**; nothing sensitive that could be committed by accident; datasets with documented provenance; no history rewrite without the user's approval, and any discovered secret never reproduced.

## Scope and method

- **Secret scan over the full history** (37 commits, all refs), applied to the added lines of every commit (`git log -p --all`). Patterns:
  - AWS keys;
  - GitHub tokens (`ghp_`, `github_pat_`);
  - OpenAI and Anthropic keys;
  - Slack tokens;
  - Google API keys;
  - PEM private keys;
  - assignments to password / secret / api_key / token.

  Only match counts were printed, never values. A positive control (two planted fake strings piped through the same `grep`) matched 2 of 2, so the zero counts are meaningful.
- **Personal data:**
  - e-mail addresses in added lines (only their domain was printed);
  - the field names of the only dataset's codebook.
- **Files:**
  - every path ever added, matched against sensitive-looking names (`.env`, `secret`, `credential`, `token`, `.key`, `.pem`, `.csv`, `.xlsx`, `.dta`, `.sav`, `.parquet`, `.pkl`, `.db`, `id_rsa`);
  - the 8 largest blobs ever stored;
  - `git status --ignored`;
  - the tracked `.claude/` folder.
- **Data flow in the app:** every file write, download and network call (`to_csv`, `open(`, `write_*`, `download_button`, `requests`, `urllib`, `http`).
- **Branch safety:** `main` and `hw5-usable` compared with their remote refs after a `git fetch`.

## Findings

| # | Finding | Severity | Evidence | Action |
|---|---|---|---|---|
| 8.1 | **No secret in the working tree or the history.** | — | 0 matches for each of the 9 patterns over 37 commits; positive control 2/2 | **None needed.** No history rewrite is warranted, so none was proposed |
| 8.2 | **No personal information.** The only "e-mail" matches are `@AGENTS.md` and `@st.cache` (code). The dataset is store-level: chain, state, employment, wages, prices, interview type; it has no name, address or phone field. | — | e-mail scan; `grep -i "name\|address\|phone\|owner" codebook` → only column headers, "# managers", "1=phone" interview type | **None needed** |
| 8.3 | **One dataset, public and documented.** Card & Krueger (1994) is copied unchanged from David Card's public replication archive (URL and download date in `SOURCE.md`); it is the largest blob ever stored (82 kB). No other data file was ever added. | — | sensitive-name scan: none; largest blobs: `public.dat`, then `fr.json` versions | **None needed** |
| 8.4 | **`.gitignore` did not protect local secrets.** It listed only `__pycache__/`, `*.pyc` and `.venv/`. A `.env`, a Streamlit `secrets.toml` (Streamlit reads it from `.streamlit/` in the directory the app is started from, here `causal_lab/`) or a Claude Code `settings.local.json` would have been committed by `git add -A`. | Medium (preventive) | `git check-ignore` on those paths → not ignored | **Fixed.** Added `**/.env`, `**/.streamlit/secrets.toml`, `.claude/settings.local.json` and `.pytest_cache/`. Verified with `git check-ignore` at the root and under `causal_lab/`; `git ls-files -ci --exclude-standard` shows that no tracked file is now ignored |
| 8.5 | Uploaded data never leave the visitor's session: kept in `st.session_state`, never written to disk, no network call anywhere in the app. Downloads (data CSV, generated scripts) are started by the user. | — | write/network scan: only `i18n.py` reads the locale files, and four `st.download_button` calls | **None needed** |
| 8.6 | **`main` and `hw5-usable` untouched.** `main` = `origin/main` = `5eb32b6`; `hw5-usable` = `origin/hw5-usable` = `679760c`. All HW6 work is in 8 commits on `hw6-review`. | — | `git branch -a -vv`, `git rev-parse` | **None needed** |
| 8.7 | No `.gitattributes`. With `core.autocrlf=true`, Git warns "LF will be replaced by CRLF" on files written with LF. The files are normalized correctly; the warnings are noise. | Low | commit output of every review | **No change.** Adding `* text=auto` would renormalize line endings across the repository in one large unrelated diff, which this review did not want to impose |

## Tests

- `git check-ignore` on 7 paths: the 5 secret or local paths are ignored; the tracked code and data files are not.
- Positive control for the secret scan: 2 of 2 planted fake strings matched.
- The `.gitignore` change touches no code, so the test suite is re-run in the final verification.

## Remaining risks

- A regular-expression scan finds known secret formats only. A secret in an unusual format, or one split across lines, would not be detected.
- The ignore rules prevent accidental commits; they do not stop a deliberate `git add -f`.
