# Copyright (C) 2025  Romolo Politi
from __future__ import annotations

import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

_DURATION_TOKEN_RE = re.compile(r"(\d+)\s*([yMdhms])")
_UNIT_TO_KWARG = {
    "y": "years",
    "M": "months",
    "d": "days",
    "h": "hours",
    "m": "minutes",
    "s": "seconds",
}


def string_to_timedelta(time_str: str) -> relativedelta:
    """Parse legacy duration strings like '1y2M3d4h5m6s'."""
    if time_str is None:
        raise ValueError("Duration cannot be null.")

    raw = str(time_str).strip()
    if not raw:
        raise ValueError("Duration cannot be empty.")
    compact = re.sub(r"\s+", "", raw)

    tokens = _DURATION_TOKEN_RE.findall(compact)
    if not tokens or "".join(f"{value}{unit}" for value, unit in tokens) != compact:
        raise ValueError(
            f"Invalid duration format: {time_str!r}. Expected tokens like '1y2M3d4h5m6s'."
        )

    kwargs: dict[str, int] = {}
    for value, unit in tokens:
        key = _UNIT_TO_KWARG[unit]
        kwargs[key] = kwargs.get(key, 0) + int(value)

    return relativedelta(**kwargs) # type: ignore


def stopCal(start: datetime, durate: str) -> datetime:
    return start + string_to_timedelta(durate)


def day_length(start: datetime, end: datetime) -> int:
    return (end - start).days
