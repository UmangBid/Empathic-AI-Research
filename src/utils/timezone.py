"""
Timezone utilities for consistent Arizona (America/Phoenix) time rendering.

We store timestamps in UTC in the database. These helpers convert and format
those datetimes for display/export in Arizona time (Mountain Time without DST).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    _PHOENIX = ZoneInfo("America/Phoenix")
except Exception:  # pragma: no cover - fallback for environments without zoneinfo
    _PHOENIX = None

try:
    # Fallback via dateutil if available
    from dateutil import tz  # type: ignore
    _PHOENIX_DU = tz.gettz("America/Phoenix")
except Exception:  # pragma: no cover
    _PHOENIX_DU = None


def _to_phoenix(dt_utc: datetime) -> datetime:
    """Convert a UTC datetime to America/Phoenix tz-aware datetime.

    - Treat naive datetimes as UTC.
    - If zoneinfo is available, use it; otherwise fallback to dateutil tz.
    """
    if dt_utc is None:
        return None  # type: ignore

    # Normalize to aware UTC
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)

    if _PHOENIX is not None:
        return dt_utc.astimezone(_PHOENIX)
    if _PHOENIX_DU is not None:
        return dt_utc.astimezone(_PHOENIX_DU)
    # As a last resort, return UTC (shouldn't happen in normal envs)
    return dt_utc


def fmt_az(dt_utc: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a UTC datetime as Arizona local time string.

    Returns empty string if dt is None.
    """
    if not dt_utc:
        return ""
    return _to_phoenix(dt_utc).strftime(fmt)


def now_az() -> datetime:
    """Current time in Arizona timezone as tz-aware datetime."""
    dt_utc = datetime.now(timezone.utc)
    return _to_phoenix(dt_utc)
