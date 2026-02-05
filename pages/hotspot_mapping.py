# pages/hotspot_mapping.py - CORRECTED VERSION WITH FIXED DISEASE COUNTING

import streamlit as st
import pandas as pd
import datetime as dt
import time
import uuid
from utils import storage
from components import page_header, kpi_card, has_role, create_notification, audit_log


@st.cache_resource
def load_map_libraries():
    """Load heavy mapping libraries only when needed"""
    import pydeck as pdk
    import folium
    from streamlit_folium import st_folium
    from utils.geo import geocode_place
    from utils.map_themes import create_themed_map, add_custom_legend, MAP_THEMES
    from utils.map_picker import create_location_picker, get_clicked_location
    from utils.free_maps import reverse_geocode

    return {
        'pdk': pdk,
        'folium': folium,
        'st_folium': st_folium,
        'geocode_place': geocode_place,
        'create_themed_map': create_themed_map,
        'add_custom_legend': add_custom_legend,
        'MAP_THEMES': MAP_THEMES,
        'create_location_picker': create_location_picker,
        'get_clicked_location': get_clicked_location,
        'reverse_geocode': reverse_geocode
    }


def render():
    """Enhanced hotspot mapping with DISEASE-BASED visualization"""
    user_role = st.session_state.user.get("role")
    page_header("🗺️", "Hotspot Mapping & Reporting",
                "Real-time geospatial disease tracking with precise location marking", user_role)

    # Load map libraries
    libs = load_map_libraries()
    create_location_picker = libs['create_location_picker']
    get_clicked_location = libs['get_clicked_location']
    reverse_geocode = libs['reverse_geocode']

    # ===== ADD MIGRATION BUTTON HERE =====
    with st.expander("🔧 Data Maintenance Tools"):
        if st.button("Fix Old Hotspot Data (Run Once)", type="secondary"):

            hotspots = storage.read("hotspots", [])
            updated = 0

            for hotspot in hotspots:
                # Add missing location fields
                if "location_name" not in hotspot:
                    hotspot["location_name"] = hotspot.get(
                        "place") or f"Location ({hotspot.get('lat', 0):.4f}, {hotspot.get('lon', 0):.4f})"
                    updated += 1
                if "place" not in hotspot:
                    hotspot["place"] = hotspot.get(
                        "location_name") or f"Location ({hotspot.get('lat', 0):.4f}, {hotspot.get('lon', 0):.4f})"
                    updated += 1

                # Add missing user fields
                if "created_by" not in hotspot:
                    hotspot["created_by"] = hotspot.get("reported_by") or hotspot.get("analyzed_by") or "System"
                    updated += 1
                if "reported_by" not in hotspot:
                    hotspot["reported_by"] = hotspot.get("created_by") or hotspot.get("analyzed_by") or "System"
                    updated += 1

            if updated > 0:
                storage.write("hotspots", hotspots)
                st.success(f"✅ Fixed {updated} fields in old hotspots!")
                st.rerun()
            else:
                st.info("ℹ️ All hotspots already have location and user data")

    st.markdown("---")  # Add a divider

    data = storage.read("hotspots", [])
    df = pd.DataFrame(data) if data else pd.DataFrame()

    # ✅ FIX: Normalize field names from different sources
    if not df.empty:
        # Add created_at if missing
        if "created_at" not in df.columns:
            if "time" in df.columns:
                df["created_at"] = df["time"]
            else:
                df["created_at"] = str(dt.datetime.now())

        # ✅ Normalize location field (AI uses "place", manual uses "location_name")
        if "location_name" not in df.columns and "place" in df.columns:
            df["location_name"] = df["place"]
        elif "place" not in df.columns and "location_name" in df.columns:
            df["place"] = df["location_name"]

        # ✅ Normalize reporter field (AI uses "reported_by", manual uses "created_by")
        if "created_by" not in df.columns and "reported_by" in df.columns:
            df["created_by"] = df["reported_by"]
        elif "reported_by" not in df.columns and "created_by" in df.columns:
            df["reported_by"] = df["created_by"]

        # ✅ CRITICAL: Normalize disease_type values (lowercase, strip spaces)
        if "disease_type" in df.columns:
            df["disease_type"] = df["disease_type"].str.lower().str.strip().str.replace(" ", "_")

        # Convert created_at to datetime
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

        # ✅ Fill NaN values
        df["location_name"] = df["location_name"].fillna("Unknown Location")
        df["place"] = df["place"].fillna("Unknown Location")
        df["created_by"] = df["created_by"].fillna("Unknown User")
        df["reported_by"] = df["reported_by"].fillna("Unknown User")

    # Summary Statistics BY DISEASE TYPE
    st.markdown("### 📊 Hotspot Overview")

    if not df.empty:
        # ✅ FIX: Improved disease counting logic
        disease_df = df[df["category"] == "Disease"].copy()

        if not disease_df.empty and "disease_type" in disease_df.columns:
            # ✅ Count each disease type (already normalized to lowercase with underscores)
            disease_counts = disease_df["disease_type"].value_counts()

            # ✅ DEBUG: Print what we found (for troubleshooting)
            print("Disease counts found:")
            print(disease_counts)
            print(f"Total disease hotspots: {len(disease_df)}")

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                # Look for both "demodicosis" and variations
                demodicosis_count = disease_counts.get("demodicosis", 0)
                kpi_card("Demodicosis", int(demodicosis_count), "Most severe", "🔴", "danger")

            with col2:
                ringworm_count = disease_counts.get("ringworm", 0)
                kpi_card("Ringworm", int(ringworm_count), "Contagious", "🟠", "warning")

            with col3:
                fungal_count = disease_counts.get("fungal_infections", 0)
                kpi_card("Fungal", int(fungal_count), "Requires treatment", "🟡", "info")

            with col4:
                dermatitis_count = disease_counts.get("dermatitis", 0)
                kpi_card("Dermatitis", int(dermatitis_count), "Moderate", "🔵", "primary")

            with col5:
                hyper_count = disease_counts.get("hypersensitivity", 0)
                kpi_card("Hypersensitivity", int(hyper_count), "Allergy", "🟢", "success")
        else:
            # Show generic metrics if no disease data
            col1, col2, col3 = st.columns(3)
            with col1:
                total = len(df)
                kpi_card("Total Hotspots", total, "All categories", "🎯", "primary")
            with col2:
                disease_count = len(df[df["category"] == "Disease"])
                kpi_card("Disease Cases", disease_count, "AI detected", "🦠", "danger")
            with col3:
                bite_count = len(df[df["category"] == "Bite Risk"])
                kpi_card("Bite Risk", bite_count, "High alert", "⚠️", "warning")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            kpi_card("Total Hotspots", 0, "No data", "🎯", "primary")

    # Filters BY DISEASE
    st.markdown("### 🔍 Filter Hotspots")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        show_demodicosis = st.checkbox("🔴 Demodicosis", value=True)
    with col2:
        show_ringworm = st.checkbox("🟠 Ringworm", value=True)
    with col3:
        show_fungal = st.checkbox("🟡 Fungal", value=True)
    with col4:
        show_dermatitis = st.checkbox("🔵 Dermatitis", value=True)
    with col5:
        show_hyper = st.checkbox("🟢 Hypersensitivity", value=True)

    col6, col7, col8 = st.columns(3)
    with col6:
        show_biterisk = st.checkbox("⚠️ Bite Risk", value=True)
    with col7:
        show_manual = st.checkbox("📍 Manual", value=True)
    with col8:
        time_filter = st.selectbox("Time Range", ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"])

    # Apply filters
    disease_filters = []
    if show_demodicosis: disease_filters.append("demodicosis")
    if show_ringworm: disease_filters.append("ringworm")
    if show_fungal: disease_filters.append("fungal_infections")
    if show_dermatitis: disease_filters.append("dermatitis")
    if show_hyper: disease_filters.append("hypersensitivity")

    df_filtered = df.copy() if not df.empty else pd.DataFrame()

    if not df_filtered.empty:
        # ✅ FIX: Improved filter logic
        mask = pd.Series([False] * len(df_filtered))

        # Disease filter
        if disease_filters and "disease_type" in df_filtered.columns:
            disease_mask = df_filtered["disease_type"].str.lower().isin([d.lower() for d in disease_filters])
            disease_mask = disease_mask & (df_filtered["category"] == "Disease")
            mask = mask | disease_mask

        # Other category filters
        if show_biterisk:
            mask = mask | (df_filtered["category"] == "Bite Risk")
        if show_manual:
            mask = mask | (df_filtered["category"] == "Manual")

        df_filtered = df_filtered[mask].copy()

        # Time filter
        if not df_filtered.empty and time_filter != "All Time":
            now = dt.datetime.now()
            days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
            cutoff = now - dt.timedelta(days=days_map[time_filter])
            df_filtered = df_filtered[df_filtered["created_at"] >= cutoff]

    # ========== DISPLAY HOTSPOTS MAP WITH DISEASE COLORS ==========
    st.markdown("### 🗺️ Interactive Disease Hotspot Map")

    if not df_filtered.empty:
        # Prepare markers with disease-specific colors
        hotspot_markers = []
        for _, row in df_filtered.iterrows():
            # ✅ FIX: Proper color and icon mapping
            if row.get("category") == "Disease":
                disease_type = str(row.get("disease_type", "")).lower().strip()

                disease_colors = {
                    "demodicosis": "#ef4444",  # Red
                    "ringworm": "#f59e0b",  # Orange
                    "fungal_infections": "#eab308",  # Yellow
                    "dermatitis": "#3b82f6",  # Blue
                    "hypersensitivity": "#10b981"  # Green
                }

                color = disease_colors.get(disease_type, "#64748b")
                icon = "virus"

            elif row.get("category") == "Bite Risk":
                color = "#ef4444" if row.get("risk_score", 0) >= 70 else "#f59e0b"
                icon = "warning"
            else:
                color = "#64748b"
                icon = "map-marker"

            # ✅ Create label with disease info - FIXED
            disease_type_val = row.get("disease_type")

            # Check if disease_type is a valid string
            if disease_type_val and isinstance(disease_type_val, str) and str(disease_type_val).strip():
                disease_type = str(disease_type_val).replace("_", " ")
                confidence = row.get('confidence', 0)
                severity = row.get('severity', 'Unknown')
                label_text = f"{disease_type.title()}: {severity} ({confidence * 100:.0f}%)"
            elif row.get("label"):
                label_text = row["label"]
            else:
                label_text = "Hotspot"

            hotspot_markers.append({
                "lat": row["lat"],
                "lon": row["lon"],
                "label": label_text,
                "color": color,
                "icon": icon
            })

        # Calculate center
        center_lat = df_filtered["lat"].mean()
        center_lon = df_filtered["lon"].mean()

        # Render map
        create_location_picker(
            default_lat=center_lat,
            default_lon=center_lon,
            zoom=12,
            existing_markers=hotspot_markers,
            height=600,
            label=f"Viewing {len(hotspot_markers)} hotspots",
            enable_search=True,
            enable_locate=False
        )

        st.success(f"🗺️ Showing {len(hotspot_markers)} hotspots (100% FREE - OpenStreetMap)")

        # Enhanced Legend with disease types
        st.markdown("""
        <div style="padding: 16px; background: rgba(51, 65, 85, 0.5); border-radius: 12px; margin-top: 16px;">
            <strong>🗺️ Disease Map Legend</strong><br><br>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div><span style="color: #ef4444; font-size: 20px;">●</span> Demodicosis (Severe)</div>
                <div><span style="color: #f59e0b; font-size: 20px;">●</span> Ringworm (Contagious)</div>
                <div><span style="color: #eab308; font-size: 20px;">●</span> Fungal Infections</div>
                <div><span style="color: #3b82f6; font-size: 20px;">●</span> Dermatitis (Moderate)</div>
                <div><span style="color: #10b981; font-size: 20px;">●</span> Hypersensitivity (Mild)</div>
                <div><span style="color: #64748b; font-size: 20px;">●</span> Manual Report</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ✅ Disease statistics table with proper handling
        st.markdown("---")
        st.markdown("### 📊 Disease Distribution")

        disease_df_filtered = df_filtered[df_filtered["category"] == "Disease"]

        if not disease_df_filtered.empty and "disease_type" in disease_df_filtered.columns:
            # Group by disease type and aggregate
            disease_stats = disease_df_filtered.groupby("disease_type").agg({
                "severity": lambda x: x.mode()[0] if len(x.mode()) > 0 else "Unknown",
                "confidence": "mean",
                "id": "count"
            }).reset_index()

            disease_stats.columns = ["Disease", "Common Severity", "Avg Confidence", "Count"]
            disease_stats["Disease"] = disease_stats["Disease"].str.replace("_", " ").str.title()
            disease_stats["Avg Confidence"] = disease_stats["Avg Confidence"].apply(lambda x: f"{x * 100:.1f}%")
            disease_stats = disease_stats.sort_values("Count", ascending=False)

            st.dataframe(disease_stats, use_container_width=True, hide_index=True)
        else:
            st.info("No disease hotspots to display statistics")

        # ✅ Recent Hotspots with proper field display
        st.markdown("---")
        st.markdown("### 📋 Recent Hotspots")

        recent = df_filtered.sort_values("created_at", ascending=False).head(10)

        for _, row in recent.iterrows():
            category_emoji = {
                "Disease": "🦠",
                "Bite Risk": "⚠️",
                "Feeding Area": "🍲",
                "Accident Prone": "🚨",
                "Manual": "📍"
            }

            emoji = category_emoji.get(row.get("category"), "📍")

            # ✅ ENHANCED: Get location with MULTIPLE fallbacks
            location = (
                    row.get("location_name") or
                    row.get("place") or
                    row.get("location") or  # Fallback for old records
                    f"Coordinates ({row.get('lat', 0):.4f}, {row.get('lon', 0):.4f})"
            # Show coordinates if nothing else
            )

            # ✅ ENHANCED: Get reporter with MULTIPLE fallbacks
            reporter = (
                    row.get("created_by") or
                    row.get("reported_by") or
                    row.get("analyzed_by") or  # Disease detections use this
                    row.get("assessed_by") or  # Bite risk assessments use this
                    "AI System"  # Better than "Unknown User"
            )

            # ✅ Get label - FIXED to handle NaN/float values
            disease_type = row.get("disease_type")

            # Check if disease_type is a valid string (not NaN or None)
            if disease_type and isinstance(disease_type, str) and str(disease_type).strip():
                label = f"{disease_type.replace('_', ' ').title()} ({row.get('severity', 'Unknown')})"
            else:
                # For bite risk and other categories, use the label field
                label = row.get("label", "Hotspot")

            # ✅ Get timestamp
            timestamp = str(row.get("created_at", ""))[:16] if pd.notna(row.get("created_at")) else "Unknown"

            st.markdown(f"""
            <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                        border-radius: 8px; margin-bottom: 8px;">
                {emoji} <strong>{label}</strong><br>
                <span style="color: #94a3b8; font-size: 12px;">
                    📍 {location} • 
                    🕒 {timestamp} •
                    👤 {reporter}
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🗺️ No hotspots match your filters")

    # ========== REPORT NEW HOTSPOT WITH MAP PICKER ==========
    st.markdown("---")
    st.markdown("### 📍 Report New Hotspot")

    st.info("👆 **Click on the map below** to mark the exact hotspot location")

    # Show existing hotspots on picker
    existing_markers = []
    for h in data:
        color_map = {
            "Bite Risk": "#ef4444" if h.get("risk_score", 0) >= 70 else "#f59e0b",
            "Disease": "#3b82f6",
            "Manual": "#64748b"
        }
        existing_markers.append({
            "lat": h["lat"],
            "lon": h["lon"],
            "label": h.get("label", "Hotspot"),
            "color": color_map.get(h.get("category", "Manual"), "#64748b"),
            "icon": "map-marker"
        })

    # Interactive map for new hotspot
    map_data = create_location_picker(
        existing_markers=existing_markers,
        label="Click to mark new hotspot",
        height=500,
        enable_search=True,
        enable_locate=True
    )

    # Get clicked location
    selected_coords = get_clicked_location(map_data)

    if selected_coords:
        st.success(f"✅ **Location Selected:** {selected_coords[0]:.6f}, {selected_coords[1]:.6f}")

        # Get address
        with st.spinner("🌐 Getting address..."):
            location_name = reverse_geocode(selected_coords[0], selected_coords[1])
            if location_name:
                st.info(f"📍 **Address:** {location_name}")
            else:
                location_name = f"Location: {selected_coords[0]:.5f}, {selected_coords[1]:.5f}"
                st.warning("⚠️ Address not found, using coordinates")

        # Hotspot details form
        with st.form("report_hotspot_form"):
            st.markdown("#### Hotspot Details")

            col1, col2 = st.columns(2)

            with col1:
                category = st.selectbox(
                    "Category",
                    ["Disease", "Bite Risk", "Feeding Area", "Accident Prone", "Other"]
                )

                if category == "Disease":
                    disease_type = st.selectbox(
                        "Disease Type",
                        ["Demodicosis", "Ringworm", "Fungal Infections", "Dermatitis", "Hypersensitivity", "Unknown"]
                    )
                    severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe"])
                elif category == "Bite Risk":
                    risk_level = st.slider("Risk Level", 0, 100, 50)
                else:
                    disease_type = None
                    severity = None
                    risk_level = None

            with col2:
                intensity = st.slider("Intensity (0-100)", 0, 100, 50)
                estimated_dogs = st.number_input("Estimated Dogs", 1, 50, 1)

            description = st.text_area(
                "Description",
                placeholder="Describe the situation, symptoms, behavior, etc.",
                height=100
            )

            photos = st.file_uploader(
                "📷 Attach Photos (Optional)",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True
            )

            submitted = st.form_submit_button("📍 Report Hotspot", type="primary", use_container_width=True)

            if submitted:
                # ✅ Create hotspot with all required fields
                hotspot_id = f"HS-{int(dt.datetime.now().timestamp())}-{uuid.uuid4().hex[:4]}"

                new_hotspot = {
                    "id": hotspot_id,
                    "lat": selected_coords[0],
                    "lon": selected_coords[1],
                    "intensity": intensity / 100,
                    "label": description[:50] if description else f"{category} Hotspot",
                    "category": category,
                    "location_name": location_name,  # ✅ For manual reports
                    "place": location_name,  # ✅ For consistency with AI reports
                    "estimated_dogs": estimated_dogs,
                    "description": description,
                    "created_at": str(dt.datetime.now()),
                    "time": str(dt.datetime.now()),  # ✅ For consistency
                    "created_by": st.session_state.user.get("name"),
                    "reported_by": st.session_state.user.get("name"),  # ✅ For consistency
                    "photos": []
                }

                # Add category-specific fields
                if category == "Disease":
                    disease_colors = {
                        "Demodicosis": "#ef4444",
                        "Ringworm": "#f59e0b",
                        "Fungal Infections": "#eab308",
                        "Dermatitis": "#3b82f6",
                        "Hypersensitivity": "#10b981",
                        "Unknown": "#64748b"
                    }

                    # ✅ CRITICAL: Store disease_type in lowercase with underscores
                    new_hotspot.update({
                        "disease_type": disease_type.lower().replace(" ", "_"),
                        "severity": severity,
                        "color": disease_colors.get(disease_type, "#64748b"),
                        "confidence": 0.8  # Manual reports have moderate confidence
                    })
                elif category == "Bite Risk":
                    new_hotspot.update({
                        "risk_score": risk_level,
                        "color": "#ef4444" if risk_level >= 70 else "#f59e0b"
                    })
                else:
                    new_hotspot["color"] = "#64748b"

                # Handle photo uploads
                if photos:
                    from components import encode_file
                    photo_data = []
                    for photo in photos:
                        photo_data.append({
                            "name": photo.name,
                            "data": encode_file(photo.getvalue())
                        })
                    new_hotspot["photos"] = photo_data

                # Save to storage
                data.append(new_hotspot)
                storage.write("hotspots", data)

                # Create notification
                create_notification(
                    "info",
                    f"📍 New {category} hotspot reported at {location_name}",
                    "normal"
                )

                # Audit log
                audit_log("HOTSPOT_REPORT", {
                    "coords": selected_coords,
                    "category": category,
                    "location": location_name
                })

                st.success("✅ Hotspot reported successfully!")
                st.balloons()
                time.sleep(2)
                st.rerun()

    else:
        st.warning("⚠️ Click on the map above to select a location first")

    # ========== HOTSPOT ANALYTICS ==========
    if not df.empty:
        st.markdown("---")
        st.markdown("### 📈 Hotspot Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Hotspots by Category")
            category_counts = df["category"].value_counts().reset_index()
            category_counts.columns = ["Category", "Count"]

            st.bar_chart(category_counts.set_index("Category"))

        with col2:
            st.markdown("#### Top Locations")
            location_counts = df["location_name"].value_counts().head(10).reset_index()
            location_counts.columns = ["Location", "Count"]

            st.dataframe(location_counts, use_container_width=True, hide_index=True)

    # ========== EXPORT OPTIONS ==========
    if not df_filtered.empty and has_role("admin", "vet"):
        st.markdown("---")
        st.markdown("### 📥 Export Data")

        col1, col2 = st.columns(2)

        with col1:
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                file_name=f"hotspots_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            import json
            json_data = df_filtered.to_json(orient="records", indent=2)
            st.download_button(
                "📥 Download JSON",
                json_data,
                file_name=f"hotspots_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True
            )