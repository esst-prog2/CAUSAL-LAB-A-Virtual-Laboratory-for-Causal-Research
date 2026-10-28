## Why

On 2026-10-28 the user asked, before going online, to make the project "very academic" and to correct any errors.

The app already cited about 55 works, but:
- they were spread over code comments and interface texts;
- they appeared in four styles ("CCT 2014", "ADH 2010", "Calonico-Cattaneo-Titiunik 2014", "Downs (1957)");
- they were never listed in full and never checked;
- the exported report had no reference list and no reproducibility section.

An audit also found two kinds of error.
- **A wrong attribution:** the fixed-effects correction of the Durbin-Watson check was credited to the "Nickell bias". The −1/(T−1) correlation of within-demeaned errors is a different result (Wooldridge, 2010, ch. 10); Nickell (1981) concerns a lagged dependent variable.
- **Null results read as proof:** eleven PASS messages turned a non-significant test into a positive statement, such as "the instruments agree", "the instrument is strong enough", "no jump", or "do not change differently".

## What Changes

- **`utils/references.py`:** one bibliography of 65 entries in APA 7 style, with DOIs for journal articles.
  - It provides in-text citations (`cite`, with pinpoints such as "ch. 3") and the full reference list.
  - It maps each method, check and solver to its sources (`METHOD_REFERENCES`).
  - The theory catalogues now hold reference keys instead of free text.
- **`spike/check_references.py`:** compares every entry that has a DOI with Crossref. It found one wrong DOI, for Andreozzi (2004), now fixed. One documented exception remains: Skyrms, for the copyright year.
- **`docs/references.bib`:** generated from the bibliography; a test keeps it in sync.
- **App:** every estimator, check and solver page shows "References: …".
- **Report:**
  - a citation line under each method it ran;
  - a "Software and reproducibility" section, with the Python and package versions, the seeding and how to cite Causal Lab;
  - a "References" section listing the works it cited.
- **`utils/reproducibility.py` and `CITATION.cff`:** version, repository and the citation of the software.
- **Interface texts (EN, FR):**
  - in-text citations now follow APA 7;
  - eleven PASS messages are reworded as absence of evidence. The overidentification message now also says that the test cannot establish the validity of the instruments.
- **Corrections:** the Nickell attribution, the "MVP build" settings note, and APA punctuation (no period after a title ending in "?").

## Capabilities

### New Capabilities
- `academic-references`

### Modified Capabilities
- `method-stress-test`: non-rejections are reported as absence of evidence.

## Impact

New `tests/test_references.py` (8 tests; 3 of 3 mutants caught). No change to any estimate.
