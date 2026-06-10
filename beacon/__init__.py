"""Beacon: Transport-agnostic reactive LLM interface layer."""

try:
    from beacon._version import version as __version__
except Exception:  # pragma: no cover - fallback for source tree without generated version file
    __version__ = "0+unknown"
