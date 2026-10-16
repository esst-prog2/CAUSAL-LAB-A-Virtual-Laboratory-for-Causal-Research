## ADDED Requirements

### Requirement: Calibration results are never overwritten silently
The calibration spike SHALL write its table only to an output file named explicitly on the command line. It SHALL check the destination before starting the simulation, SHALL refuse an existing file unless `--overwrite` is given, and SHALL report a failed write as an error with a non-zero exit status. The committed result files of 2026-10-03 and 2026-10-06 are historical records.

#### Scenario: No output argument
- **WHEN** `spike/stress_test_calibration.py` is run without an output argument
- **THEN** it exits with an error before simulating anything, and no file is modified

#### Scenario: Existing output file
- **WHEN** it is run with the name of an existing file and without `--overwrite`
- **THEN** it exits with an error before simulating anything, and the file is left byte-for-byte unchanged

#### Scenario: New output file
- **WHEN** it is run with a path that does not exist yet, in an existing folder
- **THEN** it runs the calibration unchanged and writes the table to that path

#### Scenario: Write failure
- **WHEN** the table cannot be written
- **THEN** it exits with an error stating that the results were not saved, and does not report success
