# Card & Krueger (1994) — New Jersey / Pennsylvania fast-food data

Real-world data used by `tests/test_card_krueger.py` and for the hw5 "use it for real" run.

- **Study.** David Card and Alan B. Krueger (1994), "Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania", *American Economic Review* 84(4), 772–793.
- **Files.** David Card's public replication archive, `njmin.zip`, downloaded on 2026-10-09 from https://davidcard.berkeley.edu/data_sets/njmin.zip. The files are copied unchanged:
  - `public.dat`: 410 stores, fixed-width;
  - `read.me`;
  - `check.sas`: the authors' SAS program.
- **Codebook.** `codebook` is the original file converted from code page 437 to UTF-8 so it displays correctly.
- **Design.** New Jersey raised its minimum wage from $4.25 to $5.05 on 1 April 1992. Pennsylvania (`STATE = 0`) did not, and serves as the comparison group. Wave 1 was surveyed in February–March 1992, wave 2 in November–December 1992.
- **Outcome.** Full-time-equivalent employment, exactly as in `check.sas`: `EMPTOT = EMPPT*.5 + EMPFT + NMGRS` for each wave.
- **Published result** (Table 3): mean FTE per store was New Jersey 20.44 → 21.03 and Pennsylvania 23.33 → 21.17, a difference-in-differences of **+2.76** (SE 1.36).
