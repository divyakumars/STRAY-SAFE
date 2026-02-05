# utils/map_themes.py - COMPLETE FILE (NEW)

"""
Custom map themes for SafePaws AI
"""

import folium

# Custom map styles
MAP_THEMES = {
    "dark": {
        "tiles": "CartoDB dark_matter",
        "name": "🌙 Dark Mode",
        "marker_colors": {
            "primary": "#6366f1",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444"
        }
    },

    "light": {
        "tiles": "CartoDB positron",
        "name": "☀️ Light Mode",
        "marker_colors": {
            "primary": "#3b82f6",
            "success": "#059669",
            "warning": "#d97706",
            "danger": "#dc2626"
        }
    },

    "satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "name": "🛰️ Satellite",
        "attr": "Esri",
        "marker_colors": {
            "primary": "#6366f1",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444"
        }
    },

    "street": {
        "tiles": "OpenStreetMap",
        "name": "🗺️ Street Map",
        "marker_colors": {
            "primary": "#2563eb",
            "success": "#059669",
            "warning": "#d97706",
            "danger": "#dc2626"
        }
    }
}


def create_themed_map(lat, lon, zoom=13, theme="dark", **kwargs):
    """
    Create map with custom theme
    """
    theme_config = MAP_THEMES.get(theme, MAP_THEMES["dark"])

    map_params = {
        "location": [lat, lon],
        "zoom_start": zoom,
        "control_scale": True,
        "prefer_canvas": True
    }

    # Add theme-specific parameters
    if isinstance(theme_config["tiles"], str) and not theme_config["tiles"].startswith("http"):
        map_params["tiles"] = theme_config["tiles"]

    map_params.update(kwargs)

    m = folium.Map(**map_params)

    # Add custom tile layer if URL
    if isinstance(theme_config["tiles"], str) and theme_config["tiles"].startswith("http"):
        folium.TileLayer(
            tiles=theme_config["tiles"],
            attr=theme_config.get("attr", "Custom"),
            name=theme_config["name"]
        ).add_to(m)

    return m, theme_config


def add_custom_legend(m, items):
    """
    Add custom legend to map
    """
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px;
                background: rgba(30, 41, 59, 0.95);
                padding: 16px;
                border-radius: 12px;
                border: 1px solid #475569;
                z-index: 9999;
                font-family: Arial;
                color: #e8eaf6;
                min-width: 200px;">
        <div style="font-weight: 700; margin-bottom: 12px; font-size: 14px;">
            🗺️ Map Legend
        </div>
    """

    for item in items:
        legend_html += f"""
        <div style="display: flex; align-items: center; margin: 8px 0;">
            <span style="width: 20px; height: 20px; background: {item['color']}; 
                        border-radius: 50%; display: inline-block; margin-right: 10px;"></span>
            <span style="font-size: 13px;">{item['label']}</span>
        </div>
        """

    legend_html += "</div>"

    m.get_root().html.add_child(folium.Element(legend_html))
    return m