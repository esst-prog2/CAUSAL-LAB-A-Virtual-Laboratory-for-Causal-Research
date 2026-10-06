# equilibrium-solver Specification

## Purpose
Computes the pure-strategy Nash equilibria of a model for given parameter values, verifies them, and measures how they respond to each parameter (comparative statics).

## Requirements

### Requirement: Closed-form equilibrium when available
The system SHALL evaluate a model's closed-form equilibrium when the model provides one. For models whose payoffs are not smooth (Downsian median voter, Niskanen bureaucracy), the closed form SHALL be the solution method.

#### Scenario: Median voter
- **WHEN** the Downsian model is solved with median ideal point m
- **THEN** both parties' equilibrium platforms equal m

### Requirement: Numerical Nash equilibrium with verification
For models solved numerically, the system SHALL run best-response iteration from several starting points within the strategy bounds. Each agent's best response SHALL be its bounded utility maximum given the others' strategies. The system SHALL keep only the profiles at which no agent can raise its utility by more than a relative tolerance by deviating unilaterally anywhere in its strategy space. It SHALL report each distinct verified equilibrium, with strategies, utilities, outcomes and the method used.

#### Scenario: Interior equilibrium matches the closed form
- **WHEN** the symmetric 2-player Tullock contest with prize V is solved numerically
- **THEN** each effort equals V/4 within 1e-4 relative error

#### Scenario: Corner solution
- **WHEN** a public-good contributor's best response is to contribute nothing
- **THEN** the equilibrium reports a contribution equal to the lower bound 0, and verification still passes

#### Scenario: No equilibrium found
- **WHEN** no starting point converges to a verified profile
- **THEN** the solver reports that no pure-strategy equilibrium was found, instead of returning an unverified profile

### Requirement: Comparative statics
The system SHALL report, for a chosen parameter, the derivative of every equilibrium strategy and outcome with respect to that parameter. It SHALL compute it by central finite differences, re-solving the model from the current equilibrium so that it stays on the same equilibrium branch.

#### Scenario: Cournot cost increase
- **WHEN** comparative statics are computed for firm 1's marginal cost in the 2-firm Cournot model
- **THEN** firm 1's equilibrium quantity has a negative derivative and firm 2's a positive one
