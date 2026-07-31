"""
Trip and LogSheetDay models for persisting trip plans and ELD log data.
"""

import uuid

from django.db import models


class Trip(models.Model):
    """A planned trip with route, stops, and associated daily log sheets."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User inputs
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    cycle_used_hours = models.FloatField()
    trip_start = models.DateTimeField()

    # Computed route data
    total_distance_miles = models.FloatField(null=True, blank=True)
    total_duration_hours = models.FloatField(null=True, blank=True)
    route_geometry = models.JSONField(default=dict, blank=True)
    stops = models.JSONField(default=list, blank=True)

    # Cosmetic header fields for the log sheet
    driver_name = models.CharField(max_length=120, default="Sample Driver")
    driver_id = models.CharField(max_length=40, default="DRV-0001")
    carrier_name = models.CharField(max_length=255, default="Sample Carrier Inc.")
    main_office_address = models.CharField(
        max_length=255, default="123 Logistics Way, Springfield, USA"
    )
    truck_number = models.CharField(max_length=40, default="Truck 123")
    trailer_number = models.CharField(max_length=40, default="Trailer 20544")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Trip {self.id}: {self.current_location} → {self.pickup_location} → {self.dropoff_location}"


class LogSheetDay(models.Model):
    """One day's worth of ELD log data, tied to a Trip."""

    trip = models.ForeignKey(Trip, related_name="log_sheets", on_delete=models.CASCADE)
    day_index = models.PositiveIntegerField()
    date = models.DateField()
    total_miles_today = models.FloatField(default=0)

    # JSON array of duty segments:
    # [{status, start, end, location, activity, stationary}]
    segments = models.JSONField(default=list)

    # Totals (must sum to 24 for a full day)
    total_off_duty = models.FloatField(default=0)
    total_sleeper = models.FloatField(default=0)
    total_driving = models.FloatField(default=0)
    total_on_duty_not_driving = models.FloatField(default=0)

    # Recap
    cycle_hours_used_recap = models.FloatField(default=0)

    class Meta:
        ordering = ['day_index']
        unique_together = ['trip', 'day_index']

    def __str__(self):
        return f"Day {self.day_index} of Trip {self.trip_id}"
