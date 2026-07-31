"""
HOS Rules Engine — Core trip planning logic.

Implements FMCSA Hours of Service rules for property-carrying drivers
on a 70-hour/8-day cycle with no adverse driving conditions.

Pure Python with no Django dependency so it can be unit-tested in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, timezone
from typing import Optional

# ─── Constants ───────────────────────────────────────────────────────────────
MAX_DRIVING_HOURS = 11.0
MAX_WINDOW_HOURS = 14.0
BREAK_TRIGGER_HOURS = 8.0
BREAK_DURATION_HOURS = 0.5
RESET_DURATION_HOURS = 10.0
CYCLE_LIMIT_HOURS = 70.0
RESTART_DURATION_HOURS = 34.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_STOP_DURATION_HOURS = 0.5
PICKUP_DURATION_HOURS = 1.0
DROPOFF_DURATION_HOURS = 1.0

OFF_DUTY = "OFF_DUTY"
SLEEPER_BERTH = "SLEEPER_BERTH"
DRIVING = "DRIVING"
ON_DUTY_NOT_DRIVING = "ON_DUTY_NOT_DRIVING"


@dataclass
class DutySegment:
    status: str
    start_time: datetime
    end_time: datetime
    location: str
    activity: Optional[str] = None
    stationary: bool = True
    miles: float = 0.0

    @property
    def duration_hours(self) -> float:
        return (self.end_time - self.start_time).total_seconds() / 3600.0


@dataclass
class RouteInfo:
    distance_miles: float
    duration_hours: float
    origin_name: str
    destination_name: str
    avg_speed_mph: float = field(init=False)

    def __post_init__(self):
        self.avg_speed_mph = (self.distance_miles / self.duration_hours) if self.duration_hours > 0 else 60.0


@dataclass
class HOSClock:
    time: datetime
    cycle_used: float
    driving_since_break: float
    driving_since_reset: float
    window_start: datetime
    on_duty: bool = True

    @property
    def window_elapsed(self) -> float:
        return (self.time - self.window_start).total_seconds() / 3600.0

    @property
    def window_remaining(self) -> float:
        return max(0.0, MAX_WINDOW_HOURS - self.window_elapsed)

    @property
    def driving_remaining(self) -> float:
        return max(0.0, MAX_DRIVING_HOURS - self.driving_since_reset)

    @property
    def cycle_remaining(self) -> float:
        return max(0.0, CYCLE_LIMIT_HOURS - self.cycle_used)

    @property
    def until_break(self) -> float:
        return max(0.0, BREAK_TRIGGER_HOURS - self.driving_since_break)


@dataclass
class DailyLogSheet:
    day_index: int
    log_date: date
    total_miles_today: float
    segments: list[dict]
    totals: dict
    recap: dict
