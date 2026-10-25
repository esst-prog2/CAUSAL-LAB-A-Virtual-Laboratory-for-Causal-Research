## 1. Connectors

- [x] 1.1 Probe the services: DHS and geoBoundaries public; WorldPop public, needs POST; ACLED 403 without an account.
- [x] 1.2 Write the DHS, WorldPop and ACLED connectors, and record fixtures from the live services.

## 2. App

- [x] 2.1 External Data page, Settings toggle (off by default, persistent), CSV download and send-to-method, EN and FR messages.
- [x] 2.2 Run end to end in the app with live DHS; fix the toggle and the RDD inference persistence found by doing so.

## 3. Verification

- [x] 3.1 Offline tests, live test, mutants.
- [x] 3.2 Validate with `openspec validate external-data-connectors --strict`.
