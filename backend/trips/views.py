"""
API views for trip planning.
"""

from datetime import datetime, timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from routing.client import RoutingClient
from hos.planner import plan_trip

from .models import Trip, LogSheetDay
from .serializers import TripPlanRequestSerializer


@api_view(['GET'])
def health_check(request):
    return Response({"status": "ok"})


@api_view(['POST'])
def plan_trip_view(request):
    serializer = TripPlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    trip_start = data.get('trip_start') or datetime.now(timezone.utc)
    client = RoutingClient()

    try:
        # Geocode locations
        current_geo = client.geocode(data['current_location'])
        pickup_geo = client.geocode(data['pickup_location'])
        dropoff_geo = client.geocode(data['dropoff_location'])

        # Get directions for both legs
        leg1 = client.get_directions(
            (current_geo['lat'], current_geo['lng']),
            (pickup_geo['lat'], pickup_geo['lng']),
        )
        leg2 = client.get_directions(
            (pickup_geo['lat'], pickup_geo['lng']),
            (dropoff_geo['lat'], dropoff_geo['lng']),
        )
    except Exception as e:
        return Response(
            {"error": f"Routing/geocoding failed: {str(e)}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # Run HOS engine
    current_name = _short_name(current_geo['formatted_name'])
    pickup_name = _short_name(pickup_geo['formatted_name'])
    dropoff_name = _short_name(dropoff_geo['formatted_name'])

    log_sheets = plan_trip(
        current_loc_name=current_name,
        pickup_loc_name=pickup_name,
        dropoff_loc_name=dropoff_name,
        leg1_distance_mi=leg1['distance_miles'],
        leg1_duration_hr=leg1['duration_hours'],
        leg2_distance_mi=leg2['distance_miles'],
        leg2_duration_hr=leg2['duration_hours'],
        cycle_used_hrs=data['cycle_used_hours'],
        trip_start=trip_start,
    )

    total_dist = leg1['distance_miles'] + leg2['distance_miles']
    total_driving = sum(s.totals['driving'] for s in log_sheets)
    total_duration = sum(
        s.totals['driving'] + s.totals['on_duty_not_driving'] + s.totals['off_duty'] + s.totals['sleeper_berth']
        for s in log_sheets
    )

    # Build stops list
    stops = _build_stops(current_geo, pickup_geo, dropoff_geo, log_sheets,
                         current_name, pickup_name, dropoff_name)

    # Combine geometries
    geometry = _combine_geometry(leg1.get('geometry'), leg2.get('geometry'))

    # Persist to database
    trip = Trip.objects.create(
        current_location=data['current_location'],
        pickup_location=data['pickup_location'],
        dropoff_location=data['dropoff_location'],
        cycle_used_hours=data['cycle_used_hours'],
        trip_start=trip_start,
        total_distance_miles=round(total_dist, 1),
        total_duration_hours=round(total_duration, 1),
        route_geometry=geometry,
        stops=stops,
    )

    for sheet in log_sheets:
        LogSheetDay.objects.create(
            trip=trip,
            day_index=sheet.day_index,
            date=sheet.log_date,
            total_miles_today=sheet.total_miles_today,
            segments=sheet.segments,
            total_off_duty=sheet.totals['off_duty'],
            total_sleeper=sheet.totals['sleeper_berth'],
            total_driving=sheet.totals['driving'],
            total_on_duty_not_driving=sheet.totals['on_duty_not_driving'],
            cycle_hours_used_recap=sheet.recap['cycle_hours_used_today'],
        )

    # Build response
    response_data = {
        "trip_id": str(trip.id),
        "driver_info": {
            "driver_name": trip.driver_name,
            "driver_id": trip.driver_id,
            "carrier_name": trip.carrier_name,
            "main_office_address": trip.main_office_address,
            "truck_number": trip.truck_number,
            "trailer_number": trip.trailer_number,
        },
        "summary": {
            "total_distance_miles": round(total_dist, 1),
            "total_driving_hours": round(total_driving, 1),
            "total_trip_duration_hours": round(total_duration, 1),
            "num_log_sheets": len(log_sheets),
        },
        "route": {
            "geometry": geometry,
            "stops": stops,
        },
        "log_sheets": [
            {
                "day_index": s.day_index,
                "date": str(s.log_date),
                "total_miles_today": s.total_miles_today,
                "segments": s.segments,
                "totals": s.totals,
                "recap": s.recap,
            }
            for s in log_sheets
        ],
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_trip(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return Response({"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND)

    sheets = trip.log_sheets.all().order_by('day_index')

    response_data = {
        "trip_id": str(trip.id),
        "driver_info": {
            "driver_name": trip.driver_name,
            "driver_id": trip.driver_id,
            "carrier_name": trip.carrier_name,
            "main_office_address": trip.main_office_address,
            "truck_number": trip.truck_number,
            "trailer_number": trip.trailer_number,
        },
        "summary": {
            "total_distance_miles": trip.total_distance_miles,
            "total_driving_hours": sum(s.total_driving for s in sheets),
            "total_trip_duration_hours": trip.total_duration_hours,
            "num_log_sheets": sheets.count(),
        },
        "route": {
            "geometry": trip.route_geometry,
            "stops": trip.stops,
        },
        "log_sheets": [
            {
                "day_index": s.day_index,
                "date": str(s.date),
                "total_miles_today": s.total_miles_today,
                "segments": s.segments,
                "totals": {
                    "off_duty": s.total_off_duty,
                    "sleeper_berth": s.total_sleeper,
                    "driving": s.total_driving,
                    "on_duty_not_driving": s.total_on_duty_not_driving,
                    "combined_driving_and_on_duty": round(
                        s.total_driving + s.total_on_duty_not_driving, 2
                    ),
                },
                "recap": {"cycle_hours_used_today": s.cycle_hours_used_recap},
            }
            for s in sheets
        ],
    }

    return Response(response_data)


def _short_name(full_name: str) -> str:
    """Shorten a geocoded name to City, ST format if possible."""
    parts = [p.strip() for p in full_name.split(',')]
    if len(parts) >= 3:
        return f"{parts[0]}, {parts[1]}"
    return full_name


def _build_stops(current_geo, pickup_geo, dropoff_geo, log_sheets,
                 current_name, pickup_name, dropoff_name):
    stops = [
        {"type": "start", "label": current_name,
         "lat": current_geo['lat'], "lng": current_geo['lng']},
        {"type": "pickup", "label": pickup_name,
         "lat": pickup_geo['lat'], "lng": pickup_geo['lng']},
    ]

    # Add rest/fuel stops from log sheets
    for sheet in log_sheets:
        for seg in sheet.segments:
            if seg.get('activity') in ('Fuel stop', '30-min break', '10-hr reset', '34-hr restart'):
                stop_type = {
                    'Fuel stop': 'fuel',
                    '30-min break': 'break',
                    '10-hr reset': 'rest_10hr',
                    '34-hr restart': 'rest_34hr',
                }.get(seg['activity'], 'rest')

                # Try not to duplicate stops at same location
                label = f"{seg['location']} — {seg['activity']}"
                if not any(s['label'] == label for s in stops):
                    stops.append({
                        "type": stop_type,
                        "label": label,
                        "lat": current_geo['lat'],  # Approximate
                        "lng": current_geo['lng'],
                    })

    stops.append(
        {"type": "dropoff", "label": dropoff_name,
         "lat": dropoff_geo['lat'], "lng": dropoff_geo['lng']}
    )
    return stops


def _combine_geometry(geo1, geo2):
    """Combine two GeoJSON geometries into one."""
    if not geo1 or not geo2:
        return geo1 or geo2 or {"type": "LineString", "coordinates": []}

    coords1 = geo1.get("coordinates", [])
    coords2 = geo2.get("coordinates", [])
    return {
        "type": "LineString",
        "coordinates": coords1 + coords2,
    }
