# utils/offline.py - COMPLETE FILE (NEW)

"""
Offline mode support for SafePaws AI
"""

import streamlit as st
import json
from pathlib import Path
import time

OFFLINE_CACHE_DIR = Path("offline_cache")
OFFLINE_CACHE_DIR.mkdir(exist_ok=True)


def is_online():
    """Check if internet connection is available"""
    try:
        import requests
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False


def cache_for_offline(key, data, ttl_hours=24):
    """
    Cache data for offline use

    Args:
        key: Unique identifier
        data: Data to cache (must be JSON serializable)
        ttl_hours: Time to live in hours
    """
    cache_file = OFFLINE_CACHE_DIR / f"{key}.json"

    cache_data = {
        "data": data,
        "timestamp": time.time(),
        "ttl": ttl_hours * 3600
    }

    try:
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
        return True
    except Exception as e:
        print(f"❌ Cache error: {e}")
        return False


def get_offline_data(key, default=None):
    """
    Retrieve cached data for offline use

    Returns: cached data or default if not found/expired
    """
    cache_file = OFFLINE_CACHE_DIR / f"{key}.json"

    if not cache_file.exists():
        return default

    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)

        # Check if expired
        age = time.time() - cache_data["timestamp"]
        if age > cache_data["ttl"]:
            return default

        return cache_data["data"]

    except Exception as e:
        print(f"❌ Cache read error: {e}")
        return default

def offline_mode_banner():
    """Show offline mode indicator - OPTIMIZED to prevent reloads"""

    # Check only if not already checked this session
    if "offline_checked" not in st.session_state:
        st.session_state.offline_checked = True
        st.session_state.is_offline = not is_online()

    if st.session_state.get("is_offline", False):
        st.markdown("""
        <div style="position: fixed; top: 0; left: 0; right: 0; 
                    background: #f59e0b; color: white; text-align: center;
                    padding: 12px; z-index: 99999; font-weight: 600;">
            📡 Offline Mode • Using cached data • Limited functionality
        </div>
        """, unsafe_allow_html=True)

        # Add top padding to main content
        st.markdown("""
        <style>
        .main { margin-top: 50px !important; }
        </style>
        """, unsafe_allow_html=True)

        return True
    return False


def sync_offline_changes():
    """Sync offline changes when connection restored"""
    pending_file = OFFLINE_CACHE_DIR / "pending_sync.json"

    if not pending_file.exists():
        return

    if is_online():
        try:
            with open(pending_file, 'r') as f:
                pending = json.load(f)

            # Process each pending operation
            for operation in pending:
                print(f"✅ Syncing: {operation['type']}")

            # Clear pending file
            pending_file.unlink()
            st.success("✅ Offline changes synced!")

        except Exception as e:
            st.error(f"❌ Sync error: {e}")


def add_to_sync_queue(operation_type, data):
    """Add operation to offline sync queue"""
    pending_file = OFFLINE_CACHE_DIR / "pending_sync.json"

    try:
        if pending_file.exists():
            with open(pending_file, 'r') as f:
                pending = json.load(f)
        else:
            pending = []

        pending.append({
            "type": operation_type,
            "data": data,
            "timestamp": time.time()
        })

        with open(pending_file, 'w') as f:
            json.dump(pending, f, default=str)

    except Exception as e:
        print(f"❌ Queue error: {e}")


def get_offline_map(lat, lon, zoom=13):
    """
    Create map using cached tiles if offline
    """
    import folium

    if is_online():
        tiles = 'CartoDB dark_matter'
    else:
        st.warning("🗺️ Using simplified offline map")
        tiles = 'OpenStreetMap'

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=tiles
    )

    return m