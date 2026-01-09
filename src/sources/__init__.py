"""
Data Sources Package

All source implementations should follow the BaseSource pattern
to ensure consistency and extensibility.
"""

from .base_source import BaseSource
from .warehouse_source import WarehouseSource
from .logistics_source import LogisticsSource

__all__ = ["BaseSource", "WarehouseSource", "LogisticsSource"]