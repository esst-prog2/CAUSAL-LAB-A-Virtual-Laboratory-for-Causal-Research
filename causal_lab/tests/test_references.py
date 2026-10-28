"""The bibliography is complete, consistent and cited in one style (spec: academic-references).

The entries themselves were checked against Crossref by spike/check_references.py
(network needed); these tests check what can be checked offline.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from report_engine.builder import Heading, Paragraph, build_report
from simulation_engine.dgp import VirtualWorldConfig, generate
from theory_engine.catalogue import CATALOGUE, build
from theory_engine.finite_games import matrix_catalogue
from theory_engine.vector_catalogue import VECTOR_CATALOGUE, build_vector
from utils import reproducibility
from utils.real_data import load_card_krueger
from utils.references import (BIBTEX_HEADER, METHOD_REFERENCES, REFERENCES, cite, keys_of, reference_list,
                              to_bibtex)

APP_DIR = Path(__file__).resolve().parent.parent
REPO = APP_DIR.parent


def _models():
    return ([build(k) for k in CATALOGUE] + list(matrix_catalogue().values())
            + [build_vector(k) for k in VECTOR_CATALOGUE])


def test_every_cited_key_is_in_the_bibliography():
    items = [i for refs in METHOD_REFERENCES.values() for i in refs] + [i for g in _models() for i in g.references]
    assert items
    missing = sorted(set(keys_of(items)) - set(REFERENCES))
    assert not missing, missing


def test_every_model_in_the_catalogues_cites_its_sources():
    uncited = [g.name for g in _models() if not g.references]
    assert not uncited, uncited


def test_entries_are_complete():
    for r in REFERENCES.values():
        assert r.authors and r.title and r.venue and 1700 < r.year <= datetime.now().year, r.key
        if r.kind == "article":
            assert r.volume and r.pages, r.key
            assert r.doi or r.url, f"{r.key}: an article needs a DOI or a stable URL"
        assert "  " not in r.title and not r.title.endswith("."), r.key


def test_citations_follow_apa_7():
    assert cite("downs_1957") == "Downs (1957)"
    assert cite("card_krueger_1994") == "Card & Krueger (1994)"
    assert cite("calonico_cattaneo_titiunik_2014") == "Calonico et al. (2014)"       # three or more authors
    assert cite("persson_tabellini_2000:ch. 3", "black_1948") == "Persson & Tabellini (2000, ch. 3); Black (1948)"
    entry = REFERENCES["lin_2013"].full()
    assert entry == ("Lin, W. (2013). Agnostic notes on regression adjustments to experimental data: Reexamining "
                     "Freedman's critique. Annals of Applied Statistics, 7(1), 295–318. "
                     "https://doi.org/10.1214/12-AOAS583")
    ordered = reference_list(["samuelson_1954", "abadie_imbens_2011", "abadie_imbens_2006", "black_1948"])
    assert [e.split(" (")[0] for e in ordered] == ["Abadie, A., & Imbens, G. W.", "Abadie, A., & Imbens, G. W.",
                                                   "Black, D.", "Samuelson, P. A."]
    assert "(2006)" in ordered[0] and "(2011)" in ordered[1]


def test_no_abbreviated_or_unformatted_citation_in_the_interface():
    # Before: "CCT 2014", "ADH 2010", "Calonico-Cattaneo-Titiunik 2014".
    for lang in ("en", "fr"):
        texts = json.loads((APP_DIR / "locales" / f"{lang}.json").read_text(encoding="utf-8"))
        bad = {k: v for k, v in texts.items()
               if re.search(r"\b(CCT|ADH)\b|[A-Z][a-z]+-[A-Z][a-z]+-[A-Z][a-z]+ (19|20)\d\d", v)}
        assert not bad, (lang, bad)


def test_the_bibtex_file_is_generated_from_the_bibliography():
    bib = (REPO / "docs" / "references.bib").read_text(encoding="utf-8").replace("\r\n", "\n")   # git may check out CRLF
    assert bib == BIBTEX_HEADER + to_bibtex(), "regenerate: cd causal_lab && python utils/references.py > ../docs/references.bib"
    assert bib.count("\n@") + bib.startswith("@") == len(REFERENCES)


def test_the_report_cites_what_it_used_and_lists_the_references():
    df, truth = generate(VirtualWorldConfig(seed=3))
    state = {"virtual_df": df, "virtual_truth": truth, "virtual_cfg": VirtualWorldConfig(seed=3)}
    blocks = build_report(state, "en", now=datetime(2026, 10, 28)).blocks
    headings = [b.text for b in blocks if isinstance(b, Heading)]
    assert "References" in headings and "Software and reproducibility" in headings
    start = headings.index("References")
    texts = [b.text for b in blocks if isinstance(b, Paragraph)]
    assert any(t.startswith("References: Angrist & Pischke (2009, ch. 5); Bertrand et al. (2004)") for t in texts)
    listed = [b.text for b in blocks[[i for i, b in enumerate(blocks)
                                      if isinstance(b, Heading) and b.text == "References"][0] + 1:]
              if isinstance(b, Paragraph)]
    assert any(t.startswith("Bertrand, M., Duflo, E., & Mullainathan, S. (2004).") for t in listed)
    assert any(t.startswith("Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008).") for t in listed)
    assert start > 0

    real = {"uploaded_df": load_card_krueger(), "uploaded_file_id": "card_krueger_1994"}
    texts = [b.text for b in build_report(real, "fr", now=datetime(2026, 10, 28)).blocks if isinstance(b, Paragraph)]
    assert "Références : Card & Krueger (1994)." in texts
    assert any(t.startswith("Card, D., & Krueger, A. B. (1994). Minimum wages and employment") for t in texts)


def test_the_citation_file_matches_the_app():
    cff = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    assert f'version: "{reproducibility.APP_VERSION}"' in cff
    assert f'title: "{reproducibility.APP_NAME}"' in cff
    assert f'repository-code: "{reproducibility.REPOSITORY}"' in cff
    family, initials = reproducibility.APP_AUTHOR.split(", ")
    given = re.search(r'given-names: "([^"]+)"', cff).group(1)
    assert f'family-names: "{family}"' in cff
    assert initials == " ".join(part[0] + "." for part in given.split())        # "Thierry Z." -> "T. Z."
    assert reproducibility.APP_AUTHOR_NAME == f"{given} {family.upper()}"         # "Thierry Z. BARHAME"
    assert reproducibility.citation().startswith(f"{reproducibility.APP_AUTHOR} ({reproducibility.APP_YEAR}). ")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_references: OK")
