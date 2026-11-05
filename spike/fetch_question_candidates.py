"""
Retrieves candidate evaluation questions from OpenAlex by the fixed rule of
docs/evaluation/PROTOCOL.md: published articles whose title is a question, by
descending citation count, for each stratum. Run once, before labelling; the
output is the raw material of docs/evaluation/question_set.json.

    python spike/fetch_question_candidates.py docs/evaluation/candidates.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

STRATA = {            # stratum -> (filter values, how many are needed)
    "did": (['abstract.search:"difference-in-differences"'], 7),
    "rdd": (['abstract.search:"regression discontinuity"'], 7),
    "iv": (['abstract.search:"instrumental variable"'], 7),
    "rct": (['abstract.search:"randomized controlled trial"'], 6),
    "synthetic_control": (['abstract.search:"synthetic control"'], 5),
    "its": (['abstract.search:"interrupted time series"'], 4),
    "matching": (['abstract.search:"propensity score matching"'], 4),
    "predictive": (['title.search:predict'], 5),
    "descriptive": (['title.search:"how many"', 'title.search:prevalence'], 5),
    "ambiguous": (['title.search:"associated with"', 'title.search:"relationship between"'], 6),
}
KEEP = 25            # candidates kept per stratum, so that recorded exclusions can be replaced in order
MAX_WORDS = 30
PAGES = 3


def _abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    words = sorted((pos, word) for word, positions in inverted.items() for pos in positions)
    return " ".join(word for _, word in words)


def _get(filter_value: str, page: int) -> list[dict]:
    query = urllib.parse.urlencode({
        "filter": f"{filter_value},type:article,language:en,has_abstract:true",
        "sort": "cited_by_count:desc", "per-page": 200, "page": page,
        "select": "id,doi,title,publication_year,cited_by_count,authorships,primary_location,abstract_inverted_index",
    })
    request = urllib.request.Request(f"https://api.openalex.org/works?{query}",
                                     headers={"User-Agent": "causal-lab-evaluation"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["results"]


def _record(work: dict) -> dict:
    authors = [a["author"]["display_name"] for a in (work.get("authorships") or [])[:3]]
    source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
    return {"openalex": work["id"], "doi": work.get("doi"), "title": work["title"], "year": work["publication_year"],
            "cited_by": work["cited_by_count"], "authors": authors, "journal": source,
            "abstract": _abstract(work.get("abstract_inverted_index"))}


def main(out: Path) -> None:
    result, seen = {}, set()
    for stratum, (filters, _) in STRATA.items():
        works = []
        for filter_value in filters:
            for page in range(1, PAGES + 1):
                works += _get(filter_value, page)
                time.sleep(0.3)
        works.sort(key=lambda w: -w["cited_by_count"])
        kept = []
        for work in works:
            title = work.get("title") or ""
            if "?" not in title or len(title.split()) > MAX_WORDS or work["id"] in seen:
                continue
            seen.add(work["id"])
            kept.append(_record(work))
            if len(kept) == KEEP:
                break
        result[stratum] = kept
        print(stratum, len(kept), flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
