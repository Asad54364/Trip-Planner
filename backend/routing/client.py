"""
Routing & Geocoding client.

Primary: OpenRouteService (ORS) with driving-hgv profile.
Fallback: OSRM public demo + Nominatim (when ORS_API_KEY is unset).
"""

import os
import time
import requests


ORS_API_KEY = os.environ.get("ORS_API_KEY", "")
ORS_BASE = "https://api.openrouteservice.org"
OSRM_BASE = "https://router.project-osrm.org"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"

METERS_TO_MILES = 0.000621371
SECONDS_TO_HOURS = 1 / 3600


class RoutingClient:
    """Wraps ORS (primary) and OSRM/Nominatim (fallback)."""

    def __init__(self):
        self.use_ors = bool(ORS_API_KEY)

    def geocode(self, place_name: str) -> dict:
        """Returns {lat, lng, formatted_name}."""
        if self.use_ors:
            return self._ors_geocode(place_name)
        return self._nominatim_geocode(place_name)

    def get_directions(self, origin: tuple, destination: tuple) -> dict:
        """
        origin/destination: (lat, lng)
        Returns {distance_miles, duration_hours, geometry}
        """
        if self.use_ors:
            return self._ors_directions(origin, destination)
        return self._osrm_directions(origin, destination)

    # ─── ORS ─────────────────────────────────────────────────

    def _ors_geocode(self, place_name):
        resp = requests.get(
            f"{ORS_BASE}/geocode/search",
            params={"api_key": ORS_API_KEY, "text": place_name, "size": 1},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        feat = data["features"][0]
        coords = feat["geometry"]["coordinates"]  # [lng, lat]
        label = feat["properties"].get("label", place_name)
        return {"lat": coords[1], "lng": coords[0], "formatted_name": label}

    def _ors_directions(self, origin, destination):
        resp = requests.post(
            f"{ORS_BASE}/v2/directions/driving-hgv/geojson",
            json={"coordinates": [
                [origin[1], origin[0]],      # ORS expects [lng, lat]
                [destination[1], destination[0]],
            ]},
            headers={
                "Authorization": ORS_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        feat = data["features"][0]
        props = feat["properties"]["summary"]
        return {
            "distance_miles": props["distance"] * METERS_TO_MILES,
            "duration_hours": props["duration"] * SECONDS_TO_HOURS,
            "geometry": feat["geometry"],
        }

    # ─── Fallback: OSRM + Nominatim ─────────────────────────

    def _nominatim_geocode(self, place_name):
        resp = requests.get(
            f"{NOMINATIM_BASE}/search",
            params={"q": place_name, "format": "json", "limit": 1},
            headers={"User-Agent": "TripPlannerELD/1.0 (assessment project)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"Could not geocode: {place_name}")
        item = data[0]
        time.sleep(1.1)  # Nominatim rate limit: 1 req/sec
        return {
            "lat": float(item["lat"]),
            "lng": float(item["lon"]),
            "formatted_name": item.get("display_name", place_name),
        }

    def _osrm_directions(self, origin, destination):
        coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        resp = requests.get(
            f"{OSRM_BASE}/route/v1/driving/{coords}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        route = data["routes"][0]
        return {
            "distance_miles": route["distance"] * METERS_TO_MILES,
            "duration_hours": route["duration"] * SECONDS_TO_HOURS,
            "geometry": route["geometry"],
        }
