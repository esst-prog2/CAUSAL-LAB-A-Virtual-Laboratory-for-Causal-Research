"""
What a reader needs to reproduce or cite a Causal Lab analysis: the app's
version and repository, how to cite it, and the versions of the Python
packages that computed the numbers. CITATION.cff at the repository root
gives the same citation in the Citation File Format.
"""
from __future__ import annotations

import platform
from importlib import metadata

APP_NAME = "Causal Lab: A virtual laboratory for causal research"
APP_VERSION = "0.1"
APP_AUTHOR = "Barhame, T. Z."
APP_YEAR = 2026
REPOSITORY = "https://github.com/esst-prog2/CAUSAL-LAB-A-Virtual-Laboratory-for-Causal-Research"

# The packages in requirements.txt that compute or render results.
PACKAGES = ("numpy", "pandas", "scipy", "statsmodels", "linearmodels", "scikit-learn", "sympy", "streamlit")


def citation() -> str:
    """APA 7 citation of the software."""
    return f"{APP_AUTHOR} ({APP_YEAR}). {APP_NAME} (Version {APP_VERSION}) [Computer software]. {REPOSITORY}"


def software_versions() -> list[tuple[str, str]]:
    """(name, version) of Python and of each package, as installed."""
    rows = [("Python", platform.python_version())]
    for name in PACKAGES:
        try:
            rows.append((name, metadata.version(name)))
        except metadata.PackageNotFoundError:
            rows.append((name, "—"))
    return rows
