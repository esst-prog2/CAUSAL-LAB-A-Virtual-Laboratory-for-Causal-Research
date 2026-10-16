"""hw5 — the link to reality.

"A test would go red if CAUSAL LAB's difference-in-differences estimate on
the Card & Krueger (1994) New Jersey / Pennsylvania fast-food data did not
reproduce their published effect of +2.76 full-time-equivalent employees
per store (±0.1)."

The expected value was fixed by the user, before this test existed (see
PLANNING_LOG.md, 2026-10-09). It comes from the published paper, Card &
Krueger (1994), AER 84(4), Table 3, not from running this program. The
data are the authors' public file (data/card_krueger_1994/SOURCE.md).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimators.did import estimate_did
from utils.real_data import load_card_krueger

PUBLISHED_DID = 2.76      # Card & Krueger (1994), Table 3 — chosen by the user, not computed here
TOLERANCE = 0.1           # rounding + sample definition, chosen by the user
PUBLISHED_SE = 1.36       # same table, logged by the user on 2026-10-09 (hw6 review 3 decision)
N_STORES = 410            # "410 stores", same log entry


def test_did_reproduces_card_krueger_published_effect():
    result = estimate_did(load_card_krueger())
    print(f"CAUSAL LAB DiD = {result.att:.4f} (SE {result.se:.4f}); published = {PUBLISHED_DID}")
    assert abs(result.att - PUBLISHED_DID) <= TOLERANCE, (
        f"DiD on Card & Krueger data = {result.att:.4f}, published {PUBLISHED_DID} ± {TOLERANCE}")


def test_clustered_se_matches_the_published_standard_error():
    # hw6 review 3: the SE used to be 1.91 because the 400+ store dummies were
    # counted in the small-sample correction of a two-period panel. The
    # tolerance is the project's established Card & Krueger tolerance.
    result = estimate_did(load_card_krueger())
    assert abs(result.se - PUBLISHED_SE) <= TOLERANCE, (
        f"clustered SE on Card & Krueger data = {result.se:.4f}, published {PUBLISHED_SE} ± {TOLERANCE}")


def test_every_store_is_its_own_unit():
    # hw6 review 3: SHEET is not unique (two stores, one in each state, share
    # sheet 407), so it cannot be the unit id.
    panel = load_card_krueger()
    assert panel["unit"].nunique() == N_STORES
    assert panel.groupby("unit").size().max() <= 2
    assert (panel.groupby("unit")["treated_unit"].nunique() == 1).all()
    assert (panel.groupby("unit")["period"].nunique() == panel.groupby("unit").size()).all()


if __name__ == "__main__":
    test_did_reproduces_card_krueger_published_effect()
    test_clustered_se_matches_the_published_standard_error()
    test_every_store_is_its_own_unit()
    print("test_card_krueger: OK")
