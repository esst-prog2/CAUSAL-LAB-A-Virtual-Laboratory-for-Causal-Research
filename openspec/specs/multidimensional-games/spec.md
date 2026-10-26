# multidimensional-games Specification

## Purpose
TBD - created by archiving change multidimensional-strategies. Update Purpose after archive.

## Requirements

### Requirement: Vector strategies
The system SHALL solve games in which each agent chooses 1 to 4 variables in a box. These games come from:
- a catalogue: probabilistic voting on two issues, multimarket Cournot with a joint cost, and a contest over two prizes;
- a free editor that uses the same safe expression parser as the scalar editor.

The system SHALL report a profile only if no agent gains more than 1e-6 (relative) by deviating anywhere in its box. Equilibria located from different starts SHALL be listed once each.

#### Scenario: Closed forms
- **WHEN** a catalogue model is solved, including a parameter set where firms leave a market (corner equilibrium)
- **THEN** every variable equals the model's closed form to 1e-7 relative

#### Scenario: Asymmetric game
- **WHEN** an asymmetric two-firm, two-market game with concave profits is written in the editor
- **THEN** the equilibrium equals sympy's exact solution of the first-order conditions to 1e-9 relative

#### Scenario: Non-concave agent
- **WHEN** an agent's utility is not concave, so that the interior solution of the first-order conditions is a saddle point
- **THEN** the reported equilibrium is the Karush-Kuhn-Tucker corner where that agent's best response lies, not the saddle point

#### Scenario: Global best response
- **WHEN** an agent's utility has a broad local peak and a narrow, higher one
- **THEN** the best response is the higher peak

#### Scenario: No pure equilibrium
- **WHEN** the game has no pure-strategy equilibrium (pursuit-evasion on the unit square)
- **THEN** none is reported

#### Scenario: Input errors
- **WHEN** an agent has more than 4 variables, a bound count that matches neither 1 nor its number of variables, or a lower bound not below the upper bound
- **THEN** a translated error names the agent
