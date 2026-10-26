"""Generated scripts for the six Causal Methods, and the DiD script.

The Python scripts whose packages are in requirements.txt (RCT, Matching, IV
and the DiD) are run here and must print Causal Lab's estimate and standard
error. The others (rdrobust, pysyncon, DoubleML) are run when the package is
installed. R scripts were run against R estimatr, Matching, rdrobust, Synth
and DoubleML on 2026-10-25; their measured agreement is what each script's
header states (code_generator.methods.STATUS).
"""
import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code_generator.generator import CodeGenParams, generate_python_code
from code_generator.methods import STATUS, code_options, generate_method_code
from estimators.did import estimate_did
from estimators.registry import WORLDS, run_method, virtual_options
from utils.real_data import load_card_krueger

NEEDS = {"rct": None, "matching": None, "iv": None, "rdd": "rdrobust", "synthetic_control": "pysyncon",
         "dml": "doubleml"}


def _generated(method, lang="en", seed=5):
    world = WORLDS[method]
    df, truth = world.generate(world.config_cls(seed=seed))
    mapping, options = dict(truth["roles"]), virtual_options(method, truth)
    result = run_method(method, df, mapping, options)
    return df, result, mapping, code_options(method, df, mapping, options, result), lang


def _run_python(code: str, df, folder: Path) -> list[float]:
    data = folder / "data.csv"
    df.to_csv(data, index=False)
    script = folder / "script.py"
    script.write_text(code.replace('"data.csv"', f'"{data.as_posix()}"'), encoding="utf-8")
    run = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=900)
    assert run.returncode == 0, run.stderr[-2000:]
    return [float(x) for x in re.findall(r"^[^\n:]{1,60}:\s*(-?\d+\.\d+(?:e-?\d+)?)\s*$", run.stdout, flags=re.M)]


def test_python_scripts_reproduce_causal_lab():
    with tempfile.TemporaryDirectory() as folder:
        for method, package in NEEDS.items():
            if package is not None and importlib.util.find_spec(package) is None:
                print(f"{package} not installed: generated {method} script not run")
                continue
            df, result, mapping, options, lang = _generated(method)
            numbers = _run_python(generate_method_code(method, mapping, options)["python"], df, Path(folder))
            estimate = numbers[-2] if result.se is not None else numbers[-1]
            tolerance = 1e-4 if method == "synthetic_control" else 1e-9
            assert abs(estimate - result.estimate) <= tolerance * abs(result.estimate), (method, numbers, result.estimate)
            if result.se is not None:
                se_tolerance = 1e-4 if method == "rdd" else 1e-9
                assert abs(numbers[-1] - result.se) <= se_tolerance * result.se, (method, numbers, result.se)


def test_did_python_script_reproduces_the_app_standard_error():
    # Before 2026-10-25 the script counted the unit dummies: 1.91 instead of 1.34 on Card & Krueger.
    df = load_card_krueger()
    result = estimate_did(df)
    with tempfile.TemporaryDirectory() as folder:
        numbers = _run_python(generate_python_code(CodeGenParams()), df, Path(folder))
    assert abs(numbers[-2] - result.att) < 1e-9 and abs(numbers[-1] - result.se) < 1e-9, (numbers, result.se)


def test_every_script_uses_the_mapping_and_says_how_close_it_is():
    for method in NEEDS:
        df, result, mapping, options, _ = _generated(method)
        for lang in ("en", "fr"):
            code = generate_method_code(method, mapping, options, data_path="my data.csv", lang=lang)
            for language, text in code.items():
                assert "my data.csv" in text, (method, language)
                assert not re.search(r"np\.(int|float|str_|bool_)\w*\(", text), (method, language)   # NumPy 2 repr
                columns = [c for v in mapping.values() for c in (v if isinstance(v, list) else [v]) if isinstance(c, str)]
                assert all(c in text for c in columns if c != mapping.get("unit") or language != "stata"), \
                    (method, language)
            compile(code["python"], f"{method}.py", "exec")
            header_en = generate_method_code(method, mapping, options)["python"].splitlines()[2]
            expected = {"exact": "same estimate and standard error", "rdd": "agrees to 0.01%",
                        "sc": "within 0.01%"}[STATUS[method][0]]
            assert expected in header_en, (method, header_en)
            assert "Not checked by Causal Lab" in generate_method_code(method, mapping, options)["stata"]
    fr = generate_method_code("rct", *_generated("rct")[2:4], lang="fr")["python"]
    assert "reproduit l'estimation de Causal Lab" in fr


def test_synthetic_control_stata_code_lists_every_pre_period_and_the_encoded_unit():
    df, result, mapping, options, _ = _generated("synthetic_control")
    stata = generate_method_code("synthetic_control", mapping, options)["stata"]
    labels = sorted(str(u) for u in df["unit"].unique())
    assert f"trunit({labels.index(str(options['treated_unit'])) + 1})" in stata
    assert all(f"Y({p})" in stata for p in options["pre_periods"])


def test_covariate_synthetic_control_code_searches_v_and_says_so():
    world = WORLDS["synthetic_control"]
    df, truth = world.generate(world.config_cls(seed=5, n_covariates=2))
    mapping, options = dict(truth["roles"]), virtual_options("synthetic_control", truth)
    result = run_method("synthetic_control", df, mapping, options)
    code = generate_method_code("synthetic_control", mapping,
                                code_options("synthetic_control", df, mapping, options, result))
    assert "importance V is found by a local search" in code["python"] and "custom_V" not in code["python"]
    assert 'predictors = c("X1", "X2")' in code["r"] and "custom.v" not in code["r"]
    assert "synth Y X1 X2 Y, trunit(" in code["stata"]


def test_fuzzy_robust_rdd_code_passes_the_treatment_and_reports_the_robust_row():
    world = WORLDS["rdd"]
    df, truth = world.generate(world.config_cls(seed=5, compliance=0.6))
    mapping = dict(truth["roles"])
    options = {**virtual_options("rdd", truth), "inference": "robust"}
    result = run_method("rdd", df, mapping, options)
    code = generate_method_code("rdd", mapping, code_options("rdd", df, mapping, options, result))
    assert 'fuzzy=df["D"]' in code["python"] and "fit.se.iloc[2, 0]" in code["python"]
    assert "fuzzy = df$D" in code["r"] and "fit$se[3]" in code["r"] and "fuzzy(D)" in code["stata"]
    if importlib.util.find_spec("rdrobust") is not None:
        with tempfile.TemporaryDirectory() as folder:
            numbers = _run_python(code["python"], df, Path(folder))
        assert abs(numbers[-2] - result.estimate) < 1e-9 * abs(result.estimate)
        assert abs(numbers[-1] - result.se) < 1e-9 * result.se          # robust SE, as Causal Lab reports


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_method_code: OK")
