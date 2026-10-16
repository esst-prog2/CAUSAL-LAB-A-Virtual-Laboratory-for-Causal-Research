"""The calibration spike never overwrites a results file by accident.

Before this fix, `spike/stress_test_calibration.py` run without an argument
wrote to `stress_test_calibration_results.md`, the historical hw4 record,
and replaced it (it happened during the hw6 final verification). Any explicit
name was replaced silently too.

Isolation: every test runs a copy of the script in a temporary folder, next
to a decoy "historical" file, with the 1,200-world simulation replaced by an
instant stand-in. The committed files in spike/ are never touched. Like every
test here, this file also runs as a plain script.
"""
import contextlib
import hashlib
import importlib.util
import inspect
import io
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the script's own imports

SCRIPT = Path(__file__).resolve().parent.parent.parent / "spike" / "stress_test_calibration.py"
HISTORICAL = "stress_test_calibration_results.md"
DECOY = b"# historical hw4 spike result - must never change\n"


def _fake_batch(threat_kwargs, n_reps=200):
    return {name: 0.1 for name in ("Parallel Trends", "Anticipation", "Spillovers",
                                   "Serial Correlation", "Heterogeneous Effects")}, 90.0


@contextlib.contextmanager
def _sandbox(script: Path = SCRIPT):
    """A temporary spike/ folder: a copy of the script and a decoy historical file."""
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        copy = folder / script.name
        shutil.copyfile(script, copy)
        (folder / HISTORICAL).write_bytes(DECOY)
        spec = importlib.util.spec_from_file_location("calibration_under_test", copy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(module, "run_batch", _fake_batch):
            yield module, folder


def _run(module, argv):
    """Run main(argv); return (exit code, stdout, stderr). 0 means it returned normally."""
    out, err = io.StringIO(), io.StringIO()
    # The pre-fix main() read sys.argv itself; supporting it lets the
    # regression test be run against that version to show it fails.
    takes_argv = bool(inspect.signature(module.main).parameters)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err),             patch.object(sys, "argv", [module.__file__, *argv]):
        try:
            module.main(argv) if takes_argv else module.main()
            code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
            err.write("" if isinstance(exc.code, int) else str(exc.code))
    return code, out.getvalue(), err.getvalue()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_no_output_argument_cannot_touch_the_historical_file(script: Path = SCRIPT):
    # The regression test for the original bug: the pre-fix script, run here,
    # replaced the decoy and fails this test (see the PR / PLANNING_LOG).
    with _sandbox(script) as (module, folder):
        before = _digest(folder / HISTORICAL)
        code, out, _ = _run(module, [])
        assert code != 0, "ran without an output path"
        assert "Clean world" not in out, "started the simulation without an output path"
        assert _digest(folder / HISTORICAL) == before


def test_an_existing_file_is_refused_before_computing_and_left_byte_for_byte():
    with _sandbox() as (module, folder):
        before = _digest(folder / HISTORICAL)
        code, out, err = _run(module, [HISTORICAL])
        assert code != 0 and "already exists" in err
        assert "Clean world" not in out                 # refused before the 5-minute computation
        assert _digest(folder / HISTORICAL) == before


def test_a_new_explicit_path_is_written():
    with _sandbox() as (module, folder):
        code, out, _ = _run(module, ["new_results.md"])
        assert code == 0 and "Written to" in out
        text = (folder / "new_results.md").read_text(encoding="utf-8")
        assert "**90.0 / 100**" in text and "| Parallel Trends | 10% | 10% |" in text


def test_replacing_needs_the_overwrite_flag():
    with _sandbox() as (module, folder):
        target = folder / "previous_run.md"
        target.write_text("old run\n", encoding="utf-8")
        code, _, _ = _run(module, ["previous_run.md"])
        assert code != 0 and target.read_text(encoding="utf-8") == "old run\n"
        code, out, _ = _run(module, ["previous_run.md", "--overwrite"])
        assert code == 0 and "**90.0 / 100**" in target.read_text(encoding="utf-8")


def test_invalid_destinations_are_reported_before_computing():
    with _sandbox() as (module, folder):
        (folder / "a_folder").mkdir()
        for argv, fragment in ((["missing_folder/results.md"], "folder does not exist"),
                               (["a_folder"], "is a folder")):
            code, out, err = _run(module, argv)
            assert code != 0 and fragment in err, (argv, err)
            assert "Clean world" not in out


def test_a_write_failure_is_an_error_not_a_success():
    with _sandbox() as (module, folder):
        with patch.object(Path, "open", side_effect=PermissionError("access denied")):
            code, out, err = _run(module, ["new_results.md"])
        assert code != 0 and "NOT saved" in err and "access denied" in err
        assert "Written to" not in out
        assert not (folder / "new_results.md").exists()
        assert (folder / HISTORICAL).read_bytes() == DECOY


def test_a_file_created_during_the_run_is_not_replaced():
    # The destination is checked first and written 5 minutes later; exclusive
    # creation keeps a file that appeared in between.
    with _sandbox() as (module, folder):
        target = folder / "late.md"

        def batch_creating_the_file(*args, **kwargs):
            target.write_text("created meanwhile\n", encoding="utf-8")
            return _fake_batch(*args, **kwargs)
        with patch.object(module, "run_batch", batch_creating_the_file):
            code, out, err = _run(module, ["late.md"])
        assert code != 0 and "NOT saved" in err and "Written to" not in out
        assert target.read_text(encoding="utf-8") == "created meanwhile\n"


if __name__ == "__main__":
    test_no_output_argument_cannot_touch_the_historical_file()
    test_an_existing_file_is_refused_before_computing_and_left_byte_for_byte()
    test_a_new_explicit_path_is_written()
    test_replacing_needs_the_overwrite_flag()
    test_invalid_destinations_are_reported_before_computing()
    test_a_write_failure_is_an_error_not_a_success()
    test_a_file_created_during_the_run_is_not_replaced()
    print("test_calibration_output: OK")
