"""
Unit tests for the HOS Rules Engine.
Covers all scenarios from the spec §10.
"""

import unittest
from datetime import datetime, timezone

from hos.planner import plan_trip, validate_log_sheet


def _dt(hour=6):
    """Helper: create a trip start at a given hour on a fixed date."""
    return datetime(2026, 7, 30, hour, 0, 0, tzinfo=timezone.utc)


class TestHOSEngine(unittest.TestCase):
    """Core HOS engine tests."""

    def _validate_all_sheets(self, sheets):
        """Run §9.5 invariant checks on all sheets."""
        for sheet in sheets:
            errors = validate_log_sheet(sheet)
            self.assertEqual(errors, [], f"Validation errors: {errors}")

    def _assert_24hr_totals(self, sheets):
        """Assert each full day sums to 24h."""
        for sheet in sheets:
            total = (
                sheet.totals["off_duty"]
                + sheet.totals["sleeper_berth"]
                + sheet.totals["driving"]
                + sheet.totals["on_duty_not_driving"]
            )
            self.assertAlmostEqual(total, 24.0, delta=0.15,
                                   msg=f"Day {sheet.day_index}: total={total}")

    def _assert_contiguous(self, sheets):
        """Assert segments are contiguous within each day."""
        for sheet in sheets:
            for i in range(1, len(sheet.segments)):
                prev_end = sheet.segments[i - 1]["end"]
                curr_start = sheet.segments[i]["start"]
                self.assertAlmostEqual(prev_end, curr_start, delta=0.02,
                                       msg=f"Day {sheet.day_index}: gap at {i}")

    # ─── Test 1: Short trip, no breaks ────────────────────────

    def test_short_trip_no_breaks(self):
        """A ~3-hour trip that fits in one day with no HOS limits triggered."""
        sheets = plan_trip(
            current_loc_name="Austin, TX",
            pickup_loc_name="San Antonio, TX",
            dropoff_loc_name="Houston, TX",
            leg1_distance_mi=80, leg1_duration_hr=1.5,
            leg2_distance_mi=200, leg2_duration_hr=3.0,
            cycle_used_hrs=0, trip_start=_dt(8),
        )

        self.assertEqual(len(sheets), 1)
        self._validate_all_sheets(sheets)
        self._assert_24hr_totals(sheets)
        self._assert_contiguous(sheets)

        # Should have driving segments
        driving = [s for s in sheets[0].segments if s["status"] == "DRIVING"]
        self.assertTrue(len(driving) >= 1)

    # ─── Test 2: Trip requiring 30-min break ──────────────────

    def test_30min_break_required(self):
        """A trip with >8 hrs driving triggers a 30-min break."""
        sheets = plan_trip(
            current_loc_name="Dallas, TX",
            pickup_loc_name="Little Rock, AR",
            dropoff_loc_name="Memphis, TN",
            leg1_distance_mi=320, leg1_duration_hr=5.0,
            leg2_distance_mi=200, leg2_duration_hr=3.5,
            cycle_used_hrs=0, trip_start=_dt(6),
        )

        self._validate_all_sheets(sheets)
        self._assert_24hr_totals(sheets)
        self._assert_contiguous(sheets)

        # Should have at least one 30-min break
        all_segs = []
        for s in sheets:
            all_segs.extend(s.segments)
        breaks = [s for s in all_segs if s.get("activity") == "30-min break"]
        self.assertTrue(len(breaks) >= 1, "Expected at least one 30-min break")

    # ─── Test 3: Trip requiring 10-hr reset ───────────────────

    def test_10hr_reset_required(self):
        """A long trip that exceeds 11-hr driving or 14-hr window."""
        sheets = plan_trip(
            current_loc_name="Los Angeles, CA",
            pickup_loc_name="Phoenix, AZ",
            dropoff_loc_name="Denver, CO",
            leg1_distance_mi=370, leg1_duration_hr=6.0,
            leg2_distance_mi=600, leg2_duration_hr=9.5,
            cycle_used_hrs=0, trip_start=_dt(6),
        )

        self._validate_all_sheets(sheets)
        self._assert_24hr_totals(sheets)
        self._assert_contiguous(sheets)

        # Should span multiple days due to reset
        self.assertTrue(len(sheets) >= 2, "Expected multi-day trip")

        # Should have a 10-hr reset
        all_segs = []
        for s in sheets:
            all_segs.extend(s.segments)
        resets = [s for s in all_segs if s.get("activity") == "10-hr reset"]
        self.assertTrue(len(resets) >= 1, "Expected at least one 10-hr reset")

    # ─── Test 4: Trip requiring 34-hr restart ─────────────────

    def test_34hr_restart(self):
        """Starting with high cycle used forces a 34-hr restart."""
        sheets = plan_trip(
            current_loc_name="New York, NY",
            pickup_loc_name="Chicago, IL",
            dropoff_loc_name="Denver, CO",
            leg1_distance_mi=790, leg1_duration_hr=12.0,
            leg2_distance_mi=1000, leg2_duration_hr=15.0,
            cycle_used_hrs=58,  # Only 12 hours left in cycle
            trip_start=_dt(6),
        )

        self._validate_all_sheets(sheets)
        self._assert_24hr_totals(sheets)
        self._assert_contiguous(sheets)

        all_segs = []
        for s in sheets:
            all_segs.extend(s.segments)
        restarts = [s for s in all_segs if s.get("activity") == "34-hr restart"]
        self.assertTrue(len(restarts) >= 1, "Expected 34-hr restart")

    # ─── Test 5: Fuel stop at 1,000 miles ─────────────────────

    def test_fuel_stop(self):
        """A trip over 1,000 miles should include a fuel stop."""
        sheets = plan_trip(
            current_loc_name="Seattle, WA",
            pickup_loc_name="Portland, OR",
            dropoff_loc_name="San Francisco, CA",
            leg1_distance_mi=175, leg1_duration_hr=3.0,
            leg2_distance_mi=900, leg2_duration_hr=14.0,
            cycle_used_hrs=0, trip_start=_dt(6),
        )

        self._validate_all_sheets(sheets)
        self._assert_24hr_totals(sheets)
        self._assert_contiguous(sheets)

        all_segs = []
        for s in sheets:
            all_segs.extend(s.segments)
        fuels = [s for s in all_segs if s.get("activity") == "Fuel stop"]
        self.assertTrue(len(fuels) >= 1, "Expected at least one fuel stop")

    # ─── Test 6: Edge case — cycle almost full ────────────────

    def test_cycle_near_limit(self):
        """Starting with cycle_used close to 70 triggers immediate restart."""
        sheets = plan_trip(
            current_loc_name="Miami, FL",
            pickup_loc_name="Orlando, FL",
            dropoff_loc_name="Jacksonville, FL",
            leg1_distance_mi=230, leg1_duration_hr=3.5,
            leg2_distance_mi=140, leg2_duration_hr=2.0,
            cycle_used_hrs=69,  # Only 1 hour left
            trip_start=_dt(8),
        )

        self._validate_all_sheets(sheets)
        self._assert_24hr_totals(sheets)
        self._assert_contiguous(sheets)

        all_segs = []
        for s in sheets:
            all_segs.extend(s.segments)
        restarts = [s for s in all_segs if s.get("activity") == "34-hr restart"]
        self.assertTrue(len(restarts) >= 1,
                        "Expected 34-hr restart with cycle near limit")

    # ─── Test 7: Stationary segments have brackets ────────────

    def test_stationary_brackets(self):
        """Every stationary segment has a location; driving segments are not stationary."""
        sheets = plan_trip(
            current_loc_name="Dallas, TX",
            pickup_loc_name="Oklahoma City, OK",
            dropoff_loc_name="Kansas City, MO",
            leg1_distance_mi=200, leg1_duration_hr=3.5,
            leg2_distance_mi=350, leg2_duration_hr=5.5,
            cycle_used_hrs=10, trip_start=_dt(6),
        )

        self._validate_all_sheets(sheets)

        for sheet in sheets:
            for seg in sheet.segments:
                if seg["status"] == "DRIVING":
                    self.assertFalse(seg["stationary"],
                                     "DRIVING should not be stationary")
                else:
                    self.assertTrue(seg["stationary"],
                                    f"{seg['status']} should be stationary")


if __name__ == "__main__":
    unittest.main()
