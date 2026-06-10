"""Inbound adapters: external systems → EventBus."""

from beacon.adapters.inbound.matrix import MatrixAdapter

__all__ = ["MatrixAdapter"]
