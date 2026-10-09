"""
Real-world datasets shipped with CAUSAL LAB.

`load_card_krueger()` reads Card & Krueger's (1994) public New Jersey /
Pennsylvania fast-food file (data/card_krueger_1994/public.dat, see
SOURCE.md there) and returns it in the app's panel format:

    unit          store id (SHEET)
    period        0 = wave 1 (Feb-Mar 1992), 1 = wave 2 (Nov-Dec 1992)
    treated_unit  1 for New Jersey stores (STATE = 1), 0 for Pennsylvania
    D             treated_unit * period
    Y             full-time-equivalent employment, as in the authors'
                  check.sas: EMPPT*.5 + EMPFT + NMGRS

Rows whose employment is missing in a wave are dropped, so the panel is
unbalanced exactly where the survey is.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

CARD_KRUEGER_DIR = Path(__file__).resolve().parent.parent / "data" / "card_krueger_1994"

# (name, first column, last column) from the codebook, 1-based inclusive.
_COLUMNS = [
    ("SHEET", 1, 3), ("CHAIN", 5, 5), ("STATE", 9, 9),
    ("EMPFT", 26, 30), ("EMPPT", 32, 36), ("NMGRS", 38, 42),
    ("STATUS2", 110, 110),
    ("EMPFT2", 122, 126), ("EMPPT2", 128, 132), ("NMGRS2", 134, 138),
]


def read_card_krueger_raw(path: Path | None = None) -> pd.DataFrame:
    """The raw store-level file (one row per store, both waves)."""
    path = path or CARD_KRUEGER_DIR / "public.dat"
    return pd.read_fwf(path, colspecs=[(a - 1, b) for _, a, b in _COLUMNS],
                       names=[n for n, _, _ in _COLUMNS], na_values=["."])


def load_card_krueger(path: Path | None = None) -> pd.DataFrame:
    """Card & Krueger data as a long (store, wave) panel for the app."""
    raw = read_card_krueger_raw(path)
    waves = []
    for period, suffix in ((0, ""), (1, "2")):
        fte = raw[f"EMPPT{suffix}"] * 0.5 + raw[f"EMPFT{suffix}"] + raw[f"NMGRS{suffix}"]
        waves.append(pd.DataFrame({
            "unit": raw["SHEET"].astype(int), "period": period,
            "treated_unit": raw["STATE"].astype(int), "D": raw["STATE"].astype(int) * period,
            "Y": fte, "chain": raw["CHAIN"].astype(int),
        }))
    panel = pd.concat(waves, ignore_index=True).dropna(subset=["Y"])
    return panel.sort_values(["unit", "period"]).reset_index(drop=True)
