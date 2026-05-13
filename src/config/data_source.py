"""Data source toggle — switches between real-time API and seed data.

Usage:
  from src.config.data_source import get_data_source, set_data_source

  if get_data_source() == "realtime":
      # fetch live data
  else:
      # use seed data
"""

from typing import Literal

DataSourceMode = Literal["realtime", "seed"]

_current_source: DataSourceMode | None = None


def get_data_source() -> DataSourceMode:
    global _current_source
    if _current_source is None:
        from src.config.settings import get_settings
        _current_source = get_settings().data_source or "realtime"
    return _current_source


def set_data_source(mode: DataSourceMode) -> None:
    global _current_source
    _current_source = mode


def toggle_data_source() -> DataSourceMode:
    current = get_data_source()
    new = "seed" if current == "realtime" else "realtime"
    set_data_source(new)
    return new


def is_realtime() -> bool:
    return get_data_source() == "realtime"


def is_seed() -> bool:
    return get_data_source() == "seed"


def get_source_label() -> str:
    if is_realtime():
        return "🤖 AI-Generated Market Data (enriched with live sources)"
    return "🤖 AI-Generated Market Data (pure algorithmic)"


def get_source_badge() -> dict:
    if is_realtime():
        return {"label": "AI", "color": "var(--accent-cyan)", "bg": "rgba(6,182,212,0.15)"}
    return {"label": "SEED", "color": "var(--accent-yellow)", "bg": "rgba(234,179,8,0.15)"}
