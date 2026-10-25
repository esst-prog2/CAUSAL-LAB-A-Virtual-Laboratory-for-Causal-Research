"""
Report of a Causal Lab project, as a format-neutral list of blocks.

`build_report` runs the same engines as the app pages on the session's data
(DiD, event study, Callaway & Sant'Anna, stress test, robustness battery,
code generation) and collects the Causal Methods results already computed,
in the interface language. `report_engine.render` turns the blocks into
Markdown, LaTeX, Word or PDF. No number is typed here: every value comes from
an engine, as in the app.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from code_generator.generator import CodeGenParams, generate_all
from estimators.did import estimate_did
from estimators.event_study import estimate_event_study
from estimators.staggered_did import estimate_staggered_did
from robustness_engine.robustness import run_robustness_battery
from robustness_engine.stress_test import run_stress_test
from utils import session_data
from utils.i18n import LocalizedError, render, t, tf

DESIGN_FIELDS = (            # (wizard label key, ResearchDesignInput field, option values translated?)
    ("wizard.treatment_type", "treatment_type", True),
    ("wizard.treatment_timing", "treatment_timing", True),
    ("wizard.assignment_mechanism", "assignment_mechanism", True),
    ("wizard.outcome_type", "outcome_type", True),
    ("wizard.unit_of_analysis", "unit_of_analysis", True),
    ("wizard.data_structure", "data_structure", True),
    ("wizard.spatial", "has_spatial_component", False),
    ("wizard.has_pre", "has_pre_treatment_periods", False),
    ("wizard.n_pre", "n_pre_periods", False),
    ("wizard.n_post", "n_post_periods", False),
)
THREATS = ("confounding", "spillovers", "serial_correlation", "treatment_heterogeneity",
           "differential_trend", "anticipation", "dynamic_effects")


@dataclass
class Heading:
    text: str
    level: int = 1                 # 1 = section, 2 = subsection


@dataclass
class Paragraph:
    text: str
    emphasis: bool = False         # a note or caveat, shown in italics


@dataclass
class Table:
    columns: list[str]
    rows: list[list[str]]


@dataclass
class Code:
    text: str
    language: str


@dataclass
class Report:
    title: str
    subtitle: str
    lang: str
    blocks: list = field(default_factory=list)


def _num(value, digits: int = 4) -> str:
    return "—" if value is None or value != value else f"{value:.{digits}f}"


def build_report(state, lang: str, now: datetime | None = None) -> Report:
    L = lambda key: t(key, lang)                                    # noqa: E731
    F = lambda key, **params: tf(key, lang, **params)               # noqa: E731
    R = lambda msg: render(msg, lang)                               # noqa: E731
    yes_no = lambda flag: L("common.yes") if flag else L("common.no")   # noqa: E731
    colon = " : " if lang == "fr" else ": "            # French puts a space before the colon

    now = now or datetime.now()
    report = Report(title=L("report.doc_title"), lang=lang,
                    subtitle=F("report.generated_on", date=now.strftime("%Y-%m-%d %H:%M")))
    add = report.blocks.append

    # 1. Research question and design
    design = state.get("design")
    add(Heading(L("report.section.question")))
    if design is not None and design.research_question:
        add(Paragraph(design.research_question))
    else:
        add(Paragraph(L("report.no_question"), emphasis=True))
    if design is not None:
        rows = []
        for label, attr, option in DESIGN_FIELDS:
            value = getattr(design, attr)
            shown = L(f"opt.{value}") if option else (yes_no(value) if isinstance(value, bool) else str(value))
            rows.append([L(label), shown])
        add(Table([L("report.col.item"), L("report.col.value")], rows))

    # 2. Diagnosis and recommendation
    diagnosis, recs = state.get("diagnosis"), state.get("recommendations")
    add(Heading(L("diagnosis.title")))
    if diagnosis is None:
        add(Paragraph(L("diagnosis.empty"), emphasis=True))
    else:
        add(Table([L("report.col.dimension"), L("report.col.level")],
                  [[L(f"diagnosis.dim.{slug}"), L(f"level.{level.value}")] for slug, level in diagnosis.as_rows()]))
        for note in diagnosis.notes:
            add(Paragraph(R(note)))
    if recs:
        best = recs[0]
        add(Heading(L("recommendation.title"), 2))
        add(Paragraph(f"{L('recommendation.primary_method')}{colon}{L(f'method.{best.key}')} "
                      f"({L('recommendation.confidence')}{colon}{L(f'level.{best.confidence}')})"))
        for note in best.rationale:
            add(Paragraph("— " + R(note)))
        add(Paragraph(f"{L('recommendation.main_assumption')}{colon}{R(best.main_assumption)}"))
        add(Paragraph(f"{L('recommendation.main_concern')}{colon}{R(best.main_concern)}"))
        add(Table([L("report.col.method"), L("recommendation.score"), L("recommendation.confidence")],
                  [[L(f"method.{r.key}"), f"{r.overall:.0f}/100", L(f"level.{r.confidence}")] for r in recs]))
        add(Paragraph(L("recommendation.disclaimer"), emphasis=True))

    # 3. Data
    df = session_data.active_data(state)
    add(Heading(L("report.section.data")))
    if df is None:
        add(Paragraph(L("common.no_dataset"), emphasis=True))
    else:
        truth = session_data.virtual_truth(state)
        treatment_period, staggered = session_data.treatment_setup(state, df)
        if state.get("uploaded_df") is None:
            add(Paragraph(L("report.data.virtual")))
        elif state.get("uploaded_file_id") == "card_krueger_1994":
            add(Paragraph(L("report.data.card_krueger")))
        else:
            add(Paragraph(L("report.data.uploaded")))
        add(Table([L("report.col.item"), L("report.col.value")], [
            [L("report.rows"), str(len(df))],
            [L("report.units"), str(df["unit"].nunique())],
            [L("report.periods"), str(df["period"].nunique())],
            [L("virtual.treatment_period"), str(treatment_period)],
            [L("threat.staggered_adoption"), yes_no(staggered)],
        ]))
        cfg = state.get("virtual_cfg") if truth is not None else None
        if cfg is not None:
            add(Heading(L("virtual.threats"), 2))
            add(Table([L("report.col.item"), L("report.col.value")],
                      [[L("virtual.true_att"), _num(cfg.true_att)], [L("virtual.noise"), _num(cfg.noise_sd, 2)],
                       [L("virtual.share_treated"), _num(cfg.share_treated, 2)], [L("common.seed"), str(cfg.seed)]]
                      + [[L(f"threat.{k}"), L(f"intensity.{getattr(cfg, k)}")] for k in THREATS]))

        # 4. Estimation
        add(Heading(L("estimation.title")))
        try:
            did = estimate_did(df)
        except LocalizedError as exc:
            add(Paragraph(R(exc.msg), emphasis=True))
            did = None
        if did is not None:
            rows = [[L("common.estimated_att"), _num(did.att)], [L("estimation.cluster_se"), _num(did.se)],
                    [L("common.ci95"), f"[{_num(did.ci_low, 3)}, {_num(did.ci_high, 3)}]"],
                    ["p", _num(did.p_value)], ["N", str(did.n_obs)]]
            if truth is not None:
                rows += [[L("common.true_att"), _num(truth["true_att"])],
                         [L("common.bias"), f"{did.att - truth['true_att']:+.4f}"]]
            add(Heading(L("method.did"), 2))
            add(Table([L("report.col.item"), L("report.col.value")], rows))
            if staggered:
                add(Paragraph(L("estimation.staggered_warning"), emphasis=True))

        es = estimate_event_study(df, fixed_treatment_period=None if staggered else treatment_period)
        add(Heading(L("event_study.title"), 2))
        add(Table([L("event_study.x_axis"), L("common.estimate"), L("common.se"), L("common.ci95")],
                  [[str(int(r.rel_period)), _num(r.estimate), _num(r.se), f"[{_num(r.ci_low, 3)}, {_num(r.ci_high, 3)}]"]
                   for r in es.coefficients.itertuples()]))
        add(Paragraph(L("event_study.caption"), emphasis=True))

        if staggered:
            add(Heading(L("staggered.tab"), 2))
            try:
                cs = estimate_staggered_did(df)
            except LocalizedError as exc:
                add(Paragraph(R(exc.msg), emphasis=True))
            else:
                add(Table([L("staggered.col.estimator"), "ATT", L("common.se")],
                          [[L("staggered.cs"), _num(cs.att), _num(cs.se)]]
                          + ([[L("staggered.twfe"), _num(did.att), _num(did.se)]] if did is not None else [])
                          + ([[L("common.true_att"), _num(truth["true_att"]), ""]] if truth is not None else [])))
                add(Paragraph(F("staggered.details", cohorts=cs.n_cohorts, units=cs.n_units,
                                comparison=L(f"staggered.comparison.{cs.comparison}"))))

        # 5. Break My Design and robustness
        neighbourhood = session_data.ids_encode_neighbourhood(state)
        stress = run_stress_test(df, treatment_period=treatment_period, ids_encode_neighbourhood=neighbourhood)
        add(Heading(L("break.title")))
        add(Table([L("report.col.check"), L("report.col.verdict"), L("report.col.detail")],
                  [[L(f"check.{c.slug}"), L(f"verdict.{c.verdict}"), R(c.message)] for c in stress.checks]))
        if stress.identification_strength is None:
            add(Paragraph(L("break.no_score")))
        else:
            add(Paragraph(f"{L('break.strength')}{colon}{stress.identification_strength:.0f} / 100 — "
                          + F("break.score_basis", k=stress.n_computable, n=len(stress.checks))))
        add(Paragraph(L("break.disclaimer"), emphasis=True))

        battery = run_robustness_battery(df, treatment_period=treatment_period,
                                         ids_encode_neighbourhood=neighbourhood)
        add(Heading(L("robustness.title")))
        add(Table([L("robustness.col.specification"), "ATT", L("common.se"), "N", L("robustness.col.note")],
                  [[R(r.specification), _num(r.att), _num(r.se), str(r.n_obs), R(r.note)] for r in battery]))
        if not neighbourhood:
            add(Paragraph(L("robustness.adjacent_na"), emphasis=True))

    # 6. Causal Methods results computed on that page
    methods = [(m, d) for m, d in (state.get("method_data") or {}).items() if d.get("result") is not None]
    if methods:
        add(Heading(L("methods.title")))
        for method, data in methods:
            result = data["result"]
            add(Heading(L(f"method.{result.key}"), 2))
            rows = [[L("methods.estimate_of"), R(result.estimand)], [L("common.estimate"), _num(result.estimate)],
                    [L("methods.std_error"), _num(result.se)],
                    [L("common.ci95"), f"[{_num(result.ci_low, 3)}, {_num(result.ci_high, 3)}]"
                     if result.ci_low is not None else "—"],
                    ["p", _num(result.p_value)], ["N", str(result.n_obs)]]
            if data.get("source") == "virtual" and data.get("truth"):
                rows += [[L("methods.true_effect"), _num(data["truth"]["true_effect"])],
                         [L("common.bias"), f"{result.estimate - data['truth']['true_effect']:+.4f}"]]
            add(Table([L("report.col.item"), L("report.col.value")], rows))
            for line in result.summary_lines[1:]:
                add(Paragraph(R(line)))
            for warning in result.warnings:
                add(Paragraph(R(warning), emphasis=True))

    # 7. Reproducible code
    add(Heading(L("report.section.code")))
    add(Paragraph(L("report.code_intro")))
    for language, code in generate_all(CodeGenParams(), lang).items():
        add(Heading({"python": "Python", "r": "R", "stata": "Stata"}[language], 2))
        add(Code(code, language))

    add(Paragraph(L("report.footer"), emphasis=True))
    return report
