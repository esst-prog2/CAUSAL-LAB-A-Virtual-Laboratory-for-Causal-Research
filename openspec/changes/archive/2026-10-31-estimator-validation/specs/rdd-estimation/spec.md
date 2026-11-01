## ADDED Requirements

### Requirement: Robust inference by default
The Causal Methods page SHALL report robust bias-corrected inference (Calonico et al., 2014) for regression discontinuity unless the researcher chooses conventional inference.

#### Scenario: Running RDD with default settings
- **WHEN** the researcher runs RDD without changing the inference choice
- **THEN** the reported confidence interval and p-value are the robust bias-corrected ones
