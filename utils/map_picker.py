# utils/map_picker.py - FIXED VERSION

"""
Interactive Map Picker for SafePaws AI
Allows users to click on map to select exact locations
"""

import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, Geocoder, LocateControl, MarkerCluster
import streamlit as st


def create_location_picker(
        default_lat=13.0827,
        default_lon=80.2707,
        zoom=12,
        existing_markers=None,
        height=500,
        label="Pick Location",
        enable_search=True,
        enable_locate=True
):
    """
    Interactive map where users can click to select location
    """
    import streamlit as st

    # ✅ GET THEME FROM SESSION STATE
    theme = st.session_state.get("map_theme", "dark")

    # ✅ THEME CONFIGURATION
    theme_tiles = {
        "dark": "CartoDB dark_matter",
        "light": "CartoDB positron",
        "satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "street": "OpenStreetMap"
    }

    tiles = theme_tiles.get(theme, "CartoDB dark_matter")

    # Create map with theme
    if tiles.startswith("http"):
        # Custom tile layer
        m = folium.Map(
            location=[default_lat, default_lon],
            zoom_start=zoom,
            control_scale=True,
            prefer_canvas=True
        )
        folium.TileLayer(
            tiles=tiles,
            attr="Esri",
            name="Satellite"
        ).add_to(m)
    else:
        # Built-in tiles
        m = folium.Map(
            location=[default_lat, default_lon],
            zoom_start=zoom,
            tiles=tiles,
            control_scale=True,
            prefer_canvas=True
        )

    # Add search box (uses Nominatim - FREE)
    if enable_search:
        from folium.plugins import Geocoder
        Geocoder(
            collapsed=False,
            position='topright',
            placeholder='🔍 Search location...',
            add_marker=True
        ).add_to(m)

    # Add "locate me" button (GPS)
    if enable_locate:
        from folium.plugins import LocateControl
        LocateControl(
            position='topright',
            strings={'title': '📍 Show my location'},
            locateOptions={'enableHighAccuracy': True}
        ).add_to(m)

    # Add drawing tools for clicking
    from folium.plugins import Draw
    Draw(
        export=False,
        position='topleft',
        draw_options={
            'polyline': False,
            'polygon': False,
            'circle': False,
            'rectangle': False,
            'circlemarker': False,
            'marker': True
        },
        edit_options={'edit': False, 'remove': True}
    ).add_to(m)

    # Add existing markers (e.g., show all hotspots)
    if existing_markers:
        from folium.plugins import MarkerCluster

        # Use clustering if many markers
        if len(existing_markers) > 20:
            marker_cluster = MarkerCluster().add_to(m)
            add_to = marker_cluster
        else:
            add_to = m

        for marker in existing_markers:
            # Color mapping
            color_map = {
                'red': 'red',
                'orange': 'orange',
                'green': 'green',
                'blue': 'blue',
                'purple': 'purple',
                'gray': 'gray',
                '#ef4444': 'red',
                '#f59e0b': 'orange',
                '#10b981': 'green',
                '#3b82f6': 'blue',
                '#8b5cf6': 'purple',
                '#64748b': 'gray'
            }

            folium_color = color_map.get(marker.get('color', 'blue'), 'blue')

            # Icon mapping
            icon_map = {
                'warning': 'exclamation-triangle',
                'plus-square': 'plus-square',
                'map-marker': 'map-marker',
                'info-sign': 'info-sign',
                'exclamation-triangle': 'exclamation-triangle'
            }

            folium_icon = icon_map.get(marker.get('icon', 'info-sign'), 'info-sign')

            # Create popup
            popup_html = f"""
            <div style='font-family: Arial; min-width: 150px;'>
                <b>{marker.get('label', 'Location')}</b><br>
                <small style='color: #64748b;'>
                    📍 {marker['lat']:.5f}, {marker['lon']:.5f}
                </small>
            </div>
            """

            folium.Marker(
                location=[marker['lat'], marker['lon']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=marker.get('label', 'Location'),
                icon=folium.Icon(
                    color=folium_color,
                    icon=folium_icon,
                    prefix='fa'
                )
            ).add_to(add_to)

    # Add instruction box
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; 
                background: rgba(30, 41, 59, 0.95);
                padding: 12px 16px;
                border-radius: 8px;
                border: 1px solid #475569;
                z-index: 9999;
                font-family: Arial;
                color: #e8eaf6;
                font-size: 13px;
                max-width: 250px;">
        <b>📍 {label}</b><br>
        <small>👆 Click anywhere on map<br>
        🔍 Or use search box<br>
        📱 Or click "locate me"</small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Render map and capture clicks
    from streamlit_folium import st_folium

    map_data = st_folium(
        m,
        width=None,
        height=height,
        returned_objects=["last_clicked", "all_drawings", "last_object_clicked"],
        key=f"map_{theme}_{hash(str(existing_markers))}"  # ✅ Unique key per theme
    )

    return map_data

def get_clicked_location(map_data):
    """
    Extract lat/lon from map click or drawn marker
    Returns: (lat, lon) tuple or None
    """

    # Priority 1: User clicked on map directly
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        return (lat, lon)

    # Priority 2: User drew a marker using draw tools
    if map_data and map_data.get("all_drawings"):
        drawings = map_data["all_drawings"]
        if drawings and len(drawings) > 0:
            last_drawing = drawings[-1]  # Get most recent
            if last_drawing.get("geometry") and last_drawing["geometry"].get("type") == "Point":
                coords = last_drawing["geometry"]["coordinates"]
                return (coords[1], coords[0])  # [lon, lat] → (lat, lon)

    return None


def render_confirmation_map(lat, lon, label="Selected Location", zoom=16):
    """
    Show small confirmation map with selected location
    """
    confirm_map = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles='CartoDB dark_matter',
        scrollWheelZoom=False,
        dragging=False
    )

    folium.Marker(
        [lat, lon],
        popup=label,
        tooltip=label,
        icon=folium.Icon(color='red', icon='map-pin', prefix='fa')
    ).add_to(confirm_map)

    return st_folium(confirm_map, height=300, returned_objects=[])


