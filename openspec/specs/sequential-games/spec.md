# sequential-games Specification

## Purpose
TBD - created by archiving change sequential-games-bargaining. Update Purpose after archive.

## Requirements

### Requirement: Stackelberg leadership
For the continuous catalogue models with at least two agents (Cournot, Bertrand, Tullock, public good, probabilistic voting), the system SHALL let the researcher choose a leader. It SHALL compute the subgame-perfect equilibrium:
- the followers play a Nash equilibrium of their game for each leader strategy, warm-started on one branch;
- the leader maximizes its utility given that response, on a grid refined by a bounded search and checked on a finer grid.

The system SHALL show it next to the simultaneous Nash equilibrium, with the leader's utility change.

#### Scenario: Closed forms
- **WHEN** a Cournot duopoly (costs 10 and 20), Bertrand with differentiated products, a three-firm Cournot game with one leader, or a Tullock contest (V1 = 10, V2 = 6) is solved with the first agent leading
- **THEN** the strategies equal the backward-induction closed forms: to 1e-7 relative for Cournot and Bertrand, and to 1e-3 relative for Tullock, whose leader objective is flat at the optimum

#### Scenario: First-mover advantage
- **WHEN** Cournot, Bertrand or Tullock is solved with a leader
- **THEN** the leader's utility is at least its simultaneous-game utility

### Requirement: Bargaining
The system SHALL compute:
- the generalized Nash bargaining solution of a surplus S, for bargaining power α, disagreement payoffs d1 and d2, and utilities of money given as expressions in m;
- Rubinstein's alternating-offers equilibrium share (1 - δ2)/(1 - δ1 δ2), with the finite-horizon backward-induction path;
- the Nash solution that the Rubinstein split equals when periods are short (Binmore, Rubinstein & Wolinsky 1986).

#### Scenario: Closed forms
- **WHEN** S = 100, α = 0.3, d = (10, 20) with linear utilities, or player 1's utility is sqrt(m)
- **THEN** player 1's share is 0.31, respectively 1/3

#### Scenario: Patient players
- **WHEN** δi = exp(-ri Δt) with Δt → 0
- **THEN** player 1's Rubinstein share tends to r2/(r1 + r2), the Nash solution with that bargaining power
