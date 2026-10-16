## Why

HW6 review 7 (configuration and unsafe defaults) found inputs that were accepted and then caused harm:

- the free model editor evaluated constants exactly while parsing, so `9**9**9` (369 million digits) blocked the Python process, and with it every session of the Streamlit server. The existing safe-parsing rules (whitelisted tokens) did not cover the size of numbers;
- the Virtual World generator silently clipped `share_treated` outside (0, 1), produced a world without a treated unit for `n_units = 1`, and crashed with raw numpy/KeyError messages on a negative noise or a misspelt threat level;
- the robust DiD treated any unknown `comparison` value as "not yet treated" while reporting the value it was given.

## What Changes

- Editor: constants are checked on an unevaluated parse tree and rejected above 1000 digits (`MAX_CONSTANT_DIGITS`, agent-chosen and documented in the code).
- `generate` validates `n_units`, `share_treated`, `noise_sd` and the seven threat levels.
- `estimate_staggered_did` validates `comparison` and `n_bootstrap`.

## Impact

- Code: `theory_engine/game.py`, `simulation_engine/dgp.py`, `estimators/staggered_did.py`, locales.
- Tests: new `test_config_safety.py`.
