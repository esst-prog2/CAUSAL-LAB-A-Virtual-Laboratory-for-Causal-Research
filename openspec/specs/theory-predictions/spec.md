# theory-predictions Specification

## Purpose
Turns the theoretical model into a testable prediction for a treatment, and confronts it with a causal estimate produced elsewhere in the app.

## Requirements

### Requirement: Treatment as a parameter shift
The system SHALL let the researcher model a treatment as a shift Δ of one parameter. Δ is either entered by hand or measured from the data, as the difference between the parameter's calibrated value on treated rows and on control rows (as defined by a treatment column). The predicted effect on each equilibrium strategy and outcome SHALL be the difference between the equilibrium re-solved at the shifted parameter value and the baseline equilibrium.

#### Scenario: Predicted effect of a larger prize
- **WHEN** the treatment raises the prize V of the symmetric 2-player Tullock contest by Δ
- **THEN** the predicted effect on total effort is Δ/2

### Requirement: Comparison with a causal estimate
The system SHALL compare a chosen predicted effect with a causal estimate and its 95% confidence interval. The estimate SHALL come either from a result already computed on the Causal Methods page or from values entered by hand. The verdict SHALL be:
- "consistent" when the prediction lies inside the confidence interval;
- "sign contradicts" when the interval excludes zero and lies on the opposite side of zero from the prediction;
- otherwise "magnitude differs".

The comparison SHALL remind the researcher that prediction and estimate must refer to the same outcome in the same units.

#### Scenario: Prediction inside the interval
- **WHEN** the predicted effect is 0.9 and the causal estimate's 95% CI is [0.7, 1.2]
- **THEN** the verdict is "consistent"

#### Scenario: Opposite sign
- **WHEN** the predicted effect is +0.5 and the 95% CI is [-0.9, -0.2]
- **THEN** the verdict is "sign contradicts"
