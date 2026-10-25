# method-code-generation Specification

## Purpose
TBD - created by archiving change methods-monte-carlo-stress-code. Update Purpose after archive.

## Requirements

### Requirement: Code for the six Causal Methods
For a Causal Methods estimate, the system SHALL show Python, R and Stata scripts that reproduce it with the method's column mapping and options, each downloadable, together with the data as CSV. The scripts SHALL use the reference packages the estimators are tested against:
- RCT: statsmodels HC2, estimatr, regress;
- Matching: an explicit Abadie-Imbens implementation, Matching, teffects nnmatch;
- IV: linearmodels, estimatr, ivregress;
- RDD: rdrobust in all three languages, with the bandwidth of the estimate shown;
- Synthetic control: pysyncon, Synth, synth;
- DML: DoubleML in Python and R, ddml in Stata.

Each script's header SHALL state its measured agreement with Causal Lab:
- exact;
- RDD standard error within 0.01%;
- synthetic control estimate within 0.01% (Python) or 0.1% (R Synth);
- R DML can differ by about one standard error;
- Stata not checked.

The option values in the scripts SHALL be plain numbers and strings, never NumPy reprs.

#### Scenario: Running the Python scripts
- **WHEN** the generated Python script runs on the method's data
- **THEN** it prints Causal Lab's estimate and standard error: to 1e-9 relative for RCT, Matching, IV and DML, with the RDD standard error to 1e-4 and the synthetic control estimate to 1e-4

#### Scenario: Stata synthetic control
- **WHEN** the Stata synthetic control script is generated
- **THEN** it lists every pre-treatment outcome lag and gives the treated unit's code after `encode`
