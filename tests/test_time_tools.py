from datetime import datetime

import pytest

from gantty.time_tools import day_length, stopCal, string_to_timedelta


def test_string_to_timedelta_parses_full_duration():
    delta = string_to_timedelta("1y2M3d4h5m6s")
    assert delta.years == 1
    assert delta.months == 2
    assert delta.days == 3
    assert delta.hours == 4
    assert delta.minutes == 5
    assert delta.seconds == 6


def test_string_to_timedelta_accepts_spaces_and_duplicate_units():
    delta = string_to_timedelta("1d 2d 30m")
    assert delta.days == 3
    assert delta.minutes == 30


@pytest.mark.parametrize("value", [None, "", "   ", "foo", "1q", "1d-2h"])
def test_string_to_timedelta_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        string_to_timedelta(value)


def test_stopCal_uses_calendar_aware_month_math():
    start = datetime(2025, 1, 31)
    assert stopCal(start, "1M") == datetime(2025, 2, 28)


def test_day_length_returns_days_difference():
    assert day_length(datetime(2025, 1, 1), datetime(2025, 1, 10)) == 9
