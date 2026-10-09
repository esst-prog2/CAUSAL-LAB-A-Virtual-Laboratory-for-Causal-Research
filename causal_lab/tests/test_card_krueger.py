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


def test_did_reproduces_card_krueger_published_effect():
    result = estimate_did(load_card_krueger())
    print(f"CAUSAL LAB DiD = {result.att:.4f} (SE {result.se:.4f}); published = {PUBLISHED_DID}")
    assert abs(result.att - PUBLISHED_DID) <= TOLERANCE, (
        f"DiD on Card & Krueger data = {result.att:.4f}, published {PUBLISHED_DID} ± {TOLERANCE}")


if __name__ == "__main__":
    test_did_reproduces_card_krueger_published_effect()
    print("test_card_krueger: OK")
