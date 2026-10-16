## MODIFIED Requirements

### Requirement: Comparison with a causal estimate
The system SHALL compare a chosen predicted effect with a causal estimate and its 95% confidence interval. The estimate SHALL come either from a result already computed on the Causal Methods page or from values entered by hand. The verdict SHALL be:
- "consistent" when the prediction lies inside the confidence interval;
- "sign contradicts" when the interval excludes zero and lies on the opposite side of zero from the prediction;
- otherwise "magnitude differs".

The estimate SHALL lie inside its own interval (lower ≤ estimate ≤ upper). Otherwise the comparison SHALL be refused with an error, and the bounds SHALL NOT be silently swapped. The comparison SHALL remind the researcher that prediction and estimate must refer to the same outcome in the same units.

#### Scenario: Prediction inside the interval
- **WHEN** the predicted effect is 0.9 and the causal estimate's 95% CI is [0.7, 1.2]
- **THEN** the verdict is "consistent"

#### Scenario: Opposite sign
- **WHEN** the predicted effect is +0.5 and the 95% CI is [-0.9, -0.2]
- **THEN** the verdict is "sign contradicts"

#### Scenario: Inconsistent estimate and interval
- **WHEN** the entered interval is reversed (lower > upper), or the estimate lies outside it
- **THEN** no verdict is given, and the page shows an error asking to check the values entered
