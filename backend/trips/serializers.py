"""
DRF serializers for trip planning API.
"""

from rest_framework import serializers


class TripPlanRequestSerializer(serializers.Serializer):
    """Validates the POST /api/trips/plan request body."""

    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)
    trip_start = serializers.DateTimeField(required=False)


class SegmentSerializer(serializers.Serializer):
    """Serializes a single duty segment within a log sheet."""

    status = serializers.CharField()
    start = serializers.FloatField()
    end = serializers.FloatField()
    location = serializers.CharField(allow_blank=True)
    activity = serializers.CharField(allow_null=True, allow_blank=True)
    stationary = serializers.BooleanField()


class LogSheetSerializer(serializers.Serializer):
    """Serializes a single day's log sheet."""

    day_index = serializers.IntegerField()
    date = serializers.DateField()
    total_miles_today = serializers.FloatField()
    segments = SegmentSerializer(many=True)
    totals = serializers.DictField()
    recap = serializers.DictField()


class StopSerializer(serializers.Serializer):
    """Serializes a route stop/marker."""

    type = serializers.CharField()
    label = serializers.CharField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class TripPlanResponseSerializer(serializers.Serializer):
    """Serializes the full POST /api/trips/plan response."""

    trip_id = serializers.UUIDField()
    driver_info = serializers.DictField()
    summary = serializers.DictField()
    route = serializers.DictField()
    log_sheets = LogSheetSerializer(many=True)
