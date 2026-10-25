"""
Saving and reopening a Causal Lab project.

A project file (``.causallab``) is a zip archive holding:

    manifest.json            format, version, language, current page, the
                             research design, the Virtual Lab settings, the
                             ground truth and the column mappings
    data/<name>.parquet      each dataset: the Virtual World, the uploaded
                             data, the data of each Causal Methods page

Parquet keeps every value and dtype exactly (pyarrow ships with Streamlit).
Nothing is pickled, so opening a file cannot run code, and the file only
ever goes from the browser to this machine and back ("your data remain
local"). Results are not stored: the diagnosis and recommendations are
recomputed from the design on opening, estimates are re-run with one click.
The Theoretical Model page is not saved (version 1).
"""
from __future__ import annotations

import io
import json
import zipfile
from dataclasses import asdict, fields
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from causal_engine.diagnosis import ResearchDesignInput
from simulation_engine.dgp import VirtualWorldConfig
from utils.i18n import LocalizedError, Msg

FORMAT = "causal-lab-project"
VERSION = 1
EXTENSION = ".causallab"
MAX_UNCOMPRESSED_BYTES = 1_000_000_000      # refuse archives that unpack to more than 1 GB
METHOD_FIELDS = ("truth", "mapping", "options", "source", "dropped", "file_id", "config")


