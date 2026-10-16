## MODIFIED Requirements

### Requirement: Estimation-page tab
The system SHALL show a "Robust DiD (Callaway & Sant'Anna)" tab on the Estimation page with:
- the robust ATT, its bootstrap SE and CI;
- a table comparing TWFE, Callaway & Sant'Anna and, for Virtual Worlds, the true ATT;
- the robust event study plot.

The robust estimator SHALL use only units observed in every period, as the R package `did` does by default (`allow_unbalanced_panel = FALSE`), and SHALL report how many units it left out.

#### Scenario: Staggered dataset
- **WHEN** the active dataset has staggered timing
- **THEN** the DiD tab's warning points to the robust tab, and the robust tab shows the three-way comparison

#### Scenario: Unbalanced panel
- **WHEN** some unit lacks an outcome in some period
- **THEN** that unit is left out, the estimate equals the one on the panel balanced beforehand, and the tab states how many units were left out

#### Scenario: No complete unit
- **WHEN** no unit is observed in every period
- **THEN** the tab shows an error instead of crashing
