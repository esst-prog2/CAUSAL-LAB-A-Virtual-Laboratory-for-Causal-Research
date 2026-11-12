"""
Candidates of the fourth evaluation (docs/evaluation/v4/PROTOCOL.md). One pool per
stratum, with the queries of the second set, further down the citation order and
without any work of the earlier sets' candidates or of the third set's development
half. There is no development half: version 3.1 is already frozen. The pool is
written outside the repository and only its SHA-256 is recorded before it is read.

    python spike/fetch_question_candidates_v4.py <test_pool.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_question_candidates import MAX_WORDS, _record  # noqa: E402
from fetch_question_candidates_v2 import STRATA  # noqa: E402
from fetch_question_candidates_v3 import _page  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "docs" / "evaluation"
EARLIER = (EVAL / "candidates.json", EVAL / "v2" / "candidates.json", EVAL / "v3" / "candidates.json")
POOL = 20          # qualifying works kept per stratum
PAGES_V4 = 12


def main(test_out: Path) -> None:
    seen = {w["openalex"] for path in EARLIER for works in json.loads(path.read_text(encoding="utf-8")).values()
            for w in works}
    seen |= {q["openalex"] for q in json.loads((EVAL / "v3" / "dev_set.json").read_text(encoding="utf-8"))["questions"]}
    test = {}
    for stratum, filters in STRATA.items():
        works = []
        for filter_value in filters:
            for page in range(1, PAGES_V4 + 1):
                works += _page(filter_value, page)
        works.sort(key=lambda w: (-w["cited_by_count"], w["id"]))
        pool = []
        for work in works:
            title = work.get("title") or ""
            if "?" not in title or len(title.split()) > MAX_WORDS or work["id"] in seen:
                continue
            if stratum == "descriptive" and "how many" in title.lower():
                continue
            seen.add(work["id"])
            pool.append(_record(work))
            if len(pool) == POOL:
                break
        test[stratum] = pool
        print(stratum, len(pool), flush=True)
    test_out.parent.mkdir(parents=True, exist_ok=True)
    test_out.write_text(json.dumps(test, indent=1, ensure_ascii=False), encoding="utf-8")
    print("test sha256", hashlib.sha256(test_out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main(Path(sys.argv[1]))
