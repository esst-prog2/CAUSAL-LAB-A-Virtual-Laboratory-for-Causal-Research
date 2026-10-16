## Why

Run without an argument, `spike/stress_test_calibration.py` wrote to `stress_test_calibration_results.md`, the historical hw4 spike record, and replaced it. This happened during the hw6 final verification; the file was restored from Git. Any explicit name was also replaced silently, and an invalid destination was only discovered after the 5-minute simulation.

## What Changes

- The output path is a required argument; replacing an existing file requires `--overwrite`.
- The destination is checked before the simulation; the write uses exclusive creation, so a file created during the run is not replaced.
- A write failure exits with an error and no success message.
- The calibration itself (worlds, seeds, threats, score, rates) is unchanged.

## Impact

- `spike/stress_test_calibration.py`; new `causal_lab/tests/test_calibration_output.py`; README.
