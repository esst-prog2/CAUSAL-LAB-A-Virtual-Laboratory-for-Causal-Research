"""Every translation key the code can ask for exists in English and
French, with the same placeholders (README section 4: switching to FR
redraws every page's text in French)."""
import json
import re
import string
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
EN = json.loads((ROOT / "locales" / "en.json").read_text(encoding="utf-8"))
FR = json.loads((ROOT / "locales" / "fr.json").read_text(encoding="utf-8"))

STATIC_CALL = re.compile(r"""\b(?:L|F|t|tf|Msg|LocalizedError|CalibrationError)\(\s*"([a-z_][\w.\- ]*)\"""")


def _fields(template: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(template) if f}


def test_same_keys_and_placeholders():
    assert set(EN) == set(FR), sorted(set(EN) ^ set(FR))
    mismatched = [k for k in EN if _fields(EN[k]) != _fields(FR[k])]
    assert not mismatched, mismatched


def test_every_static_key_in_code_exists():
    missing = set()
    for path in ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        for key in STATIC_CALL.findall(path.read_text(encoding="utf-8")):
            if "." in key and key not in EN:
                missing.add(f"{path.name}: {key}")
    assert not missing, sorted(missing)


def test_dynamic_key_families_exist():
    from causal_engine.diagnosis import ResearchDesignInput, diagnose
    from causal_engine.recommendation import component_slug, recommend
    from robustness_engine.stress_test import CHECK_SLUGS
    from simulation_engine.dgp import VirtualWorldConfig
    from theory_engine.calibration import STATISTICS
    from ui.methods_page import METHODS

    expected = set()
    pages = ["dashboard", "research_question", "diagnosis", "recommendation", "virtual_lab", "estimation",
             "methods", "theory", "break_my_design", "robustness", "code", "settings"]
    expected |= {f"nav.{p}" for p in pages}
    expected |= {f"check.{s}" for s in CHECK_SLUGS.values()}
    expected |= {f"verdict.{v}" for v in ("PASS", "WARNING")}
    expected |= {f"assessment.{a}" for a in ("plausible", "questionable", "violated")}
    expected |= {f"level.{lv}" for lv in ("LOW", "MEDIUM", "HIGH", "UNKNOWN")}
    expected |= {f"intensity.{i}" for i in ("none", "low", "medium", "high", "severe")}
    expected |= {f"stat.{s}" for s in STATISTICS} | {"coef.slope", "coef.intercept"}
    expected |= {f"structure.{s}" for s in ("cross-section", "panel", "repeated cross-section", "time series")}
    expected |= {f"threat.{f}" for f in ("confounding", "spillovers", "serial_correlation", "treatment_heterogeneity",
                                         "differential_trend", "anticipation", "staggered_adoption")}
    for method, spec in METHODS.items():
        expected |= {f"method.{method}", f"methods.assumption.{method}"}
        expected |= {f"mparam.{method}.{p.field}" for p in spec.params}
    options = {
        "treatment_type": ["binary", "continuous", "multiple"],
        "treatment_timing": ["single_date", "staggered", "continuous_time"],
        "assignment_mechanism": ["random", "policy", "geographic", "self_selected", "threshold"],
        "outcome_type": ["continuous", "binary", "count", "survival", "categorical"],
        "unit_of_analysis": ["individual", "household", "firm", "municipality", "territory", "district", "country",
                             "region", "spatial_cell", "time_series"],
        "data_structure": ["cross_section", "panel", "repeated_cross_section", "time_series", "spatial",
                           "spatio_temporal_panel", "experimental", "survey", "administrative"],
    }
    expected |= {f"opt.{o}" for values in options.values() for o in values}
    # recommendation components and method keys for several designs
    for mech in options["assignment_mechanism"]:
        for timing in options["treatment_timing"]:
            design = ResearchDesignInput(assignment_mechanism=mech, treatment_timing=timing)
            diag = diagnose(design)
            expected |= {f"diagnosis.dim.{slug}" for slug, _ in diag.as_rows()}
            for score in recommend(design, diag):
                expected.add(f"method.{score.key}")
                expected |= {f"rec.component.{component_slug(c)}" for c in score.components}
    assert VirtualWorldConfig  # imported for the threat field names above
    missing = sorted(k for k in expected if k not in EN)
    assert not missing, missing


def test_engine_messages_render_in_french():
    from causal_engine.diagnosis import ResearchDesignInput, diagnose
    from causal_engine.recommendation import recommend
    from robustness_engine.stress_test import run_stress_test
    from simulation_engine.dgp import VirtualWorldConfig, generate
    from theory_engine.catalogue import CATALOGUE, build

    df, _ = generate(VirtualWorldConfig(n_units=60, seed=1, spillovers="high"))
    report = run_stress_test(df, treatment_period=10)
    design = ResearchDesignInput(research_question="effect on neighboring territories", treatment_timing="staggered")
    diag = diagnose(design)
    messages = [c.message for c in report.checks] + list(diag.notes)
    for score in recommend(design, diag):
        messages += [*score.rationale, score.main_assumption, score.main_concern]
    for key, entry in CATALOGUE.items():
        game = build(key, entry.n_range[0] if entry.n_range else None)
        messages += [game.name, game.description, *game.parameter_info.values(), *game.outcomes,
                     *[a.name for a in game.agents]]
    for m in messages:
        fr = m.render("fr")
        assert fr and fr != m.key, m.key
        if EN[m.key] != FR[m.key]:
            assert fr != str(m), m.key          # actually translated


if __name__ == "__main__":
    test_same_keys_and_placeholders()
    test_every_static_key_in_code_exists()
    test_dynamic_key_families_exist()
    test_engine_messages_render_in_french()
    print("test_i18n_coverage: OK")
