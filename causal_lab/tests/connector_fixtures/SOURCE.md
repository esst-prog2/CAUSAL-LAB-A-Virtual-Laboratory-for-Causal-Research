# Connector test fixtures

These are responses recorded from the live services on 2026-10-25, so the connector tests can run offline. `tests/test_data_connectors.py` replays them.

| File | Request | Source and licence |
|---|---|---|
| `dhs_national.json` | `api.dhsprogram.com/rest/dhs/data?indicatorIds=CM_ECMR_C_U5M,CN_NUTS_C_HA2&countryIds=CD,RW&breakdown=national` | The DHS Program (ICF), public API; DHS terms of use |
| `dhs_subnational.json` | same, `indicatorIds=CM_ECMR_C_U5M&countryIds=RW&breakdown=subnational` | same |
| `geoboundaries_rwa_adm1_meta.json` | `www.geoboundaries.org/api/current/gbOpen/RWA/ADM1/` | geoBoundaries (gbOpen); CC BY 4.0 for Rwanda ADM1 |
| `geoboundaries_rwa_adm1.geojson` | the `simplifiedGeometryGeoJSON` file named in the metadata | same |
| `worldpop_rwa_adm1_raw.json` | `api.worldpop.org/v1/services/stats` (POST, dataset `wpgppop`), for each of the 5 provinces and the years 2010 and 2015; the raw text, PHP notices included, keyed `<province index>_<year>` | WorldPop (University of Southampton); CC BY 4.0 |

ACLED replies are not recorded, because ACLED requires an account. The tests build them from ACLED's API documentation.
