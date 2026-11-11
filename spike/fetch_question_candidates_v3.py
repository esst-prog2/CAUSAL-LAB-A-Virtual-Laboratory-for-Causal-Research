"""
Candidates of the third evaluation (docs/evaluation/v3/PROTOCOL.md). One pool per
stratum, with the queries of the second set, further down the citation order and
without any work of the first two sets' candidates. The pool is split by a rule
fixed before it was seen: works at even ranks go to development, at odd ranks to the
test set. The test half is written outside the repository and only its SHA-256 is
recorded, so that it can be shown later that it did not change while the analyser
was developed on the other half.

    python spike/fetch_question_candidates_v3.py <dev.json> <test.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_question_candidates import MAX_WORDS, _get, _record  # noqa: E402
from fetch_question_candidates_v2 import STRATA  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EARLIER = (ROOT / "docs" / "evaluation" / "candidates.json", ROOT / "docs" / "evaluation" / "v2" / "candidates.json")
POOL = 40          # qualifying works kept per stratum, before the split
PAGES_V3 = 9
CACHE = Path.home() / ".cache" / "causal_lab_openalex_v3"


def _page(filter_value: str, page: int) -> list[dict]:
    """One page, cached on disk, retried when OpenAlex sends a truncated answer."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(f"{filter_value}|{page}".encode()).hexdigest()[:20] + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    for attempt in range(5):
        try:
            works = _get(filter_value, page)
            break
        except (json.JSONDecodeError, OSError):
            time.sleep(10 * (attempt + 1))
    else:
        raise SystemExit(f"OpenAlex kept failing on {filter_value}, page {page}")
    path.write_text(json.dumps(works, ensure_ascii=False), encoding="utf-8")
    time.sleep(1)
    return works


def main(dev_out: Path, test_out: Path) -> None:
    seen = {w["openalex"] for path in EARLIER for works in json.loads(path.read_text(encoding="utf-8")).values()
            for w in works}
    dev, test = {}, {}
    for stratum, filters in STRATA.items():
        works = []
        for filter_value in filters:
            for page in range(1, PAGES_V3 + 1):
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
        dev[stratum], test[stratum] = pool[0::2], pool[1::2]
        print(stratum, len(dev[stratum]), len(test[stratum]), flush=True)
    dev_out.parent.mkdir(parents=True, exist_ok=True)
    dev_out.write_text(json.dumps(dev, indent=1, ensure_ascii=False), encoding="utf-8")
    test_out.write_text(json.dumps(test, indent=1, ensure_ascii=False), encoding="utf-8")
    print("test sha256", hashlib.sha256(test_out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
