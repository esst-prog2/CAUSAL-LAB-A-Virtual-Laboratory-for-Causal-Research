## 1. Find

- [x] 1.1 Browser crawl (EN, FR): console errors, exceptions, requests to other hosts, cut labels.
- [x] 1.2 Fuzz the CSV upload (19 panels), Causal Methods (6 methods × odd mappings, tiny file), Theoretical Model uploads and project files.
- [x] 1.3 Audit state shared between sessions: caches, globals, files written, credentials.

## 2. Fix

- [x] 2.1 Leave out incomplete rows at upload, with a count.
- [x] 2.2 IV minimum rows; RCT balance N/A on too few rows; empty mapped columns refused; translated message for unexpected errors.
- [x] 2.3 Validate panels when a project is opened; bound the caches; stop rebinding `style`; wrap button labels.

## 3. Verify

- [x] 3.1 One regression test per finding; 6 of 6 mutants caught; full suite and a rerun of the fuzzers.
