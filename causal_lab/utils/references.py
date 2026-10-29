"""
The bibliography of Causal Lab: every work the app's methods, checks and
models rest on, in one place.

Each entry is cited in the interface as "Author (Year)" and listed in full in
the report and in docs/references.bib (generated from this file; a test keeps
the two in sync). Journal articles carry their DOI; the DOIs, titles, years,
volumes and pages were checked against Crossref on 2026-10-28
(spike/check_references.py).

Style: APA 7th edition, author-year.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Reference:
    key: str
    kind: str                         # "article", "book", "chapter", "unpublished"
    authors: tuple[str, ...]          # "Surname, I. I."
    year: int
    title: str
    venue: str = ""                   # journal, publisher, or "In Editors (Eds.), Book" for chapters
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    note: str = ""
    cited_as: str = field(default="", compare=False)   # in-text form when the default would be ambiguous

    # ------------------------------------------------------------------
    def surnames(self) -> list[str]:
        return [a.split(",")[0] for a in self.authors]

    def citation(self) -> str:
        """In-text citation: Author (Year), Author & Author (Year), Author et al. (Year)."""
        if self.cited_as:
            return self.cited_as
        names = self.surnames()
        if len(names) == 1:
            who = names[0]
        elif len(names) == 2:
            who = f"{names[0]} & {names[1]}"
        else:
            who = f"{names[0]} et al."
        return f"{who} ({self.year})"

    def full(self) -> str:
        """APA-style reference list entry (plain text)."""
        authors = self.authors
        if len(authors) == 1:
            who = authors[0]
        elif len(authors) <= 20:
            who = ", ".join(authors[:-1]) + ", & " + authors[-1]
        else:
            who = ", ".join(authors[:19]) + ", ... " + authors[-1]
        end = "" if self.title.endswith(("?", "!")) else "."          # APA: no period after ? or !
        parts = [f"{who} ({self.year}). {self.title}{end}"]
        if self.kind == "article":
            vol = self.volume + (f"({self.issue})" if self.issue else "")
            parts.append(f" {self.venue}, {vol}, {self.pages}." if self.pages else f" {self.venue}, {vol}.")
        elif self.kind in ("book", "chapter"):
            parts.append(f" {self.venue}.")
        elif self.venue:
            parts.append(f" {self.venue}.")
        if self.doi:
            parts.append(f" https://doi.org/{self.doi}")
        elif self.url:
            parts.append(f" {self.url}")
        if self.note:
            parts.append(f" {self.note}")
        return "".join(parts)


def _a(key, authors, year, title, venue, volume, issue, pages, doi="", **kw) -> Reference:
    return Reference(key, "article", tuple(authors), year, title, venue, str(volume), str(issue), pages, doi, **kw)


def _b(key, authors, year, title, publisher, **kw) -> Reference:
    return Reference(key, "book", tuple(authors), year, title, publisher, **kw)


_ENTRIES = [
    # ---------------------------------------------------------------- data
    _a("card_krueger_1994", ["Card, D.", "Krueger, A. B."], 1994,
       "Minimum wages and employment: A case study of the fast-food industry in New Jersey and Pennsylvania",
       "American Economic Review", 84, 4, "772–793", url="https://www.jstor.org/stable/2118030"),
    # ------------------------------------------------- difference-in-differences
    _b("angrist_pischke_2009", ["Angrist, J. D.", "Pischke, J.-S."], 2009,
       "Mostly harmless econometrics: An empiricist's companion", "Princeton University Press"),
    _a("bertrand_duflo_mullainathan_2004", ["Bertrand, M.", "Duflo, E.", "Mullainathan, S."], 2004,
       "How much should we trust differences-in-differences estimates?", "Quarterly Journal of Economics",
       119, 1, "249–275", "10.1162/003355304772839588"),
    _a("callaway_santanna_2021", ["Callaway, B.", "Sant'Anna, P. H. C."], 2021,
       "Difference-in-differences with multiple time periods", "Journal of Econometrics", 225, 2, "200–230",
       "10.1016/j.jeconom.2020.12.001"),
    _a("goodman_bacon_2021", ["Goodman-Bacon, A."], 2021,
       "Difference-in-differences with variation in treatment timing", "Journal of Econometrics", 225, 2,
       "254–277", "10.1016/j.jeconom.2021.03.014"),
    _a("dechaisemartin_dhaultfoeuille_2020", ["de Chaisemartin, C.", "D'Haultfœuille, X."], 2020,
       "Two-way fixed effects estimators with heterogeneous treatment effects", "American Economic Review",
       110, 9, "2964–2996", "10.1257/aer.20181169"),
    _a("cameron_gelbach_miller_2008", ["Cameron, A. C.", "Gelbach, J. B.", "Miller, D. L."], 2008,
       "Bootstrap-based improvements for inference with clustered errors", "Review of Economics and Statistics",
       90, 3, "414–427", "10.1162/rest.90.3.414"),
    _a("mackinnon_webb_2017", ["MacKinnon, J. G.", "Webb, M. D."], 2017,
       "Wild bootstrap inference for wildly different cluster sizes", "Journal of Applied Econometrics",
       32, 2, "233–254", "10.1002/jae.2508"),
    _a("durbin_watson_1950", ["Durbin, J.", "Watson, G. S."], 1950,
       "Testing for serial correlation in least squares regression: I", "Biometrika", 37, "3/4", "409–428",
       "10.1093/biomet/37.3-4.409"),
    _a("roth_2022", ["Roth, J."], 2022,
       "Pretest with caution: Event-study estimates after testing for parallel trends",
       "American Economic Review: Insights", 4, 3, "305–322", "10.1257/aeri.20210236"),
    _a("morris_white_crowther_2019", ["Morris, T. P.", "White, I. R.", "Crowther, M. J."], 2019,
       "Using simulation studies to evaluate statistical methods", "Statistics in Medicine", 38, 11, "2074–2102",
       "10.1002/sim.8086"),
    _b("wooldridge_2010", ["Wooldridge, J. M."], 2010,
       "Econometric analysis of cross section and panel data (2nd ed.)", "MIT Press"),
    # ----------------------------------------------------------------- RCT
    _a("lin_2013", ["Lin, W."], 2013,
       "Agnostic notes on regression adjustments to experimental data: Reexamining Freedman's critique",
       "Annals of Applied Statistics", 7, 1, "295–318", "10.1214/12-AOAS583"),
    _a("mackinnon_white_1985", ["MacKinnon, J. G.", "White, H."], 1985,
       "Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties",
       "Journal of Econometrics", 29, 3, "305–325", "10.1016/0304-4076(85)90158-7"),
    # ------------------------------------------------------------ matching
    _a("rosenbaum_rubin_1983", ["Rosenbaum, P. R.", "Rubin, D. B."], 1983,
       "The central role of the propensity score in observational studies for causal effects", "Biometrika",
       70, 1, "41–55", "10.1093/biomet/70.1.41"),
    _a("abadie_imbens_2006", ["Abadie, A.", "Imbens, G. W."], 2006,
       "Large sample properties of matching estimators for average treatment effects", "Econometrica",
       74, 1, "235–267", "10.1111/j.1468-0262.2006.00655.x"),
    _a("abadie_imbens_2008", ["Abadie, A.", "Imbens, G. W."], 2008,
       "On the failure of the bootstrap for matching estimators", "Econometrica", 76, 6, "1537–1557",
       "10.3982/ECTA6474"),
    _a("abadie_imbens_2011", ["Abadie, A.", "Imbens, G. W."], 2011,
       "Bias-corrected matching estimators for average treatment effects", "Journal of Business & Economic Statistics",
       29, 1, "1–11", "10.1198/jbes.2009.07333"),
    _a("abadie_imbens_2016", ["Abadie, A.", "Imbens, G. W."], 2016,
       "Matching on the estimated propensity score", "Econometrica", 84, 2, "781–807", "10.3982/ECTA11293"),
    # --------------------------------------------------------------- IV
    _a("imbens_angrist_1994", ["Imbens, G. W.", "Angrist, J. D."], 1994,
       "Identification and estimation of local average treatment effects", "Econometrica", 62, 2, "467–475",
       "10.2307/2951620"),
    _a("staiger_stock_1997", ["Staiger, D.", "Stock, J. H."], 1997,
       "Instrumental variables regression with weak instruments", "Econometrica", 65, 3, "557–586",
       "10.2307/2171753"),
    # --------------------------------------------------------------- RDD
    _a("hahn_todd_vanderklaauw_2001", ["Hahn, J.", "Todd, P.", "Van der Klaauw, W."], 2001,
       "Identification and estimation of treatment effects with a regression-discontinuity design", "Econometrica",
       69, 1, "201–209", "10.1111/1468-0262.00183"),
    _a("imbens_kalyanaraman_2012", ["Imbens, G. W.", "Kalyanaraman, K."], 2012,
       "Optimal bandwidth choice for the regression discontinuity estimator", "Review of Economic Studies",
       79, 3, "933–959", "10.1093/restud/rdr043"),
    _a("calonico_cattaneo_titiunik_2014", ["Calonico, S.", "Cattaneo, M. D.", "Titiunik, R."], 2014,
       "Robust nonparametric confidence intervals for regression-discontinuity designs", "Econometrica",
       82, 6, "2295–2326", "10.3982/ECTA11757"),
    # --------------------------------------------------- synthetic control
    _a("abadie_gardeazabal_2003", ["Abadie, A.", "Gardeazabal, J."], 2003,
       "The economic costs of conflict: A case study of the Basque Country", "American Economic Review",
       93, 1, "113–132", "10.1257/000282803321455188"),
    _a("abadie_diamond_hainmueller_2010", ["Abadie, A.", "Diamond, A.", "Hainmueller, J."], 2010,
       "Synthetic control methods for comparative case studies: Estimating the effect of California's tobacco "
       "control program", "Journal of the American Statistical Association", 105, 490, "493–505",
       "10.1198/jasa.2009.ap08746"),
    # --------------------------------------------------------------- DML
    _a("robinson_1988", ["Robinson, P. M."], 1988, "Root-N-consistent semiparametric regression", "Econometrica",
       56, 4, "931–954", "10.2307/1912705"),
    _a("chernozhukov_et_al_2018", ["Chernozhukov, V.", "Chetverikov, D.", "Demirer, M.", "Duflo, E.", "Hansen, C.",
                                   "Newey, W.", "Robins, J."], 2018,
       "Double/debiased machine learning for treatment and structural parameters", "Econometrics Journal",
       21, 1, "C1–C68", "10.1111/ectj.12097"),
    # ------------------------------------------------------ game theory
    _b("von_neumann_morgenstern_1944", ["von Neumann, J.", "Morgenstern, O."], 1944,
       "Theory of games and economic behavior", "Princeton University Press"),
    _a("nash_1950", ["Nash, J. F."], 1950, "The bargaining problem", "Econometrica", 18, 2, "155–162",
       "10.2307/1907266"),
    Reference("tucker_1950", "unpublished", ("Tucker, A. W.",), 1950, "A two-person dilemma",
              "Unpublished manuscript, Stanford University"),
    _b("luce_raiffa_1957", ["Luce, R. D.", "Raiffa, H."], 1957, "Games and decisions: Introduction and critical survey",
       "Wiley"),
    _a("maynard_smith_price_1973", ["Maynard Smith, J.", "Price, G. R."], 1973, "The logic of animal conflict",
       "Nature", 246, 5427, "15–18", "10.1038/246015a0"),
    _b("rousseau_1755", ["Rousseau, J.-J."], 1755,
       "Discours sur l'origine et les fondements de l'inégalité parmi les hommes", "Marc-Michel Rey"),
    _b("axelrod_1984", ["Axelrod, R."], 1984, "The evolution of cooperation", "Basic Books"),
    _a("tsebelis_1989", ["Tsebelis, G."], 1989,
       "The abuse of probability in political analysis: The Robinson Crusoe fallacy",
       "American Political Science Review", 83, 1, "77–91", "10.2307/1956435"),
    _a("andreozzi_2004", ["Andreozzi, L."], 2004,
       "Rewarding policemen increases crime. Another surprising result from the inspection game", "Public Choice",
       121, "1–2", "69–82", "10.1007/s11127-004-6166-x"),
    _b("fudenberg_tirole_1991", ["Fudenberg, D.", "Tirole, J."], 1991, "Game theory", "MIT Press"),
    _b("skyrms_2004", ["Skyrms, B."], 2004, "The stag hunt and the evolution of social structure",
       "Cambridge University Press", doi="10.1017/CBO9781139165228"),
    _a("mckelvey_palfrey_1995", ["McKelvey, R. D.", "Palfrey, T. R."], 1995,
       "Quantal response equilibria for normal form games", "Games and Economic Behavior", 10, 1, "6–38",
       "10.1006/game.1995.1023"),
    _a("avis_et_al_2010", ["Avis, D.", "Rosenberg, G. D.", "Savani, R.", "von Stengel, B."], 2010,
       "Enumeration of Nash equilibria for two-player games", "Economic Theory", 42, 1, "9–37",
       "10.1007/s00199-009-0449-x"),
    _a("rubinstein_1982", ["Rubinstein, A."], 1982, "Perfect equilibrium in a bargaining model", "Econometrica",
       50, 1, "97–109", "10.2307/1912531"),
    _a("binmore_rubinstein_wolinsky_1986", ["Binmore, K.", "Rubinstein, A.", "Wolinsky, A."], 1986,
       "The Nash bargaining solution in economic modelling", "RAND Journal of Economics", 17, 2, "176–188",
       "10.2307/2555382"),
    _b("von_stackelberg_1934", ["von Stackelberg, H."], 1934, "Marktform und Gleichgewicht", "Springer"),
    _a("dixit_1987", ["Dixit, A."], 1987, "Strategic behavior in contests", "American Economic Review", 77, 5,
       "891–898", url="https://www.jstor.org/stable/1810215"),
    # ------------------------------------------ structural estimation
    _a("hansen_1982", ["Hansen, L. P."], 1982, "Large sample properties of generalized method of moments estimators",
       "Econometrica", 50, 4, "1029–1054", "10.2307/1912775"),
    _a("hansen_singleton_1982", ["Hansen, L. P.", "Singleton, K. J."], 1982,
       "Generalized instrumental variables estimation of nonlinear rational expectations models", "Econometrica",
       50, 5, "1269–1286", "10.2307/1911873"),
    # -------------------------------------------- public choice models
    _a("black_1948", ["Black, D."], 1948, "On the rationale of group decision-making", "Journal of Political Economy",
       56, 1, "23–34", "10.1086/256633"),
    _b("downs_1957", ["Downs, A."], 1957, "An economic theory of democracy", "Harper & Row"),
    _a("lindbeck_weibull_1987", ["Lindbeck, A.", "Weibull, J. W."], 1987,
       "Balanced-budget redistribution as the outcome of political competition", "Public Choice", 52, 3,
       "273–297", "10.1007/BF00116710"),
    _b("persson_tabellini_2000", ["Persson, T.", "Tabellini, G."], 2000,
       "Political economics: Explaining economic policy", "MIT Press"),
    Reference("tullock_1980", "chapter", ("Tullock, G.",), 1980, "Efficient rent seeking",
              "In J. M. Buchanan, R. D. Tollison, & G. Tullock (Eds.), Toward a theory of the rent-seeking society "
              "(pp. 97–112). Texas A&M University Press"),
    _a("hillman_riley_1989", ["Hillman, A. L.", "Riley, J. G."], 1989, "Politically contestable rents and transfers",
       "Economics & Politics", 1, 1, "17–39", "10.1111/j.1468-0343.1989.tb00003.x"),
    _b("niskanen_1971", ["Niskanen, W. A."], 1971, "Bureaucracy and representative government", "Aldine-Atherton"),
    _b("mueller_2003", ["Mueller, D. C."], 2003, "Public choice III", "Cambridge University Press",
       doi="10.1017/CBO9780511813771"),
    _a("samuelson_1954", ["Samuelson, P. A."], 1954, "The pure theory of public expenditure",
       "Review of Economics and Statistics", 36, 4, "387–389", "10.2307/1925895"),
    _a("bergstrom_blume_varian_1986", ["Bergstrom, T.", "Blume, L.", "Varian, H."], 1986,
       "On the private provision of public goods", "Journal of Public Economics", 29, 1, "25–49",
       "10.1016/0047-2727(86)90024-1"),
    _b("coughlin_1992", ["Coughlin, P. J."], 1992, "Probabilistic voting theory", "Cambridge University Press",
       doi="10.1017/CBO9780511895395"),
    _a("lin_enelow_dorussen_1999", ["Lin, T.-M.", "Enelow, J. M.", "Dorussen, H."], 1999,
       "Equilibrium in multicandidate probabilistic spatial voting", "Public Choice", 98, "1–2", "59–82",
       "10.1023/A:1018391410733"),
    _a("schofield_2007", ["Schofield, N."], 2007,
       "The mean voter theorem: Necessary and sufficient conditions for convergent equilibrium",
       "Review of Economic Studies", 74, 3, "965–980", "10.1111/j.1467-937X.2007.00444.x"),
    _a("snyder_1989", ["Snyder, J. M."], 1989, "Election goals and the allocation of campaign resources",
       "Econometrica", 57, 3, "637–660", "10.2307/1911056"),
    _b("konrad_2009", ["Konrad, K. A."], 2009, "Strategy and dynamics in contests", "Oxford University Press"),
    # --------------------------------------------- industrial organization
    _b("cournot_1838", ["Cournot, A.-A."], 1838,
       "Recherches sur les principes mathématiques de la théorie des richesses", "Hachette"),
    _b("tirole_1988", ["Tirole, J."], 1988, "The theory of industrial organization", "MIT Press"),
    _a("singh_vives_1984", ["Singh, N.", "Vives, X."], 1984, "Price and quantity competition in a differentiated duopoly",
       "RAND Journal of Economics", 15, 4, "546–554", "10.2307/2555525"),
    _b("vives_1999", ["Vives, X."], 1999, "Oligopoly pricing: Old ideas and new tools", "MIT Press"),
    _a("bulow_geanakoplos_klemperer_1985", ["Bulow, J. I.", "Geanakoplos, J. D.", "Klemperer, P. D."], 1985,
       "Multimarket oligopoly: Strategic substitutes and complements", "Journal of Political Economy", 93, 3,
       "488–511", "10.1086/261312"),
]

REFERENCES: dict[str, Reference] = {r.key: r for r in _ENTRIES}
assert len(REFERENCES) == len(_ENTRIES), "duplicate reference key"


# What each method, check and solver of the app rests on (citation items).
METHOD_REFERENCES: dict[str, tuple[str, ...]] = {
    "did": ("angrist_pischke_2009:ch. 5", "bertrand_duflo_mullainathan_2004"),
    "event_study": ("angrist_pischke_2009:ch. 5",),
    "staggered": ("callaway_santanna_2021", "goodman_bacon_2021", "dechaisemartin_dhaultfoeuille_2020"),
    "stress_test": ("cameron_gelbach_miller_2008", "mackinnon_webb_2017", "durbin_watson_1950",
                    "wooldridge_2010:ch. 10"),
    "rct": ("lin_2013", "mackinnon_white_1985"),
    "matching": ("rosenbaum_rubin_1983", "abadie_imbens_2006", "abadie_imbens_2008", "abadie_imbens_2011",
                 "abadie_imbens_2016"),
    "iv": ("imbens_angrist_1994", "staiger_stock_1997"),
    "rdd": ("hahn_todd_vanderklaauw_2001", "imbens_kalyanaraman_2012", "calonico_cattaneo_titiunik_2014"),
    "synthetic_control": ("abadie_gardeazabal_2003", "abadie_diamond_hainmueller_2010"),
    "dml": ("robinson_1988", "chernozhukov_et_al_2018"),
    "nash_enumeration": ("avis_et_al_2010",),
    "qre": ("mckelvey_palfrey_1995",),
    "gmm": ("hansen_1982", "hansen_singleton_1982"),
    "stackelberg": ("von_stackelberg_1934", "dixit_1987"),
    "bargaining": ("nash_1950", "rubinstein_1982", "binmore_rubinstein_wolinsky_1986"),
    "demo_study": ("morris_white_crowther_2019", "roth_2022", "cameron_gelbach_miller_2008",
                   "bertrand_duflo_mullainathan_2004"),
    "demo_replication": ("card_krueger_1994",),
}


def _split(item: str) -> tuple[str, str]:
    """"persson_tabellini_2000:ch. 3" -> ("persson_tabellini_2000", "ch. 3")."""
    key, _, pinpoint = item.partition(":")
    return key, pinpoint.strip()


def cite(*items: str) -> str:
    """In-text citations joined by "; ". Each item is a key, or a key and a
    pinpoint: cite("downs_1957", "persson_tabellini_2000:ch. 3") gives
    "Downs (1957); Persson & Tabellini (2000, ch. 3)"."""
    out = []
    for item in items:
        key, pinpoint = _split(item)
        text = REFERENCES[key].citation()
        out.append(text[:-1] + f", {pinpoint})" if pinpoint else text)
    return "; ".join(out)


def keys_of(items) -> list[str]:
    """The reference keys of citation items (pinpoints dropped)."""
    return [_split(item)[0] for item in items]


def reference_list(keys) -> list[str]:
    """Full entries for `keys`, without duplicates, sorted by first author and year (APA order)."""
    unique = {k: REFERENCES[k] for k in keys}
    return [r.full() for r in sorted(unique.values(), key=lambda r: (r.surnames()[0].lower().replace("von ", "")
                                                                     .replace("de ", ""), r.year, r.title))]


_BIBTEX_TYPES = {"article": "article", "book": "book", "chapter": "incollection", "unpublished": "unpublished"}


def _bib_escape(text: str) -> str:
    return text.replace("&", r"\&")


def to_bibtex(keys=None) -> str:
    """BibTeX entries for `keys` (all references by default), in key order."""
    out = []
    for key in sorted(keys or REFERENCES):
        r = REFERENCES[key]
        fields = {"author": " and ".join(r.authors), "year": str(r.year), "title": "{" + r.title + "}"}
        if r.kind == "article":
            fields.update(journal=r.venue, volume=r.volume, number=r.issue, pages=r.pages.replace("–", "--"))
        elif r.kind == "book":
            fields["publisher"] = r.venue
        elif r.kind == "chapter":
            fields["booktitle"] = r.venue
        else:
            fields["note"] = r.venue
        if r.doi:
            fields["doi"] = r.doi
        elif r.url:
            fields["url"] = r.url
        body = ",\n".join(f"  {k} = {{{_bib_escape(v)}}}" for k, v in fields.items() if v)
        out.append(f"@{_BIBTEX_TYPES[r.kind]}{{{key},\n{body}\n}}")
    return "\n\n".join(out) + "\n"


BIBTEX_HEADER = "% Generated from causal_lab/utils/references.py; do not edit by hand.\n\n"

if __name__ == "__main__":
    # python utils/references.py > ../docs/references.bib
    import sys
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    print(BIBTEX_HEADER + to_bibtex(), end="")
