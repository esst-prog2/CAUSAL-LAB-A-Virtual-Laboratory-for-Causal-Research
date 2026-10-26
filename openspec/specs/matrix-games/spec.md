# matrix-games Specification

## Purpose
TBD - created by archiving change matrix-games-mixed-equilibria. Update Purpose after archive.

## Requirements

### Requirement: Every Nash equilibrium of a matrix game
The system SHALL let the researcher choose a two-player matrix game from a catalogue or type its payoff matrices (1 to 6 actions per player). It SHALL report every Nash equilibrium, pure and mixed, with each player's probabilities and expected payoff. Equilibria SHALL be found by vertex enumeration of the best-response polytopes. A set of equilibria in a degenerate game SHALL be reported by its extreme points.

The catalogue SHALL hold:
- the prisoner's dilemma;
- matching pennies;
- the battle of the sexes;
- hawk-dove;
- the stag hunt;
- a tax inspection game;
- rock-paper-scissors.

#### Scenario: Closed forms
- **WHEN** the catalogue games are solved
- **THEN** the equilibria equal their closed forms. For instance, the inspection game's only equilibrium has the taxpayer evading with probability 1/11 and the authority inspecting with probability 1/4

#### Scenario: Gambit
- **WHEN** 60 random games (half with tied payoffs) are solved
- **THEN** the equilibria equal Gambit's enummixed extreme equilibria. Every generic game has an odd number of equilibria, and no reported profile admits a profitable pure deviation

### Requirement: Logit quantal response equilibrium
The system SHALL compute the logit QRE for any λ ≥ 0 by following the branch that starts from uniform play, with Newton's method at each step and step halving. It SHALL plot the QRE probabilities as λ grows. The page SHALL state that in games with a symmetry the branch splits: Causal Lab follows the symmetric continuation, where Gambit takes one side.

#### Scenario: Gambit's QRE on generic games
- **WHEN** the QRE of the 30 generic reference games is computed at λ = 1 and λ = 5
- **THEN** it equals Gambit's logit_solve_lambda to 1e-6 and solves the logit equations to 1e-8

#### Scenario: Limits
- **WHEN** λ = 0, or λ = 50 in the prisoner's dilemma
- **THEN** play is uniform, respectively both players defect with probability above 0.999
