"""
Population by administrative unit and year, from WorldPop.

The administrative boundaries come from geoBoundaries (gbOpen, CC BY 4.0 or
ODbL depending on the country); for each unit and year, WorldPop's zonal
statistics service (dataset wpgppop, 100 m unconstrained population,
2000-2020) returns the total population inside the unit's polygon. One
request per unit and year, about 3 seconds each, a few at a time; the
polygon is sent with POST, because it is too long for a URL.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import pandas as pd

from data_connectors.common import get_json, parse_json, request
from utils.i18n import LocalizedError

GEOBOUNDARIES_URL = "https://www.geoboundaries.org/api/current/gbOpen/{iso3}/{level}/"
STATS_URL = "https://api.worldpop.org/v1/services/stats"
YEARS = range(2000, 2021)
LEVELS = ("ADM0", "ADM1", "ADM2")
PARALLEL_REQUESTS = 4


def fetch_boundaries(session, iso3: str, level: str) -> list[dict]:
    """[{"name": ..., "geometry": ...}] for the units of `iso3` at `level`."""
    if level not in LEVELS:
        raise LocalizedError("err.worldpop_level", level=level, allowed=", ".join(LEVELS))
    meta = get_json(session, "geoBoundaries", GEOBOUNDARIES_URL.format(iso3=iso3.upper(), level=level))
    if not isinstance(meta, dict) or "simplifiedGeometryGeoJSON" not in meta:
        raise LocalizedError("err.worldpop_boundaries", iso3=iso3, level=level)
    shapes = get_json(session, "geoBoundaries", meta["simplifiedGeometryGeoJSON"])
    return [{"name": f["properties"].get("shapeName") or f"unit {i + 1}", "geometry": f["geometry"]}
            for i, f in enumerate(shapes.get("features", []))]


def population(session, geometry: dict, year: int) -> float:
    geojson = json.dumps({"type": "FeatureCollection",
                          "features": [{"type": "Feature", "properties": {}, "geometry": geometry}]})
    text = request(session, "post", "WorldPop", STATS_URL,
                   data={"dataset": "wpgppop", "year": str(year), "geojson": geojson, "runasync": "false"})
    reply = parse_json("WorldPop", text)
    if reply.get("error") or "total_population" not in (reply.get("data") or {}):
        raise LocalizedError("err.worldpop_reply", detail=reply.get("error_message") or "no total_population")
    return float(reply["data"]["total_population"])


def fetch_worldpop_population(session, iso3: str, years: list[int], level: str = "ADM1",
                              progress: Callable[[int, int], None] | None = None) -> pd.DataFrame:
    """Long panel: unit (boundary name), period (year), population."""
    years = sorted(set(int(y) for y in years))
    if not years or any(y not in YEARS for y in years):
        raise LocalizedError("err.worldpop_years", first=YEARS[0], last=YEARS[-1])
    units = fetch_boundaries(session, iso3, level)
    if not units:
        raise LocalizedError("err.worldpop_boundaries", iso3=iso3, level=level)
    jobs = [(u, y) for u in units for y in years]
    done = []

    def run(job):
        unit, year = job
        value = population(session, unit["geometry"], year)
        done.append(1)
        if progress is not None:
            progress(len(done), len(jobs))
        return {"unit": unit["name"], "period": year, "population": value}

    with ThreadPoolExecutor(PARALLEL_REQUESTS) as pool:
        rows = list(pool.map(run, jobs))
    return pd.DataFrame(rows).sort_values(["unit", "period"]).reset_index(drop=True)
