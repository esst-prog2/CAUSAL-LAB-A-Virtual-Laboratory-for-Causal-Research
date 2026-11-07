"""
Candidates of the second evaluation set (docs/evaluation/v2/PROTOCOL.md): new works
only, every OpenAlex ID of the first candidates being excluded. The abstracts, needed
for labelling, go to a local file outside the repository.

    python spike/fetch_question_candidates_v2.py docs/evaluation/v2/candidates.json <abstracts.json>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_question_candidates import MAX_WORDS, PAGES, _get, _record  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIRST = ROOT / "docs" / "evaluation" / "candidates.json"
STRATA = {
    "did": ['abstract.search:"difference-in-differences"'],
    "rdd": ['abstract.search:"regression discontinuity"'],
    "iv": ['abstract.search:"instrumental variable"'],
    "rct": ['abstract.search:"randomly assigned"', 'abstract.search:"randomized field experiment"'],
    "synthetic_control": ['abstract.search:"synthetic control"'],
    "its": ['abstract.search:"interrupted time series"'],
    "matching": ['abstract.search:"propensity score matching"'],
    "predictive": ["title.search:predict", "title.search:forecast"],
    "descriptive": ["title.search:prevalence", 'title.search:"what proportion"', 'title.search:"how common"'],
    "ambiguous": ['title.search:"associated with"', "title.search:correlated", 'title.search:"relationship between"'],
    "threshold": ["title.search:eligibility", "title.search:threshold", "title.search:cutoff", 'title.search:"cut-off"'],
}
KEEP = 25
PAGES_V2 = PAGES + 2      # further down the citation order, the first works being excluded


def main(out: Path, abstracts: Path) -> None:
    first = json.loads(FIRST.read_text(encoding="utf-8"))
    seen = {w["openalex"] for works in first.values() for w in works}
    result, text = {}, {}
    for stratum, filters in STRATA.items():
        works = []
        for filter_value in filters:
            for page in range(1, PAGES_V2 + 1):
                works += _get(filter_value, page)
                time.sleep(2)
        works.sort(key=lambda w: -w["cited_by_count"])
        kept = []
        for work in works:
            title = work.get("title") or ""
            if "?" not in title or len(title.split()) > MAX_WORDS or work["id"] in seen:
                continue
            if stratum == "descriptive" and "how many" in title.lower():
                continue
            seen.add(work["id"])
            record = _record(work)
            text[record["openalex"]] = record.pop("abstract")
            kept.append(record)
            if len(kept) == KEEP:
                break
        result[stratum] = kept
        print(stratum, len(kept), flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    abstracts.write_text(json.dumps(text, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
