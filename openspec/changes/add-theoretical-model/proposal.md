## Why

CAUSAL LAB estimates causal effects but never says what effect theory predicts. In public choice and applied micro, a causal estimate is usually read against a structural model of interacting agents: voters and parties, lobbies competing for a rent, a bureau facing its sponsor, contributors to a public good, firms in a market. Without such a model, the app cannot answer the question that comes after "what is the effect?", which is "is this the effect the theory predicts, given these data?". The user decided on 2026-10-06 (PLANNING_LOG) to add this as a "Theoretical Model" option.

## What Changes

- **Model definition.** A model consists of agents, each with a strategy variable, a bounded strategy space and a utility (payoff) function of everyone's strategies and of named parameters. Models come from a catalogue or are written in a free editor:
  - Public choice: Downsian median voter, probabilistic voting, Tullock rent-seeking contest, Niskanen bureaucracy, voluntary public-good provision.
  - Classic interactions: Cournot oligopoly and differentiated Bertrand.
  - Free editor: the user declares N agents, parameters and utility expressions.
- **Equations.** The app shows each agent's utility, first-order condition and, when it can be derived symbolically, the best-response function, rendered as equations.
- **Equilibrium.** The app solves for the pure-strategy Nash equilibrium. It uses the catalogue closed form when one exists. Otherwise it solves numerically by multi-start best-response iteration, verifies that no agent has a profitable unilateral deviation, and reports every distinct equilibrium found, or that none was found.
- **Calibration to data.** Each parameter is set by hand, or computed from the loaded dataset as a column statistic (optionally on a filtered subgroup) or as a regression coefficient. The app detects the dataset's structure (cross-section, panel, repeated cross-section, time series) and solves one equilibrium per unit of computation that structure allows: pooled, per group, or per period. This gives an equilibrium table and an equilibrium path.
- **Predictions.** Comparative statics: the derivative of every equilibrium strategy and outcome with respect to every parameter. A treatment is modelled as a shift Δ of one parameter; the shift is entered by hand or measured as a treated-minus-control difference in the data. The predicted effect is the re-solved equilibrium change. It is compared with a causal estimate (from the Causal Methods page, or entered by hand) and given a verdict: consistent, magnitude differs, or sign contradicts.
- **Page.** A new "Theoretical Model" sidebar page, in English and French.
- **Dependency.** New dependency: `sympy`.

## Capabilities

### New Capabilities
- `theoretical-model`: defining agents, strategies, parameters and utilities, through the catalogue or the free editor (with safe expression parsing), and deriving first-order conditions and best responses.
- `equilibrium-solver`: computing, verifying and reporting pure-strategy Nash equilibria, and comparative statics.
- `theory-data-calibration`: setting model parameters from data, detecting the data structure, and solving one equilibrium per group or period.
- `theory-predictions`: treatment-as-parameter-shift predictions and their comparison with causal estimates.
- `theory-lab-page`: the page that ties these together.

### Modified Capabilities
(none — no existing requirement changes; the Causal Methods results are only read.)

## Impact

- New package `causal_lab/theory_engine/` (`game.py`, `catalogue.py`, `calibration.py`, `predictions.py`) and new page module `causal_lab/ui/theory_page.py`.
- `causal_lab/app.py`: one new sidebar entry. `causal_lab/locales/{en,fr}.json`: new keys.
- `causal_lab/requirements.txt`: adds `sympy`.
- New tests in `causal_lab/tests/`.
- README.md section 3: the feature is added under "Delivered".
