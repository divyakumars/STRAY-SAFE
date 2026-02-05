# utils/free_maps.py (NEW FILE)

"""
FREE Map Integration for SafePaws AI
Uses OpenStreetMap + Nominatim (100% free, no API keys)
"""

import requests
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import streamlit as st

# Initialize geocoder (FREE - OpenStreetMap Nominatim)
geolocator = Nominatim(user_agent="safepaws_ai_v1.0_social_impact")


@st.cache_data(ttl=86400)  # Cache for 24 hours
def geocode_address(address, retry=3):
    """
    FREE Geocoding using OpenStreetMap Nominatim
    Limit: 1 request/second (fair use)
    Returns: (lat, lon) tuple or None
    """
    if not address or len(address.strip()) < 3:
        return None

    for attempt in range(retry):
        try:
            time.sleep(1.1)  # Rate limit: 1 req/sec
            location = geolocator.geocode(
                address,
                timeout=10,
                addressdetails=True,
                language='en'
            )

            if location:
                print(f"✅ Geocoded: {address} → ({location.latitude:.6f}, {location.longitude:.6f})")
                return (location.latitude, location.longitude)
            else:
                print(f"⚠️ No results for: {address}")
                return None

        except GeocoderTimedOut:
            print(f"⏱️ Geocoding timeout attempt {attempt + 1}/{retry}")
            if attempt < retry - 1:
                time.sleep(2)
            else:
                return None
        except GeocoderServiceError as e:
            print(f"❌ Geocoding service error: {e}")
            return None
        except Exception as e:
            print(f"❌ Geocoding error: {e}")
            return None

    return None


@st.cache_data(ttl=86400)
def reverse_geocode(lat, lon, retry=3):
    """
    FREE Reverse geocoding using Nominatim
    Returns: formatted address string or None
    """
    for attempt in range(retry):
        try:
            time.sleep(1.1)  # Rate limit
            location = geolocator.reverse(
                f"{lat}, {lon}",
                timeout=10,
                language='en'
            )

            if location:
                return location.address
            else:
                return None

        except Exception as e:
            print(f"⚠️ Reverse geocoding attempt {attempt + 1}/{retry} failed: {e}")
            if attempt < retry - 1:
                time.sleep(2)
            else:
                return None

    return None


def get_directions(origin_lat, origin_lon, dest_lat, dest_lon, mode="driving"):
    """
    FREE Routing using OSRM (Open Source Routing Machine)
    Returns: dict with distance, duration, route geometry
    """
    # OSRM public server (FREE)
    base_url = "https://router.project-osrm.org/route/v1"

    # Mode: driving, walking, cycling
    url = f"{base_url}/{mode}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            return {
                "distance_km": round(route["distance"] / 1000, 2),
                "duration_min": round(route["duration"] / 60, 0),
                "distance_text": f"{route['distance'] / 1000:.1f} km",
                "duration_text": f"{route['duration'] / 60:.0f} min",
                "geometry": route["geometry"]["coordinates"]
            }
        else:
            print(f"❌ Routing failed: {data.get('code', 'Unknown error')}")
            return None

    except requests.exceptions.Timeout:
        print("⏱️ Routing request timeout")
        return None
    except Exception as e:
        print(f"❌ Routing error: {e}")
        return None


@st.cache_data(ttl=3600)
def search_locations(query, limit=5):
    """
    FREE Location search/autocomplete using Nominatim
    Returns: list of dicts with name, lat, lon
    """
    if not query or len(query) < 3:
        return []

    try:
        time.sleep(1.1)
        locations = geolocator.geocode(
            query,
            exactly_one=False,
            limit=limit,
            timeout=10,
            addressdetails=True
        )

        if locations:
            results = []
            for loc in locations:
                results.append({
                    "name": loc.address,
                    "lat": loc.latitude,
                    "lon": loc.longitude,
                    "type": loc.raw.get("type", "location")
                })
            return results
        else:
            return []

    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns: distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2

    R = 6371.0  # Earth radius in km

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return round(distance, 2)


def validate_coordinates(lat, lon):
    """
    Validate latitude and longitude
    Returns: True if valid, False otherwise
    """
    try:
        lat = float(lat)
        lon = float(lon)

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return True
        return False
    except (ValueError, TypeError):
        return False


# utils/free_maps.py - ADD THESE FUNCTIONS
import polyline  # Install: pip install polyline


def get_directions_with_alternatives(origin_lat, origin_lon, dest_lat, dest_lon, mode="driving"):
    """
    Get multiple route options with detailed instructions
    Returns: dict with routes, steps, and alternatives
    """
    base_url = "https://router.project-osrm.org/route/v1"

    url = f"{base_url}/{mode}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {
        "overview": "full",
        "geometries": "polyline",  # More compact than geojson
        "steps": "true",
        "alternatives": "true",  # Get alternative routes
        "annotations": "true"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()

        if data.get("code") == "Ok" and data.get("routes"):
            routes = []

            for idx, route in enumerate(data["routes"][:3]):  # Max 3 alternatives
                # Decode polyline
                coordinates = polyline.decode(route["geometry"])

                # Extract turn-by-turn instructions
                steps = []
                if route.get("legs"):
                    for leg in route["legs"]:
                        for step in leg.get("steps", []):
                            steps.append({
                                "instruction": step.get("maneuver", {}).get("instruction", "Continue"),
                                "distance": step.get("distance", 0),
                                "duration": step.get("duration", 0),
                                "type": step.get("maneuver", {}).get("type", "turn")
                            })

                routes.append({
                    "route_id": idx,
                    "distance_km": round(route["distance"] / 1000, 2),
                    "duration_min": round(route["duration"] / 60, 0),
                    "distance_text": f"{route['distance'] / 1000:.1f} km",
                    "duration_text": f"{route['duration'] / 60:.0f} min",
                    "coordinates": [(lat, lon) for lat, lon in coordinates],  # Already lat, lon
                    "steps": steps,
                    "is_fastest": idx == 0
                })

            return {
                "success": True,
                "routes": routes,
                "origin": (origin_lat, origin_lon),
                "destination": (dest_lat, dest_lon)
            }
        else:
            return {"success": False, "error": data.get("message", "No routes found")}

    except Exception as e:
        print(f"❌ Routing error: {e}")
        return {"success": False, "error": str(e)}


def get_eta_with_traffic(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Get ETA considering typical traffic patterns (approximate)
    """
    route_info = get_directions_with_alternatives(origin_lat, origin_lon, dest_lat, dest_lon)

    if not route_info.get("success"):
        return None

    base_duration = route_info["routes"][0]["duration_min"]

    # Apply traffic multipliers based on time of day
    import datetime
    hour = datetime.datetime.now().hour

    # Traffic patterns (1.0 = normal, >1.0 = congestion)
    traffic_multipliers = {
        range(7, 10): 1.4,  # Morning rush
        range(10, 17): 1.1,  # Daytime
        range(17, 20): 1.5,  # Evening rush
        range(20, 24): 0.9,  # Night
        range(0, 7): 0.8  # Early morning
    }

    multiplier = 1.0
    for time_range, mult in traffic_multipliers.items():
        if hour in time_range:
            multiplier = mult
            break

    adjusted_duration = int(base_duration * multiplier)

    return {
        "base_duration": base_duration,
        "traffic_duration": adjusted_duration,
        "delay": adjusted_duration - base_duration,
        "traffic_level": "Heavy" if multiplier > 1.3 else "Moderate" if multiplier > 1.0 else "Light"
    }