# utils/map_picker.py - UPDATE render_route_map()

def render_route_map_enhanced(origin, destination, route_data=None, zoom=13, show_alternatives=True):
    """
    Enhanced route visualization with multiple routes and turn-by-turn

    Args:
        origin: (lat, lon, label) tuple
        destination: (lat, lon, label) tuple
        route_data: dict from get_directions_with_alternatives()
        zoom: Initial zoom
        show_alternatives: Show alternative routes
    """
    from folium.plugins import BeautifyIcon
    import folium
    from streamlit_folium import st_folium

    # Calculate center
    center_lat = (origin[0] + destination[0]) / 2
    center_lon = (origin[1] + destination[1]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='CartoDB dark_matter'
    )

    # Origin marker (volunteer)
    folium.Marker(
        location=origin[:2],
        popup=f'<b>🚗 Start</b><br>{origin[2] if len(origin) > 2 else "Your Location"}',
        tooltip='Start Location',
        icon=folium.Icon(color='green', icon='play-circle', prefix='fa')
    ).add_to(m)

    # Destination marker (SOS)
    folium.Marker(
        location=destination[:2],
        popup=f'<b>🚨 Emergency</b><br>{destination[2] if len(destination) > 2 else "Destination"}',
        tooltip='Emergency Location',
        icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
    ).add_to(m)

    # Draw routes
    if route_data and route_data.get("success"):
        routes = route_data["routes"]

        # Color palette for routes
        route_colors = ['#6366f1', '#8b5cf6', '#ec4899']

        for idx, route in enumerate(routes):
            if idx > 0 and not show_alternatives:
                break  # Only show fastest route

            color = route_colors[idx % len(route_colors)]
            weight = 6 if idx == 0 else 4
            opacity = 0.9 if idx == 0 else 0.5

            # Route line
            folium.PolyLine(
                locations=route["coordinates"],
                color=color,
                weight=weight,
                opacity=opacity,
                popup=f"""
                <div style='font-family: Arial; min-width: 200px;'>
                    <b>{'⚡ Fastest Route' if route['is_fastest'] else f'Alternative {idx}'}</b><br>
                    📏 {route['distance_text']}<br>
                    ⏱️ {route['duration_text']}<br>
                    {'🚦 Recommended' if route['is_fastest'] else ''}
                </div>
                """
            ).add_to(m)

            # Add waypoint markers for turn-by-turn
            if idx == 0:  # Only for main route
                for step_idx, step in enumerate(route["steps"][:10]):  # First 10 turns
                    if step_idx < len(route["coordinates"]) - 1:
                        coord_idx = int((step_idx / len(route["steps"])) * len(route["coordinates"]))
                        if coord_idx < len(route["coordinates"]):
                            folium.CircleMarker(
                                location=route["coordinates"][coord_idx],
                                radius=4,
                                color='white',
                                fill=True,
                                fillColor=color,
                                fillOpacity=0.8,
                                popup=f"<small>{step['instruction']}<br>{step['distance'] / 1000:.1f} km</small>"
                            ).add_to(m)

        # Info panel
        main_route = routes[0]
        info_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 50px;
                    background: rgba(30, 41, 59, 0.98);
                    padding: 16px;
                    border-radius: 12px;
                    border: 2px solid #6366f1;
                    z-index: 9999;
                    font-family: 'Segoe UI', Arial;
                    color: #e8eaf6;
                    min-width: 250px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
            <div style="font-size: 16px; font-weight: 700; margin-bottom: 12px; color: #6366f1;">
                ⚡ Fastest Route
            </div>
            <div style="margin-bottom: 8px;">
                <span style="color: #94a3b8;">📏 Distance:</span> 
                <strong style="color: #fff;">{main_route['distance_text']}</strong>
            </div>
            <div style="margin-bottom: 8px;">
                <span style="color: #94a3b8;">⏱️ Duration:</span> 
                <strong style="color: #fff;">{main_route['duration_text']}</strong>
            </div>
            {f'<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #475569; font-size: 13px;"><span style="color: #94a3b8;">{len(routes) - 1} alternative routes available</span></div>' if len(routes) > 1 and show_alternatives else ''}
        </div>
        """
        m.get_root().html.add_child(folium.Element(info_html))

        # Turn-by-turn panel (collapsible)
        if main_route.get("steps"):
            steps_html = "<ul style='margin: 0; padding-left: 20px; max-height: 200px; overflow-y: auto;'>"
            for step in main_route["steps"][:8]:  # First 8 steps
                icon = "➡️" if "right" in step["type"] else "⬅️" if "left" in step["type"] else "⬆️"
                steps_html += f"<li style='margin: 4px 0; font-size: 12px;'>{icon} {step['instruction']} <small style='color: #94a3b8;'>({step['distance'] / 1000:.1f} km)</small></li>"
            steps_html += "</ul>"

            instructions_html = f"""
            <div style="position: fixed; 
                        bottom: 20px; left: 50px;
                        background: rgba(30, 41, 59, 0.98);
                        padding: 16px;
                        border-radius: 12px;
                        border: 1px solid #475569;
                        z-index: 9999;
                        font-family: 'Segoe UI', Arial;
                        color: #e8eaf6;
                        max-width: 350px;">
                <div style="font-weight: 700; margin-bottom: 8px;">🗺️ Turn-by-Turn Directions</div>
                {steps_html}
            </div>
            """
            m.get_root().html.add_child(folium.Element(instructions_html))

    else:
        # Fallback: straight line
        folium.PolyLine(
            locations=[origin[:2], destination[:2]],
            color='#f59e0b',
            weight=3,
            opacity=0.6,
            dash_array='5, 10',
            popup='Direct line (route unavailable)'
        ).add_to(m)

    # Fit bounds
    m.fit_bounds([origin[:2], destination[:2]])

    return st_folium(m, height=600, returned_objects=[])