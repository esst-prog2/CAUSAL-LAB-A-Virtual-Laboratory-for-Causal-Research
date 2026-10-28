"""
Check the bibliography (causal_lab/utils/references.py) against Crossref.

For every entry with a DOI, the Crossref record must agree on the title,
year, first author, volume, issue and pages. Entries without a DOI are
looked up by title and author, and the best match is shown for a manual
check (books are often not in Crossref).

    python spike/check_references.py

Needs network access to api.crossref.org; sends only DOIs and titles.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from utils.references import REFERENCES  # noqa: E402

API = "https://api.crossref.org/works"
# Known, deliberate differences from the Crossref record.
EXCEPTIONS = {
    # Crossref gives the online date (Dec 2003); APA cites the copyright year
    # printed in the book, 2004, which is also how the book is usually cited.
    ("skyrms_2004", "year"),
}
HEADERS = {"User-Agent": "CausalLab-reference-check/1.0 (https://github.com/esst-prog2)"}


def _get(url: str) -> dict | None:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as reply:
                return json.load(reply)["message"]
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _pages(text: str) -> str:
    return re.sub(r"[–—-]+", "-", text or "")


def _year(item: dict) -> int | None:
    for field in ("published-print", "issued", "published-online"):
        parts = (item.get(field) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def check(ref) -> list[str]:
    item = _get(f"{API}/{urllib.parse.quote(ref.doi)}")
    if item is None:
        return [f"DOI not found in Crossref: {ref.doi}"]
    problems = []
    title = " ".join(item.get("title") or [""]) + (" " + " ".join(item.get("subtitle") or []))
    if difflib.SequenceMatcher(None, _norm(ref.title), _norm(title)).ratio() < 0.85 \
            and _norm(ref.title) not in _norm(title):
        problems.append(f"title: ours {ref.title!r} / Crossref {title.strip()!r}")
    year = _year(item)
    if year != ref.year and (ref.key, "year") not in EXCEPTIONS:
        problems.append(f"year: ours {ref.year} / Crossref {year}")
    authors = item.get("author") or []
    if authors:
        first = _norm(authors[0].get("family", ""))
        if first and first not in _norm(ref.surnames()[0]) and _norm(ref.surnames()[0]) not in first:
            problems.append(f"first author: ours {ref.surnames()[0]} / Crossref {authors[0].get('family')}")
        if len(authors) != len(ref.authors):
            problems.append(f"number of authors: ours {len(ref.authors)} / Crossref {len(authors)}")
    if ref.kind == "article":
        theirs_pages = _pages(item.get("page"))
        ours_pages = _pages(ref.pages)
        if theirs_pages and "-" not in theirs_pages:          # JSTOR-era records give the first page only
            ours_pages = ours_pages.split("-")[0]
        for name, ours, theirs in (("volume", ref.volume, item.get("volume")),
                                   ("issue", _pages(ref.issue), _pages(item.get("issue"))),
                                   ("pages", ours_pages, theirs_pages)):
            if theirs and ours and _norm(ours) != _norm(theirs):
                problems.append(f"{name}: ours {ours} / Crossref {theirs}")
    return problems


def search(ref) -> str:
    query = urllib.parse.urlencode({"query.bibliographic": f"{ref.title} {ref.surnames()[0]} {ref.year}", "rows": 1})
    found = _get(f"{API}?{query}")
    items = (found or {}).get("items") or []
    if not items:
        return "no match"
    it = items[0]
    return (f"best match: {' '.join(it.get('title') or [''])!r}, {_year(it)}, "
            f"{(it.get('author') or [{}])[0].get('family')}, DOI {it.get('DOI')}")


if __name__ == "__main__":
    bad = 0
    for ref in REFERENCES.values():
        if ref.doi:
            problems = check(ref)
            bad += bool(problems)
            print(f"{'OK ' if not problems else 'BAD'} {ref.key}" + "".join(f"\n      {p}" for p in problems), flush=True)
        else:
            print(f"--  {ref.key} (no DOI, {ref.kind}): {search(ref)}", flush=True)
        time.sleep(0.2)
    print(f"\n{bad} entries with a DOI disagree with Crossref")
