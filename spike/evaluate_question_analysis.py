"""
Runs the frozen evaluation of docs/evaluation/PROTOCOL.md: the analyser on
question_set.json. Refuses to run if the set differs from its recorded hash.

    python spike/evaluate_question_analysis.py docs/evaluation/v2
writes results.json in that folder and prints the tables of the report. It refuses
to overwrite an existing results.json: a frozen set is run once.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "causal_lab"))

from causal_engine.diagnosis import ResearchDesignInput, diagnose  # noqa: E402
from causal_engine.question_analysis import STATED, analyze  # noqa: E402
from causal_engine.recommendation import recommend, recommended  # noqa: E402

INTENTS = ("causal", "predictive", "descriptive", "ambiguous")
NO_PRE = dict(has_pre_treatment_periods=False, n_pre_periods=0)
# The form each design implies, fixed before the run.
FORMS = {
    "rct": dict(assignment_mechanism="random", data_structure="experimental", **NO_PRE),
    "rdd": dict(assignment_mechanism="threshold", data_structure="cross_section", **NO_PRE),
    "did": dict(assignment_mechanism="policy", data_structure="panel", n_pre_periods=4, answers_confirmed=True),
    "synthetic_control": dict(assignment_mechanism="policy", data_structure="panel", n_pre_periods=15,
                              n_treated_units="one"),
    "iv": dict(assignment_mechanism="self_selected", data_structure="cross_section", instrument="available", **NO_PRE),
    "its": dict(assignment_mechanism="policy", data_structure="time_series", n_pre_periods=24, n_treated_units="one",
                has_control_group=False, instrument="none"),
    "matching": dict(assignment_mechanism="self_selected", data_structure="cross_section", instrument="none",
                     confounders_observed="measured", **NO_PRE),
}
FAMILY = {"event_study": "did"}


def _family(key):
    return FAMILY.get(key, key)


def _clue(design: str, analysis) -> bool:
    inferred = analysis.inferred
    return {"rdd": inferred.get("assignment_mechanism") == "threshold",
            "rct": inferred.get("assignment_mechanism") == "random",
            "iv": inferred.get("instrument") == "available",
            "did": inferred.get("assignment_mechanism") == "policy" or inferred.get("treatment_timing") == "staggered",
            "synthetic_control": inferred.get("n_treated_units") == "one",
            "its": inferred.get("n_treated_units") == "one",
            "matching": inferred.get("assignment_mechanism") == "self_selected"}[design]


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
    return {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}


def _method(question: str, design: str, **extra) -> str:
    d = ResearchDesignInput(research_question=question, **FORMS[design], **extra)
    best = recommended(recommend(d, diagnose(d)))
    if best is None:
        return "abstained"
    return "correct" if _family(best.key) == _family(design) else f"wrong:{best.key}"


def main() -> None:
    EVAL = Path(sys.argv[1])
    if (EVAL / "results.json").exists():
        raise SystemExit(f"{EVAL / 'results.json'} exists: this set has been run. Results are not replaced.")
    raw = (EVAL / "question_set.json").read_bytes()
    recorded = (EVAL / "question_set.sha256").read_text(encoding="utf-8").split()[0]
    digest = hashlib.sha256(raw).hexdigest()
    if digest != recorded:
        raise SystemExit(f"question_set.json differs from its frozen hash: {digest} != {recorded}")
    questions = json.loads(raw)["questions"]

    rows = []
    for item in questions:
        q = item["question"]
        d = ResearchDesignInput(research_question=q)
        analysis = analyze(d)
        recs = recommend(d, diagnose(d))
        follow = [m.key for m in analysis.follow_up]
        row = {"id": item["id"], "question": q, "stratum": item["stratum"], "intent": item["intent"],
               "read": analysis.intent, "evidence": analysis.intent_words, "threshold": item["threshold"],
               "threshold_read": analysis.threshold, "design": item["design"],
               "recommended_no_form": recommended(recs).key if recommended(recs) else None,
               "follow_up": follow, "treatment": str(analysis.elements["treatment"].text),
               "treatment_status": analysis.status("treatment"), "outcome": str(analysis.elements["outcome"].text),
               "outcome_status": analysis.status("outcome"), "inferred": dict(analysis.inferred)}
        key = item.get("clarification_key")
        row["clarification_ok"] = None if not key else key in follow
        if item["design"]:
            row["clue"] = _clue(item["design"], analysis)
            row["method"] = _method(q, item["design"])
            row["method_confirmed"] = _method(q, item["design"], causal_confirmed=True)
        for part in ("treatment", "outcome"):
            word = item.get(f"{part}_word")
            row[f"{part}_ok"] = None if not word else word.lower() in row[part].lower()
        rows.append(row)

    n = len(rows)
    confusion = {a: {b: sum(r["intent"] == a and r["read"] == b for r in rows) for b in INTENTS} for a in INTENTS}
    per_class = {c: _prf(confusion[c][c], sum(confusion[o][c] for o in INTENTS if o != c),
                         sum(confusion[c][o] for o in INTENTS if o != c)) for c in INTENTS}
    with_design = [r for r in rows if r["design"]]
    method = Counter(r["method"].split(":")[0] for r in with_design)
    method_confirmed = Counter(r["method_confirmed"].split(":")[0] for r in with_design)
    by_design = {}
    for design in sorted({r["design"] for r in with_design}):
        group = [r for r in with_design if r["design"] == design]
        by_design[design] = {"n": len(group), "clue": sum(r["clue"] for r in group),
                             "correct": sum(r["method"] == "correct" for r in group),
                             "abstained": sum(r["method"] == "abstained" for r in group),
                             "wrong": sum(r["method"].startswith("wrong") for r in group),
                             "correct_confirmed": sum(r["method_confirmed"] == "correct" for r in group),
                             "wrong_confirmed": sum(r["method_confirmed"].startswith("wrong") for r in group)}
    ambiguous = [r for r in rows if r["intent"] == "ambiguous"]
    stated = [(r, p) for r in rows for p in ("treatment", "outcome") if r[f"{p}_status"] == STATED and r[f"{p}_ok"] is not None]
    kinds = ("assignment", "unclear", "ordinary", None)
    threshold_confusion = {str(a): {str(b): sum(r["threshold"] == a and r["threshold_read"] == b for r in rows) for b in kinds}
                           for a in kinds}
    no_threshold = [r for r in rows if r["threshold"] != "assignment"]
    has_threshold = [r for r in rows if r["threshold"] == "assignment"]
    summary = {
        "n": n, "strata": dict(Counter(r["stratum"] for r in rows)), "intents": dict(Counter(r["intent"] for r in rows)),
        "accuracy": sum(r["intent"] == r["read"] for r in rows) / n, "confusion": confusion, "per_class": per_class,
        "false_causal": sum(r["intent"] != "causal" and r["read"] == "causal" for r in rows),
        "not_causal_labelled": sum(r["intent"] != "causal" for r in rows),
        "false_non_causal": sum(r["intent"] == "causal" and r["read"] in ("predictive", "descriptive") for r in rows),
        "causal_labelled": sum(r["intent"] == "causal" for r in rows),
        "ambiguous_abstained": sum(r["read"] == "ambiguous" and "qa.ask.intent" in r["follow_up"] for r in ambiguous),
        "ambiguous_labelled": len(ambiguous),
        "recommended_without_form": sum(r["recommended_no_form"] is not None for r in rows),
        "with_design": len(with_design), "method": dict(method), "method_confirmed": dict(method_confirmed),
        "by_design": by_design,
        "threshold_confusion": threshold_confusion,
        "threshold_true_positive": sum(r["threshold_read"] == "assignment" for r in has_threshold),
        "threshold_labelled": len(has_threshold),
        "threshold_false_positive": sum(r["threshold_read"] == "assignment" for r in no_threshold),
        "clarification_ok": sum(r["clarification_ok"] is True for r in rows),
        "clarification_labelled": sum(r["clarification_ok"] is not None for r in rows),
        "treatment_ok": sum(r["treatment_ok"] is True for r in rows),
        "treatment_labelled": sum(r["treatment_ok"] is not None for r in rows),
        "outcome_ok": sum(r["outcome_ok"] is True for r in rows),
        "outcome_labelled": sum(r["outcome_ok"] is not None for r in rows),
        "stated_wrong": sum(r[f"{p}_ok"] is False for r, p in stated), "stated_checked": len(stated),
    }
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (EVAL / "results.json").write_text(json.dumps({"commit": commit, "question_set_sha256": digest, "summary": summary,
                                                   "rows": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
