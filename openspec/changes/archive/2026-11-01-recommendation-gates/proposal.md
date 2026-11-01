## Why

On 2026-11-01 the user set a method-selection discipline for the Method Recommendation Engine:
- recommend the most credible and feasible causal design, never a default;
- a policy or a panel does not imply DiD;
- RDD only with a real cutoff, IV only with a credible instrument, synthetic control only with a suitable treated unit, donor pool and pre-treatment fit;
- say so when no credible design is supported, and ask for missing information;
- answer in a fixed format: method, why it fits, identification, assumptions, threats and diagnostics, alternatives, details needed.

Run over all 1,620 wizard designs, the old engine broke this discipline:
- It ranked IV first for 462 designs, although the wizard never asks for an instrument. The IV "instrument availability" component was fixed at 30.
- It ranked synthetic control first for 354 designs, with a fixed "few treated units" score of 85 that it never checked.
- With a declared assignment cutoff, it recommended an event study or synthetic control over RDD for 135 designs.
- It had no "no credible design" outcome.

## What Changes

- **Gates.** Each of eight methods (RCT, RDD, DiD, event study, synthetic control, IV, interrupted time series, matching or regression adjustment) is first checked against its necessary conditions. Each method ends up "supported", "needs information", or "ruled out", with the reasons. ITS is new.
- **Scoring.** Only supported methods are scored. The score is the mean of three components:
  - design credibility (randomisation > cutoff > comparison over time > instrument > time series > selection on observables);
  - assumption plausibility under the diagnosed threats;
  - data adequacy.
- **No credible design.** When no method is supported, the page and the report say so explicitly, and list what would make a method credible.
- **New wizard step,** "What could identify the effect", with four questions:
  - whether untreated comparison units are observed;
  - the number of treated units (one, a few, many);
  - whether a defensible instrument exists (yes, no, not sure);
  - whether all important confounders are measured (yes, no, not sure).
  
  "Not sure" turns the method into "needs information", with the question to answer.
- **Structured answer.** The Recommendation page and the report give:
  - the recommended method;
  - the causal estimand (ATE, ATT, LATE, local at the cutoff, effect on the treated unit);
  - why it fits;
  - the identification strategy;
  - the key assumptions;
  - the threats and diagnostics;
  - the alternatives, with when each is preferable;
  - the details still needed.
  
  Ruled-out methods are listed with their reasons.
- **Notes** cover staggered adoption (Callaway & Sant'Anna), a single treated unit, a continuous treatment, and spillovers (the no-interference assumption).

Across the grid of designs, each method is recommended where its design holds. A random assignment always gives RCT, and a cutoff always gives RDD. When no condition is met, the result is "no credible design".

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `method-recommendation`: gates, three-component scores, no-credible-design outcome, structured answer.
- `research-design-wizard`: the identification questions.

## Impact

- **Code:** `causal_engine/recommendation.py` (rewritten), `causal_engine/diagnosis.py` (four fields), `app.py` (wizard step 6 and the Recommendation page), `report_engine/builder.py`, and the EN and FR texts.
- **Project files:** older files open unchanged, with the new fields at their defaults.
- **Tests:** `test_recommendation.py` is rewritten as one rule per test, including a grid check. The i18n test now covers the new key families. `test_app_flows.py` gains the no-credible-design page.
