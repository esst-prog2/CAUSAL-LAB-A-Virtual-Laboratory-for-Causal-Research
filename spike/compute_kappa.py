"""
Agreement between a second rater and the labels of a frozen evaluation set.

    python spike/compute_kappa.py docs/evaluation/rater_sheet_filled.csv docs/evaluation/question_set.json

It refuses to compute anything from an incomplete or invalid sheet: a kappa on
partial ratings would look like a result. See docs/evaluation/RATER_PROCEDURE.md.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

INTENTS = ("causal", "predictive", "descriptive", "ambiguous")
THRESHOLDS = ("yes", "unclear", "no")
FIRST_RATER_THRESHOLD = {"assignment": "yes", "unclear": "unclear", "ordinary": "no", None: "no"}


class SheetError(ValueError):
    """The sheet cannot be used: no agreement statistic is reported."""


def read_sheet(path: Path) -> dict[str, tuple[str, str]]:
    """id -> (intent, threshold) of the second rater; raises SheetError on any gap."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    ratings, problems = {}, []
    for row in rows[1:]:
        if len(row) < 4:
            problems.append(f"short row: {row[:1]}")
            continue
        qid, intent, threshold = row[0].strip(), row[2].strip().lower(), row[3].strip().lower()
        if intent not in INTENTS:
            problems.append(f"{qid}: intent {intent!r}")
        if threshold not in THRESHOLDS:
            problems.append(f"{qid}: threshold {threshold!r}")
        ratings[qid] = (intent, threshold)
    if problems:
        raise SheetError("incomplete or invalid ratings, nothing computed: " + "; ".join(problems[:10]))
    return ratings


def cohen_kappa(a: list[str], b: list[str], categories: tuple[str, ...]) -> dict:
    """Cohen (1960): (observed - chance) / (1 - chance), with each rater's own marginals.
    PABAK (Byrt, Bishop & Carlin 1993) is reported with it, because kappa falls when
    one category dominates even if agreement is high."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    chance = sum(ca[c] * cb[c] for c in categories) / n ** 2
    kappa = (observed - chance) / (1 - chance) if chance < 1 else None
    k = len(categories)
    return {"n": n, "agreement": observed, "chance": chance, "kappa": kappa, "pabak": (k * observed - 1) / (k - 1)}


def per_category(a: list[str], b: list[str], categories: tuple[str, ...]) -> dict:
    """Positive agreement per category: 2 x both / (first + second)."""
    out = {}
    for c in categories:
        both = sum(x == c and y == c for x, y in zip(a, b, strict=True))
        first, second = a.count(c), b.count(c)
        out[c] = {"first": first, "second": second, "both": both,
                  "positive_agreement": 2 * both / (first + second) if first + second else None}
    return out


def agreement(ratings: dict, questions: list[dict]) -> dict:
    ids = [q["id"] for q in questions]
    missing = [i for i in ids if i not in ratings]
    extra = [i for i in ratings if i not in ids]
    if missing or extra:
        raise SheetError(f"the sheet does not match the set: missing {missing[:10]}, unknown {extra[:10]}")
    first_intent = [q["intent"] for q in questions]
    second_intent = [ratings[q["id"]][0] for q in questions]
    first_threshold = [FIRST_RATER_THRESHOLD[q["threshold"]] for q in questions]
    second_threshold = [ratings[q["id"]][1] for q in questions]
    disagreements = [{"id": q["id"], "question": q["question"], "first": f, "second": s}
                     for q, f, s in zip(questions, first_intent, second_intent, strict=True) if f != s]
    return {"intent": cohen_kappa(first_intent, second_intent, INTENTS),
            "intent_by_category": per_category(first_intent, second_intent, INTENTS),
            "intent_pairs": sorted(Counter((d["first"], d["second"]) for d in disagreements).items(), key=lambda x: -x[1]),
            "threshold": cohen_kappa(first_threshold, second_threshold, THRESHOLDS),
            "threshold_by_category": per_category(first_threshold, second_threshold, THRESHOLDS),
            "disagreements": disagreements}


def main() -> None:
    sheet, question_set = Path(sys.argv[1]), Path(sys.argv[2])
    questions = json.loads(question_set.read_text(encoding="utf-8"))["questions"]
    try:
        print(json.dumps(agreement(read_sheet(sheet), questions), indent=1, ensure_ascii=False))
    except SheetError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
