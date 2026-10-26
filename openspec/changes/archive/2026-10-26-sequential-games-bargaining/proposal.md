## Why

Sequential equilibria (Stackelberg, bargaining) were in README section 3's "Not this term" list. The user asked for a broad project on 2026-10-26.

## What Changes

- `theory_engine/sequential.py`: subgame-perfect Stackelberg equilibrium for any continuous Game, with a chosen leader and the followers' Nash response re-solved per leader strategy.
- `theory_engine/bargaining.py`: the generalized Nash bargaining solution with utility expressions, and Rubinstein's infinite and finite horizon.
- `ui/sequential_page.py`, with two new model kinds on the Theory page:
  - Stackelberg, compared with the simultaneous game; the result is kept across reruns;
  - Bargaining: the Nash solution, the Rubinstein path, and the Binmore, Rubinstein & Wolinsky link.
- Messages in English and French.

## Capabilities

### New Capabilities
- `sequential-games`

### Modified Capabilities
(none)

## Impact

**Validated against closed forms derived independently:** Cournot (2 and 3 firms), Bertrand by sympy backward induction, Tullock by Dixit (1987), and the Nash and Rubinstein formulas.

**Precision:** the nested numerical solution locates the leader to about 1e-7 relative. On the Tullock contest it is about 1e-4, because the leader's objective is flat at the optimum (its utility agrees to 1e-8).

**Tests:** new `tests/test_sequential_games.py`; 4 of 4 mutants caught.
