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
- **Published result** (Table 3, p. 780, column (iii) "Difference, NJ − PA"; checked against the printed page on 2026-10-16):
  - row 3, all available observations: mean FTE per store New Jersey 20.44 → 21.03, Pennsylvania 23.33 → 21.17; difference-in-differences **+2.76 (SE 1.36)**;
  - row 4, balanced sample (stores with employment data in both waves): Pennsylvania −2.28 (1.25), New Jersey 0.47 (0.48); difference-in-differences **+2.75 (SE 1.34)**.

  The app's fixed-effects DiD uses only stores observed in both waves, so row 4 is its counterpart. On these files it reproduces row 4: n = 75 PA and 309 NJ stores, 2.7500. The SE is 1.3376 with the app's CR1 cluster-robust estimator, and 1.3423 with the paper's convention √(SE_NJ² + SE_PA²). Both print as 1.34. The paper's text (p. 778) gives 2.76 with t = 2.03 for row 3.
