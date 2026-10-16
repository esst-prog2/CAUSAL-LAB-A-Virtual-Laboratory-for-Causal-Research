"""Unsafe inputs and invalid configurations are refused up front (hw6 review 7)."""
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimators.staggered_did import estimate_staggered_did
from simulation_engine.dgp import VirtualWorldConfig, generate
from utils.i18n import LocalizedError

APP_DIR = Path(__file__).resolve().parent.parent
TIMEOUT_S = 30     # a guarded expression is refused in milliseconds; unguarded, 9**9**9 never returns


def _refused(fn, *args, **kwargs) -> str:
    try:
        fn(*args, **kwargs)
    except LocalizedError as exc:
        return str(exc)
    raise AssertionError("expected a LocalizedError")


def test_huge_constants_in_the_model_editor_are_refused_quickly():
    # Before: parse_expression("9**9**9") made sympy compute a 369-million-digit
    # integer, which blocked the whole Streamlit server process. Run in a
    # subprocess so that a regression fails on the timeout instead of hanging.
    code = (
        "import sys; sys.path.insert(0, '.')\n"
        "import sympy as sp\n"
        "from theory_engine.game import parse_expression\n"
        "from utils.i18n import LocalizedError\n"
        "x = sp.Symbol('x')\n"
        "for text in ('9**9**9', 'x**(9**9**9)', '(((10**100)**100)**100)**100', 'exp(9**9**9)'):\n"
        "    try:\n"
        "        parse_expression(text, {'x': x})\n"
        "    except LocalizedError as exc:\n"
        "        assert 'digits' in str(exc), exc\n"
        "    else:\n"
        "        raise SystemExit('accepted ' + text)\n"
        "assert str(parse_expression('10**3*x**2 - 2^3', {'x': x})) == '1000*x**2 - 8'\n"
    )
    done = subprocess.run([sys.executable, "-c", code], cwd=APP_DIR, timeout=TIMEOUT_S,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr or done.stdout


def test_virtual_world_refuses_values_it_used_to_clip_or_crash_on():
    # Before: n_units=1 gave a world without a treated unit, share_treated=1.5
    # was clipped silently, noise_sd=-1 and a misspelt level crashed in numpy
    # or with a bare KeyError.
    for kwargs, fragment in ((dict(n_units=1), "at least 2 units"),
                             (dict(share_treated=1.5), "share_treated"),
                             (dict(share_treated=0.0), "share_treated"),
                             (dict(noise_sd=-1.0), "noise_sd"),
                             (dict(spillovers="huge"), "spillovers = 'huge'")):
        assert fragment in _refused(generate, VirtualWorldConfig(**kwargs)), kwargs
    generate(VirtualWorldConfig(n_units=2, share_treated=0.5))     # the smallest valid world still works


def test_robust_did_refuses_an_unknown_comparison_group():
    # Before: "never-treated" (hyphen) silently ran the not-yet-treated
    # comparison and reported "never-treated".
    df, _ = generate(VirtualWorldConfig(staggered_adoption=True, seed=1))
    assert "never-treated" in _refused(estimate_staggered_did, df, comparison="never-treated")
    assert "at least 2" in _refused(estimate_staggered_did, df, n_bootstrap=1)


if __name__ == "__main__":
    test_huge_constants_in_the_model_editor_are_refused_quickly()
    test_virtual_world_refuses_values_it_used_to_clip_or_crash_on()
    test_robust_did_refuses_an_unknown_comparison_group()
    print("test_config_safety: OK")
