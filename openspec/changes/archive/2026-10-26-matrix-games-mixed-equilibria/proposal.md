## Why

README section 3 listed "mixed-strategy equilibria" under "Not this term". On 2026-10-26 the user asked for a broad project ("fais mon projet vaste et bien fait") and to stop following the single-method advice.

## What Changes

- **`theory_engine/finite_games.py`:**
  - bimatrix games;
  - all Nash equilibria by vertex enumeration of the best-response polytopes, as Gambit's enummixed does;
  - the logit QRE by branch continuation from uniform play;
  - a catalogue of 7 games.
- **`ui/matrix_game_page.py`:** catalogue or payoff editor, payoff table, equilibrium table, and QRE path chart.
- **Theory page:** a "Kind of model" choice (continuous / matrix), which persists across pages.
- **Messages:** English and French.
- **References:** `tests/external_reference` stores Gambit's equilibria and QREs for 60 random games (pygambit 16.7.0).

## Capabilities

### New Capabilities
- `matrix-games`

### Modified Capabilities
(none)

## Impact

**Two first drafts were replaced after comparing with references:**
- **Support enumeration** reported only valid equilibria, but in 54 of 300 tied games it missed extreme points, because its minimum-norm solutions fell inside a face. Vertex enumeration now equals Gambit on all 800 test games.
- **A damped fixed-point QRE** jumped branches at λ ≥ 3. Newton continuation now equals Gambit to 1.4e-9 on 600 generic (game, λ) pairs.

**nashpy disagreed with Gambit on 41 of 500 generic games:**
- it reported an even number of equilibria in 36 of them, impossible for a generic game;
- Gambit is therefore the stored reference.

**Tests:** new `tests/test_finite_games.py`; 4 real mutants caught.
