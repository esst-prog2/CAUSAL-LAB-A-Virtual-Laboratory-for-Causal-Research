## Why

README section 3 listed "Connectors to external data sources (DHS, ACLED, WorldPop, etc.)" under "Not this term". On 2026-10-25 the user decided to build them anyway, with the other excluded features. They are the first part of Causal Lab that uses the network, so the app's promise ("your data remain local", "no data is sent anywhere") needs an explicit opt-in.

## What Changes

New package `causal_lab/data_connectors/`:
- `dhs`: public API, preferred estimates, national or regional;
- `worldpop`: geoBoundaries polygons plus WorldPop zonal statistics by POST, four requests at a time;
- `acled`: OAuth password grant, paged reads, aggregation with zeros;
- `common`: HTTP errors per service and JSON extraction.

UI:
- a new External Data page, after Virtual Lab;
- a Settings toggle, off by default;
- a CSV download and "Send to Causal Methods" for each fetched dataset.

Also:
- the build note says the optional connectors send only query parameters;
- recorded live responses in `tests/connector_fixtures`, with their sources and licences.

No new dependency: requests ships with Streamlit.

## Capabilities

### New Capabilities
- `data-connectors`

### Modified Capabilities
(none)

## Impact

**Checked live:**
- DHS: RDC and Rwanda under-five mortality, national and 22 Rwandan regions;
- WorldPop: Rwanda's provinces, 10 requests in 58 s.

**ACLED:** written to its documented API but not run against it (no account); the page says so.

**Found by running the app:** Streamlit drops a widget's key when its page is left. That reset the connectors toggle and would have reset the RDD inference choice; both now keep their state outside the widget, and regression tests cover them.

**Tests:**
- new `tests/test_data_connectors.py`, offline, plus a live test under `CAUSAL_LAB_LIVE=1`;
- 5 mutants caught; one (non-preferred DHS rows) first survived, which led to a test where the non-preferred row comes first.
