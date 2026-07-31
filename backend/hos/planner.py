"""
HOS Engine — Planning functions and daily log splitting.
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional

from .engine import (
    DutySegment, RouteInfo, HOSClock, DailyLogSheet,
    OFF_DUTY, SLEEPER_BERTH, DRIVING, ON_DUTY_NOT_DRIVING,
    MAX_DRIVING_HOURS, MAX_WINDOW_HOURS, BREAK_TRIGGER_HOURS,
    BREAK_DURATION_HOURS, RESET_DURATION_HOURS, CYCLE_LIMIT_HOURS,
    RESTART_DURATION_HOURS, FUEL_INTERVAL_MILES, FUEL_STOP_DURATION_HOURS,
    PICKUP_DURATION_HOURS, DROPOFF_DURATION_HOURS,
)


def plan_trip(
    current_loc_name: str, pickup_loc_name: str, dropoff_loc_name: str,
    leg1_distance_mi: float, leg1_duration_hr: float,
    leg2_distance_mi: float, leg2_duration_hr: float,
    cycle_used_hrs: float, trip_start: Optional[datetime] = None,
) -> list[DailyLogSheet]:
    if trip_start is None:
        trip_start = datetime.now(timezone.utc)

    leg1 = RouteInfo(leg1_distance_mi, leg1_duration_hr, current_loc_name, pickup_loc_name)
    leg2 = RouteInfo(leg2_distance_mi, leg2_duration_hr, pickup_loc_name, dropoff_loc_name)

    clock = HOSClock(
        time=trip_start, cycle_used=cycle_used_hrs,
        driving_since_break=0.0, driving_since_reset=0.0,
        window_start=trip_start, on_duty=True,
    )
    segments: list[DutySegment] = []

    # Pre-trip inspection (15 min)
    _add_segment(segments, clock, ON_DUTY_NOT_DRIVING, 0.25,
                 current_loc_name, "Pre-trip inspection")

    miles_since_fuel = 0.0

    # Drive leg 1
    miles_since_fuel = _process_drive(clock, segments, leg1, miles_since_fuel)

    # Pickup
    _process_duty(clock, segments, PICKUP_DURATION_HOURS, pickup_loc_name, "Pickup")

    # Drive leg 2
    miles_since_fuel = _process_drive(clock, segments, leg2, miles_since_fuel)

    # Dropoff
    _process_duty(clock, segments, DROPOFF_DURATION_HOURS, dropoff_loc_name, "Dropoff")

    return split_schedule_into_daily_logs(segments, trip_start)


def _add_segment(segments, clock, status, hours, location, activity=None):
    is_driving = (status == DRIVING)
    seg = DutySegment(
        status=status, start_time=clock.time,
        end_time=clock.time + timedelta(hours=hours),
        location=location, activity=activity,
        stationary=not is_driving, miles=0.0,
    )
    segments.append(seg)
    clock.time += timedelta(hours=hours)
    if status != OFF_DUTY:
        clock.cycle_used += hours
    return seg


def _process_drive(clock, segments, route, miles_since_fuel=0.0):
    remaining_hr = route.duration_hours
    remaining_mi = route.distance_miles
    spd = route.avg_speed_mph

    while remaining_hr > 0.001:
        # Handle immediate limits (no driving possible)
        if clock.cycle_remaining <= 0.001:
            _do_restart(clock, segments, route, remaining_mi)
            continue
        if clock.driving_remaining <= 0.001 or clock.window_remaining <= 0.001:
            _do_reset(clock, segments, route, remaining_mi)
            continue
        if clock.until_break <= 0.001:
            _do_break(clock, segments, route, remaining_mi)
            continue

        # Calculate max driveable chunk
        max_hr = min(
            remaining_hr,
            clock.driving_remaining,
            clock.window_remaining,
            clock.cycle_remaining,
            clock.until_break,
        )

        # Check fuel
        mi_to_fuel = FUEL_INTERVAL_MILES - miles_since_fuel
        if mi_to_fuel <= 0:
            _do_fuel(clock, segments, route, remaining_mi)
            miles_since_fuel = 0.0
            continue
        hr_to_fuel = mi_to_fuel / spd if spd > 0 else 9999
        if hr_to_fuel < max_hr:
            max_hr = hr_to_fuel

        max_hr = max(0.001, max_hr)
        mi_chunk = min(max_hr * spd, remaining_mi)
        hr_chunk = mi_chunk / spd if spd > 0 else max_hr

        loc = _interp_loc(route, remaining_mi)
        seg = DutySegment(
            status=DRIVING, start_time=clock.time,
            end_time=clock.time + timedelta(hours=hr_chunk),
            location=loc, activity=None,
            stationary=False, miles=mi_chunk,
        )
        segments.append(seg)

        clock.time += timedelta(hours=hr_chunk)
        clock.driving_since_break += hr_chunk
        clock.driving_since_reset += hr_chunk
        clock.cycle_used += hr_chunk
        remaining_hr -= hr_chunk
        remaining_mi -= mi_chunk
        miles_since_fuel += mi_chunk

        # After driving, check if fuel is due
        if miles_since_fuel >= FUEL_INTERVAL_MILES - 1 and remaining_hr > 0.01:
            _do_fuel(clock, segments, route, remaining_mi)
            miles_since_fuel = 0.0

    return miles_since_fuel


def _do_break(clock, segments, route, remaining_mi):
    loc = _interp_loc(route, remaining_mi)
    _add_segment(segments, clock, ON_DUTY_NOT_DRIVING,
                 BREAK_DURATION_HOURS, loc, "30-min break")
    clock.driving_since_break = 0.0
    # Correct cycle_used already handled by _add_segment


def _do_fuel(clock, segments, route, remaining_mi):
    loc = _interp_loc(route, remaining_mi)
    _add_segment(segments, clock, ON_DUTY_NOT_DRIVING,
                 FUEL_STOP_DURATION_HOURS, loc, "Fuel stop")
    clock.driving_since_break = 0.0  # 30-min fuel clears break


def _do_reset(clock, segments, route, remaining_mi):
    loc = _interp_loc(route, remaining_mi)
    seg = DutySegment(
        status=OFF_DUTY, start_time=clock.time,
        end_time=clock.time + timedelta(hours=RESET_DURATION_HOURS),
        location=loc, activity="10-hr reset", stationary=True,
    )
    segments.append(seg)
    clock.time += timedelta(hours=RESET_DURATION_HOURS)
    clock.driving_since_reset = 0.0
    clock.driving_since_break = 0.0
    clock.window_start = clock.time


def _do_restart(clock, segments, route, remaining_mi):
    loc = _interp_loc(route, remaining_mi)
    seg = DutySegment(
        status=OFF_DUTY, start_time=clock.time,
        end_time=clock.time + timedelta(hours=RESTART_DURATION_HOURS),
        location=loc, activity="34-hr restart", stationary=True,
    )
    segments.append(seg)
    clock.time += timedelta(hours=RESTART_DURATION_HOURS)
    clock.cycle_used = 0.0
    clock.driving_since_reset = 0.0
    clock.driving_since_break = 0.0
    clock.window_start = clock.time


def _process_duty(clock, segments, hours, location, activity):
    remaining = hours
    while remaining > 0.001:
        if clock.window_remaining <= 0.001:
            _do_reset(clock, segments, RouteInfo(0, 0, location, location), 0)
            continue
        if clock.cycle_remaining <= 0.001:
            _do_restart(clock, segments, RouteInfo(0, 0, location, location), 0)
            continue
        chunk = min(remaining, clock.window_remaining, clock.cycle_remaining)
        _add_segment(segments, clock, ON_DUTY_NOT_DRIVING, chunk, location, activity)
        remaining -= chunk


def _interp_loc(route, remaining_mi):
    if route.distance_miles <= 0:
        return route.destination_name
    progress = 1.0 - (remaining_mi / route.distance_miles)
    if progress < 0.05:
        return route.origin_name
    if progress > 0.95:
        return route.destination_name
    return f"En route to {route.destination_name}"


# ─── Daily Log Splitting ────────────────────────────────────────────────────

def split_schedule_into_daily_logs(segments, trip_start):
    if not segments:
        return []

    first_date = segments[0].start_time.date()
    last_date = segments[-1].end_time.date()
    dates = []
    cur = first_date
    while cur <= last_date:
        dates.append(cur)
        cur += timedelta(days=1)

    logs = []
    for idx, log_date in enumerate(dates, 1):
        tz = trip_start.tzinfo
        day_start = datetime(log_date.year, log_date.month, log_date.day, tzinfo=tz)
        day_end = day_start + timedelta(hours=24)

        day_segs = []
        day_miles = 0.0

        for seg in segments:
            s = max(seg.start_time, day_start)
            e = min(seg.end_time, day_end)
            if s >= e:
                continue
            sh = (s - day_start).total_seconds() / 3600.0
            eh = (e - day_start).total_seconds() / 3600.0
            m = 0.0
            if seg.status == DRIVING and seg.duration_hours > 0:
                frac = (eh - sh) / seg.duration_hours
                m = seg.miles * min(frac, 1.0)
                day_miles += m
            day_segs.append({
                "status": seg.status,
                "start": round(sh, 4),
                "end": round(eh, 4),
                "location": seg.location,
                "activity": seg.activity,
                "stationary": seg.stationary,
            })

        day_segs = _pad_day(day_segs)
        totals = _totals(day_segs)

        logs.append(DailyLogSheet(
            day_index=idx, log_date=log_date,
            total_miles_today=round(day_miles, 1),
            segments=day_segs, totals=totals,
            recap={"cycle_hours_used_today": 0},
        ))

    # Compute running cycle recap
    running = 0.0
    for log in logs:
        running += log.totals["combined_driving_and_on_duty"]
        log.recap["cycle_hours_used_today"] = round(running, 2)

    return logs


def _pad_day(segs):
    if not segs:
        return [{"status": OFF_DUTY, "start": 0.0, "end": 24.0,
                 "location": "", "activity": None, "stationary": True}]
    padded = []
    first = segs[0]["start"]
    if first > 0.001:
        padded.append({"status": OFF_DUTY, "start": 0.0, "end": round(first, 4),
                        "location": segs[0]["location"], "activity": None, "stationary": True})
    for i, s in enumerate(segs):
        if padded and s["start"] - padded[-1]["end"] > 0.001:
            padded.append({"status": OFF_DUTY, "start": round(padded[-1]["end"], 4),
                            "end": round(s["start"], 4), "location": s["location"],
                            "activity": None, "stationary": True})
        padded.append(s)
    last = padded[-1]["end"]
    if last < 23.999:
        padded.append({"status": OFF_DUTY, "start": round(last, 4), "end": 24.0,
                        "location": padded[-1]["location"], "activity": None, "stationary": True})
    return padded


def _totals(segs):
    t = {"off_duty": 0.0, "sleeper_berth": 0.0, "driving": 0.0, "on_duty_not_driving": 0.0}
    m = {OFF_DUTY: "off_duty", SLEEPER_BERTH: "sleeper_berth",
         DRIVING: "driving", ON_DUTY_NOT_DRIVING: "on_duty_not_driving"}
    for s in segs:
        k = m.get(s["status"])
        if k:
            t[k] += s["end"] - s["start"]
    for k in t:
        t[k] = round(t[k], 2)
    t["combined_driving_and_on_duty"] = round(t["driving"] + t["on_duty_not_driving"], 2)
    return t


def validate_log_sheet(sheet):
    errors = []
    if sheet.total_miles_today < 0:
        errors.append(f"Day {sheet.day_index}: negative miles")
    total = sum(sheet.totals[k] for k in ["off_duty", "sleeper_berth", "driving", "on_duty_not_driving"])
    if abs(total - 24.0) > 0.1:
        errors.append(f"Day {sheet.day_index}: totals={total:.2f}, expected 24")
    exp = round(sheet.totals["driving"] + sheet.totals["on_duty_not_driving"], 2)
    act = sheet.totals.get("combined_driving_and_on_duty", 0)
    if abs(exp - act) > 0.01:
        errors.append(f"Day {sheet.day_index}: combined mismatch {act} vs {exp}")
    for i, s in enumerate(sheet.segments):
        if s.get("stationary") and not s.get("location"):
            errors.append(f"Day {sheet.day_index}, seg {i}: empty location")
    for i in range(1, len(sheet.segments)):
        if abs(sheet.segments[i-1]["end"] - sheet.segments[i]["start"]) > 0.01:
            errors.append(f"Day {sheet.day_index}: gap at segs {i-1}-{i}")
    return errors
