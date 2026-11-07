"""The agreement script: hand-computed values, and a refusal to report on partial ratings."""
import csv
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "spike"))

from compute_kappa import THRESHOLDS, SheetError, agreement, cohen_kappa, read_sheet


def _sheet(rows):
    path = Path(tempfile.mkdtemp()) / "sheet.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question", "intent", "threshold"])
        writer.writerows(rows)
    return path


def test_kappa_against_a_hand_computation():
    # 2 x 2 table: both yes 20, both no 15, yes/no 5, no/yes 10 (n = 50). Observed 0.70.
    # Chance = 0.5 x 0.6 + 0.5 x 0.4 = 0.50, so kappa = 0.20 / 0.50 = 0.40.
    a = ["yes"] * 25 + ["no"] * 25
    b = ["yes"] * 20 + ["no"] * 5 + ["yes"] * 10 + ["no"] * 15
    r = cohen_kappa(a, b, ("yes", "no"))
    assert abs(r["agreement"] - 0.70) < 1e-12 and abs(r["chance"] - 0.50) < 1e-12 and abs(r["kappa"] - 0.40) < 1e-12
    assert abs(r["pabak"] - 0.40) < 1e-12


def test_kappa_falls_with_a_dominant_category_although_agreement_is_high():
    # The prevalence paradox (Feinstein & Cicchetti 1990): 90% agreement, kappa about zero.
    a = ["yes"] * 45 + ["yes"] * 5
    b = ["yes"] * 45 + ["no"] * 5
    r = cohen_kappa(a, b, ("yes", "no"))
    assert abs(r["agreement"] - 0.90) < 1e-12 and abs(r["kappa"]) < 1e-12 and r["pabak"] > 0.75


def test_an_incomplete_or_invalid_sheet_gives_no_result():
    for rows in ([["Q01", "q", "", "no"]], [["Q01", "q", "causal", ""]], [["Q01", "q", "maybe", "no"]]):
        try:
            read_sheet(_sheet(rows))
        except SheetError:
            continue
        raise AssertionError(rows)
    questions = [{"id": "Q01", "question": "q", "intent": "causal", "threshold": None},
                 {"id": "Q02", "question": "r", "intent": "ambiguous", "threshold": None}]
    try:
        agreement(read_sheet(_sheet([["Q01", "q", "causal", "no"]])), questions)
    except SheetError:
        return
    raise AssertionError("a sheet missing a question must be refused")


def test_a_complete_sheet_lists_every_disagreement():
    questions = [{"id": "Q01", "question": "q", "intent": "causal", "threshold": "assignment"},
                 {"id": "Q02", "question": "r", "intent": "ambiguous", "threshold": None}]
    r = agreement(read_sheet(_sheet([["Q01", "q", "Causal", "yes"], ["Q02", "r", "causal", "no"]])), questions)
    assert [d["id"] for d in r["disagreements"]] == ["Q02"] and r["intent"]["n"] == 2
    assert r["threshold"]["agreement"] == 1 and set(r["threshold_by_category"]) == set(THRESHOLDS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_compute_kappa: OK")
