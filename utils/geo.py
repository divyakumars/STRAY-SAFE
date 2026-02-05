# utils/geo.py (UPDATE EXISTING FILE)

from utils.free_maps import geocode_address


def geocode_place(place):
    """
    Geocode place names to coordinates
    Now uses FREE Google-quality geocoding with fallback
    """

    # Try FREE Nominatim geocoding first
    coords = geocode_address(place)

    if coords:
        return coords

    # Fallback to hardcoded Chennai locations (for offline/backup)
    locations = {
        "t.nagar": (13.0418, 80.2341),
        "t nagar": (13.0418, 80.2341),
        "anna nagar": (13.0850, 80.2101),
        "adyar": (13.0067, 80.2571),
        "velachery": (12.9750, 80.2200),
        "tambaram": (12.9229, 80.1275),
        "guindy": (13.0067, 80.2206),
        "besant nagar": (13.0001, 80.2668),
        "marina beach": (13.0499, 80.2824),
        "mylapore": (13.0333, 80.2667),
        "nungambakkam": (13.0569, 80.2426),
        "kodambakkam": (13.0518, 80.2244),
        "vadapalani": (13.0504, 80.2124),
        "porur": (13.0358, 80.1561),
        "sholinganallur": (12.9008, 80.2271),
        "perungudi": (12.9611, 80.2425),
        "thiruvanmiyur": (12.9826, 80.2588),
        "chrompet": (12.9517, 80.1392)
    }

    place_lower = place.lower().strip()

    # Try exact match
    if place_lower in locations:
        return locations[place_lower]

    # Try partial match
    for key, coords in locations.items():
        if key in place_lower or place_lower in key:
            return coords

    # Default to Chennai center
    print(f"⚠️ Location '{place}' not found, using Chennai center")
    return (13.0827, 80.2707)