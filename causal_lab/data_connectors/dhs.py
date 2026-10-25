"""
DHS Program indicators (api.dhsprogram.com, public, no key).

Returns a long panel: one row per country (or region) and survey year, one
column per indicator. Only each survey's preferred estimate is kept
(IsPreferred = 1): the API also returns, for instance, the under-five
mortality rate over ten years next to the preferred five-year rate.
Subnational regions follow each survey's own boundaries, which change over
time, so a regional panel is usually unbalanced.
"""
from __future__ import annotations

import pandas as pd

from data_connectors.common import get_json
from utils.i18n import LocalizedError

URL = "https://api.dhsprogram.com/rest/dhs/data"
SERVICE = "DHS Program"
PER_PAGE = 1000
COMMON_INDICATORS = {        # id: English label (the DHS API's own names)
    "CM_ECMR_C_U5M": "Under-five mortality rate",
    "CM_ECMR_C_IMR": "Infant mortality rate",
    "CN_NUTS_C_HA2": "Children stunted",
    "CN_NUTS_C_WH2": "Children wasted",
    "CH_VACC_C_BAS": "Children with all basic vaccinations",
    "FE_FRTR_W_TFR": "Total fertility rate",
    "ED_LITR_W_LIT": "Women who are literate",
    "WS_SRCE_H_IMP": "Households with an improved water source",
}


def fetch_dhs_indicators(session, countries: list[str], indicators: list[str],
                         subnational: bool = False) -> pd.DataFrame:
    """countries: DHS country codes (CD, RW...); indicators: DHS indicator ids."""
    if not countries or not indicators:
        raise LocalizedError("err.dhs_needs_choice")
    rows, page, pages = [], 1, 1
    while page <= pages:
        reply = get_json(session, SERVICE, URL, params={
            "indicatorIds": ",".join(indicators), "countryIds": ",".join(countries),
            "breakdown": "subnational" if subnational else "national",
            "f": "json", "perpage": PER_PAGE, "page": page})
        pages = int(reply.get("TotalPages", 1))
        rows.extend(reply.get("Data", []))
        page += 1
    rows = [r for r in rows if r.get("IsPreferred") == 1]
    if subnational:
        rows = [r for r in rows if r.get("CharacteristicCategory", "").lower() == "region"]
    if not rows:
        raise LocalizedError("err.dhs_no_data")
    data = pd.DataFrame(rows)
    data["region"] = data["CharacteristicLabel"].str.lstrip(".").str.strip()
    data["unit"] = (data["CountryName"] + " / " + data["region"]) if subnational else data["CountryName"]
    panel = data.pivot_table(index=["unit", "CountryName", "SurveyYear", "SurveyId"], columns="IndicatorId",
                             values="Value", aggfunc="first").reset_index()
    panel.columns.name = None
    panel = panel.rename(columns={"CountryName": "country", "SurveyYear": "period", "SurveyId": "survey"})
    return panel.sort_values(["unit", "period"]).reset_index(drop=True)
