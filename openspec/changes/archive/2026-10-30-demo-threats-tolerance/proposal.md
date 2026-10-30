## Why

Review issue #1 asked for a study of DiD that varies several threats, reports the distribution of the bias, and decides **how much bias is too much**.

The Guided Demo varied only diverging pre-trends, and it fixed no threshold. On 2026-10-30 the user fixed the threshold: |bias| ≤ 10% of the true effect and coverage ≥ 90%. The user also asked for three more threats.

## What Changes

- **More threats:** the study adds confounding, staggered adoption with effects that grow over time, and anticipation, each with 5 levels × 1,000 worlds. The seeds are the same as for diverging pre-trends, whose stored replications are reused unchanged.
- **The decision rule** is stated on the page, with when it was fixed: after the pre-trends results, before the three other threats were simulated. Each scenario is marked within or beyond the rule.
- **An overview** gives, for each threat, the level up to which the DiD is acceptable and what happens at the first level beyond.
- **One tab per threat:** the exact description of the threat, its table, its coverage and detection figure, and the distribution of the bias with the tolerance band. The reading text compares the pre-trend detection rate with its rate without any threat.
- **The live re-run** works for any threat and level.
- **README section 1** gives the answers per threat.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `guided-demo`: four threats, the decision rule, the bias distribution.

## Impact

- The stored study grows to 20,000 worlds. The three new threats ran in parallel, about 25 minutes in total.
- Tests: the decision rule checked by hand, every threat recomputed from its seeds, and the answers per threat that README section 1 states.
