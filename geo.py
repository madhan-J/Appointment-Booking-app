"""
Geocoding and Haversine distance calculations.
"""

import math
from typing import List, Dict, Any, Tuple, Optional

try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def geocode_address(address_query: str) -> Optional[Tuple[float, float]]:
    if not GEOPY_AVAILABLE or not address_query:
        return None
    try:
        geolocator = Nominatim(user_agent="appointment_management_agent")
        location = geolocator.geocode(address_query, timeout=5)
        if location:
            return (location.latitude, location.longitude)
    except Exception:
        pass
    return None

def find_nearest_locations(
    user_lat: float, user_lon: float, locations: List[Dict[str, Any]], top_k: int = 5
) -> List[Dict[str, Any]]:
    results = []
    for loc in locations:
        loc_copy = dict(loc)
        try:
            dist = haversine_distance(user_lat, user_lon, float(loc["lat"]), float(loc["lng"]))
            loc_copy["distance_km"] = dist
            results.append(loc_copy)
        except (ValueError, KeyError, TypeError):
            continue

    results.sort(key=lambda x: x["distance_km"])
    return results[:top_k]

def get_google_maps_url(lat: float, lng: float, name: str = "") -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
