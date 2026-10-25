"""
Connectors to external data sources: DHS indicators, WorldPop population
by administrative unit, and ACLED conflict events.

These are the only parts of Causal Lab that send requests over the network.
They are off until the researcher turns them on in Settings, and each
request carries query parameters only (country codes, indicator ids,
administrative boundaries, years, and the researcher's own ACLED
credentials sent to ACLED); no dataset loaded in Causal Lab is ever sent.
"""