# --------------------------------------------------------------------------
# JSON encoding of the few non-JSON values in the state
# --------------------------------------------------------------------------
def _encode(value):
    if isinstance(value, Msg):
        return {"__msg__": value.key, "params": {k: _encode(v) for k, v in value.params.items()}}
    if isinstance(value, dict):
        if all(isinstance(k, str) for k in value):
            return {k: _encode(v) for k, v in value.items()}
        # JSON object keys are strings: keep non-string keys (unit ids) as pairs.
        return {"__items__": [[_encode(k), _encode(v)] for k, v in value.items()]}
    if isinstance(value, (list, tuple)):
        return [_encode(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_encode(v) for v in value.tolist()]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot save a value of type {type(value).__name__}")


def _decode(value):
    if isinstance(value, dict):
        if set(value) == {"__msg__", "params"}:
            return Msg(value["__msg__"], **{k: _decode(v) for k, v in value["params"].items()})
        if set(value) == {"__items__"}:
            return {_decode(k): _decode(v) for k, v in value["__items__"]}
        return {k: _decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_decode(v) for v in value]
    return value


def _dataclass_from(cls, data: dict | None):
    """Rebuild a settings dataclass from saved fields, keeping the default for
    a field the file lacks and ignoring fields this version does not know."""
    if data is None:
        return None
    if not isinstance(data, dict):
        raise LocalizedError("err.project_invalid", detail=cls.__name__)
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


def _parquet(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Save
# --------------------------------------------------------------------------
def save_project(state) -> bytes:
    """The project file for a Streamlit session state (or any mapping with
    the same keys), as bytes ready for a download button."""
    get = state.get
    datasets: dict[str, pd.DataFrame] = {}
    manifest = {
        "format": FORMAT,
        "version": VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lang": get("lang", "en"),
        "page": get("page", "dashboard"),
        "design": asdict(get("design") or ResearchDesignInput()),
        "diagnosed": get("diagnosis") is not None,
        "vw_config": asdict(get("vw_config") or VirtualWorldConfig()),
        "virtual": None,
        "uploaded": None,
        "methods": {},
    }
    if get("virtual_df") is not None:
        datasets["virtual"] = get("virtual_df")
        cfg = get("virtual_cfg")
        manifest["virtual"] = {"config": asdict(cfg) if cfg is not None else None,
                               "truth": _encode(get("virtual_truth"))}
    if get("uploaded_df") is not None:
        datasets["uploaded"] = get("uploaded_df")
        manifest["uploaded"] = {"file_id": get("uploaded_file_id")}
    for method, data in (get("method_data") or {}).items():
        if data.get("df") is None:
            continue
        datasets[f"method_{method}"] = data["df"]
        manifest["methods"][method] = {k: _encode(data.get(k)) for k in METHOD_FIELDS}

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for name, df in datasets.items():
            archive.writestr(f"data/{name}.parquet", _parquet(df))
    return buffer.getvalue()


def project_file_name(state) -> str:
    """A file name from the research question, else a timestamp."""
    design = state.get("design")
    question = (design.research_question if design is not None else "") or ""
    stem = "".join(c if c.isalnum() else "_" for c in question.strip()[:40]).strip("_")
    return (stem or "causal_lab_" + datetime.now().strftime("%Y%m%d_%H%M")) + EXTENSION


# --------------------------------------------------------------------------
# Open
# --------------------------------------------------------------------------
def load_project(content: bytes) -> dict:
    """The session-state values stored in a project file. Raises
    LocalizedError on anything that is not a valid project file of a version
    this code can read."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise LocalizedError("err.project_not_a_project") from None
    with archive:
        names = set(archive.namelist())
        if "manifest.json" not in names:
            raise LocalizedError("err.project_not_a_project")
        if sum(info.file_size for info in archive.infolist()) > MAX_UNCOMPRESSED_BYTES:
            raise LocalizedError("err.project_too_large", limit_mb=MAX_UNCOMPRESSED_BYTES // 1_000_000)
        try:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocalizedError("err.project_invalid", detail=f"manifest.json: {exc}") from None
        if not isinstance(manifest, dict) or manifest.get("format") != FORMAT:
            raise LocalizedError("err.project_not_a_project")
        version = manifest.get("version")
        if not isinstance(version, int) or version > VERSION:
            raise LocalizedError("err.project_newer_version", version=version, supported=VERSION)

        def dataset(name: str) -> pd.DataFrame:
            member = f"data/{name}.parquet"
            if member not in names:
                raise LocalizedError("err.project_invalid", detail=member)
            try:
                return pd.read_parquet(io.BytesIO(archive.read(member)))
            except Exception as exc:       # pyarrow raises several types for a damaged file
                raise LocalizedError("err.project_invalid", detail=f"{member}: {exc}") from None

        state = {
            "lang": manifest.get("lang") if manifest.get("lang") in ("en", "fr") else "en",
            "page": manifest.get("page", "dashboard"),
            "design": _dataclass_from(ResearchDesignInput, manifest.get("design")) or ResearchDesignInput(),
            "diagnosed": bool(manifest.get("diagnosed")),
            "vw_config": _dataclass_from(VirtualWorldConfig, manifest.get("vw_config")) or VirtualWorldConfig(),
            "virtual_df": None, "virtual_truth": None, "virtual_cfg": None,
            "uploaded_df": None, "uploaded_file_id": None,
            "method_data": {},
        }
        if manifest.get("virtual"):
            state["virtual_df"] = dataset("virtual")
            state["virtual_truth"] = _decode(manifest["virtual"].get("truth"))
            state["virtual_cfg"] = _dataclass_from(VirtualWorldConfig, manifest["virtual"].get("config"))
        if manifest.get("uploaded"):
            state["uploaded_df"] = dataset("uploaded")
            state["uploaded_file_id"] = manifest["uploaded"].get("file_id")
        for method, data in (manifest.get("methods") or {}).items():
            entry = {k: _decode(data.get(k)) for k in METHOD_FIELDS}
            entry.update(df=dataset(f"method_{method}"), result=None, error=None)
            entry["options"] = entry["options"] or {}
            state["method_data"][method] = entry
    return state


def apply_project(session, state: dict) -> None:
    """Replace the session's project by an opened one (`state` from
    load_project), recomputing the diagnosis and recommendations if the saved
    project had them. Everything else in the session (widget states) stays."""
    from causal_engine.diagnosis import diagnose
    from causal_engine.recommendation import recommend

    state = dict(state)
    diagnosed = state.pop("diagnosed")
    for key, value in state.items():
        session[key] = value
    session["diagnosis"] = diagnose(state["design"]) if diagnosed else None
    session["recommendations"] = recommend(state["design"], session["diagnosis"]) if diagnosed else None
