# pages/emergency_sos.py - UPDATED WITH IMAGE/VIDEO DISPLAY

import streamlit as st
import pandas as pd
import datetime as dt
import time
import uuid
import base64
from utils import storage, notify
from components import page_header, kpi_card, has_role, create_notification, audit_log, encode_file


def decode_and_display_attachment(attachment):
    """Helper to decode and display SOS attachments"""
    if not attachment:
        return

    try:
        # Decode the base64 data
        file_data = base64.b64decode(attachment.get("data", ""))
        file_type = attachment.get("type", "")
        file_name = attachment.get("name", "attachment")

        # Display based on type
        if file_type.startswith("image/"):
            st.image(file_data, caption=file_name, width="stretch")
        elif file_type.startswith("video/"):
            st.video(file_data)
        else:
            st.warning(f"📎 Attachment: {file_name} (unsupported preview)")
    except Exception as e:
        st.error(f"❌ Failed to display attachment: {str(e)}")


@st.cache_resource
def load_map_for_sos():
    """Load mapping libraries for SOS"""
    import pydeck as pdk
    from utils.geo import geocode_place
    from utils.map_picker import create_location_picker, get_clicked_location, render_confirmation_map
    from utils.free_maps import reverse_geocode, search_locations, get_directions, calculate_distance_km

    return {
        'pydeck': pdk,
        'geocode_place': geocode_place,
        'create_location_picker': create_location_picker,
        'get_clicked_location': get_clicked_location,
        'render_confirmation_map': render_confirmation_map,
        'reverse_geocode': reverse_geocode,
        'search_locations': search_locations,
        'get_directions': get_directions,
        'calculate_distance_km': calculate_distance_km
    }


def render():
    """Ultra-enhanced Emergency SOS with MAP PICKER and FULL ADDRESS"""
    user_role = st.session_state.user.get("role")
    page_header("🚨", "Emergency SOS System",
                "Real-time emergency response with precise location marking", user_role)

    # Load map libraries FIRST (before any usage)
    libs = load_map_for_sos()
    create_location_picker = libs['create_location_picker']
    get_clicked_location = libs['get_clicked_location']
    reverse_geocode = libs['reverse_geocode']
    search_locations = libs['search_locations']
    calculate_distance_km = libs['calculate_distance_km']

    # ========== HANDLE DIRECT MAP VIEW FROM EMAIL/SMS LINK ==========
    query_params = st.query_params

    if "sos_id" in query_params and "action" in query_params:
        if query_params["action"] == "view_map":
            sos_id = query_params["sos_id"]

            # Load SOS data
            sos = storage.read("sos", [])
            target_sos = next((s for s in sos if s["id"] == sos_id), None)

            if target_sos:
                st.success(f"🔍 Viewing Emergency: **{sos_id}**")

                coords = target_sos.get("coords")
                if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    # Display emergency details
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("🚨 Severity", target_sos.get("severity", "N/A"))
                    with col2:
                        st.metric("📋 Type", target_sos.get("type", "Emergency"))
                    with col3:
                        st.metric("⏱️ Status", target_sos.get("status", "active").upper())

                    # Show full address
                    full_addr = target_sos.get("full_address") or target_sos.get("place", "Unknown")
                    st.info(f"**📍 Location:** {full_addr}")
                    st.caption(f"**🗺️ Coordinates:** {coords[0]:.6f}, {coords[1]:.6f}")

                    # Show description if available
                    if target_sos.get("desc"):
                        st.markdown("**📝 Description:**")
                        st.write(target_sos["desc"])

                    # ===== DISPLAY ATTACHMENT IF AVAILABLE =====
                    if target_sos.get("attachment"):
                        st.markdown("---")
                        st.markdown("**📸 Attached Media:**")
                        decode_and_display_attachment(target_sos["attachment"])

                    # Display map with marker
                    st.markdown("---")
                    st.markdown("### 🗺️ Emergency Location Map")

                    severity_colors = {
                        "Critical": "#ef4444",
                        "High": "#f59e0b",
                        "Medium": "#10b981"
                    }

                    marker = [{
                        "lat": coords[0],
                        "lon": coords[1],
                        "label": f"🚨 {sos_id}\n{target_sos.get('type', 'Emergency')}\n📍 {full_addr}",
                        "color": severity_colors.get(target_sos.get('severity'), '#64748b'),
                        "icon": "exclamation-triangle"
                    }]

                    create_location_picker(
                        default_lat=coords[0],
                        default_lon=coords[1],
                        zoom=16,
                        existing_markers=marker,
                        height=600,
                        label="Emergency Location",
                        enable_search=False,
                        enable_locate=True
                    )

                    # Action buttons
                    st.markdown("---")
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if has_role("volunteer", "vet", "admin") and target_sos.get("status") == "active":
                            if st.button("✅ ACCEPT EMERGENCY", type="primary", width="stretch"):
                                target_sos["assigned"] = st.session_state.user.get("name")
                                target_sos["status"] = "dispatched"
                                storage.write("sos", sos)
                                st.success("✅ Emergency accepted! Redirecting...")
                                # Clear query params
                                st.query_params.clear()
                                time.sleep(1)
                                st.rerun()

                    with col_b:
                        if st.button("🔙 Back to SOS List", width="stretch"):
                            st.query_params.clear()
                            st.rerun()

                    with col_c:
                        # Copy coordinates button
                        coords_text = f"{coords[0]:.6f}, {coords[1]:.6f}"
                        st.text_input("Copy Coordinates", coords_text, disabled=True, key="coords_copy")

                    # Stop rendering the rest of the page
                    return
                else:
                    st.error("❌ No valid coordinates for this emergency")
                    if st.button("🔙 Back to SOS List"):
                        st.query_params.clear()
                        st.rerun()
                    return
            else:
                st.error(f"❌ Emergency {sos_id} not found")
                if st.button("🔙 Back to SOS List"):
                    st.query_params.clear()
                    st.rerun()
                return

    # Load data
    sos = storage.read("sos", [])
    if not isinstance(sos, list):
        sos = []
        storage.write("sos", sos)

    users = storage.read("users", [])
    volunteers = [u for u in users if u.get("role") == "volunteer"]
    vets = [u for u in users if u.get("role") == "vet"]

    # Helper function
    def get_user_coords(u):
        c = u.get("coords")
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return (float(c[0]), float(c[1]))
        lat, lon = u.get("lat"), u.get("lon")
        if lat is not None and lon is not None:
            return (float(lat), float(lon))
        return None

    # KPI Overview
    st.markdown("### 📊 SOS Overview")
    col1, col2, col3, col4, col5 = st.columns(5)

    total = len(sos)
    active = sum(1 for s in sos if s.get("status") == "active")
    dispatched = sum(1 for s in sos if s.get("status") == "dispatched")
    resolved = sum(1 for s in sos if s.get("status") == "resolved")
    avg_response = 18  # Mock

    with col1:
        kpi_card("Total SOS", total, "All time", "📞", "primary")
    with col2:
        kpi_card("Active", active, "Need response", "🔴", "danger")
    with col3:
        kpi_card("Dispatched", dispatched, "In progress", "🚀", "warning")
    with col4:
        kpi_card("Resolved", resolved, "Completed", "✅", "success")
    with col5:
        kpi_card("Avg Response", f"{avg_response}m", "Target: <20m", "⏱️", "info")

    # ========== CREATE NEW SOS WITH MAP PICKER ==========
    with st.expander("🚨 Create New Emergency SOS", expanded=False):
        st.markdown("### 📍 Step 1: Mark Exact Location")

        # Location selection method
        location_method = st.radio(
            "Choose location method:",
            ["🗺️ Click on Map (Most Accurate)", "🔍 Search Address", "📱 Use My GPS"],
            horizontal=True,
            key="sos_location_method"
        )

        selected_coords = None
        location_name = None
        full_address = None  # NEW: Store complete address

        # ========== METHOD 1: CLICK ON MAP ==========
        if location_method == "🗺️ Click on Map (Most Accurate)":
            st.info("👆 **Click anywhere on the map** to mark the exact emergency location")

            # Show existing SOS markers for context
            existing_sos = []
            for s in sos:
                coords = s.get("coords")
                if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    color = '#ef4444' if s.get('severity') == 'Critical' else '#f59e0b' if s.get(
                        'severity') == 'High' else '#10b981'
                    existing_sos.append({
                        'lat': coords[0],
                        'lon': coords[1],
                        'label': f"SOS: {s['id']} ({s.get('severity', 'N/A')})",
                        'color': color,
                        'icon': 'exclamation-triangle'
                    })

            # Render interactive map picker
            map_data = create_location_picker(
                existing_markers=existing_sos,
                label="Click to mark emergency location",
                height=500
            )

            # Get clicked location
            clicked = get_clicked_location(map_data)

            if clicked:
                selected_coords = clicked

                # Show selected location
                col_a, col_b = st.columns([2, 1])

                with col_a:
                    st.success(f"✅ **Location Marked:** {clicked[0]:.6f}, {clicked[1]:.6f}")

                    # Get human-readable address - ENHANCED
                    with st.spinner("🔍 Getting full address..."):
                        address = reverse_geocode(clicked[0], clicked[1])
                        if address:
                            full_address = address
                            location_name = address
                            st.success(f"📍 **Full Address:**")
                            st.info(address)
                        else:
                            full_address = f"Coordinates: {clicked[0]:.6f}, {clicked[1]:.6f}"
                            location_name = full_address
                            st.warning("⚠️ Could not retrieve address, using coordinates")

                with col_b:
                    # Mini confirmation map
                    from utils.map_picker import render_confirmation_map
                    with st.expander("🗺️ Preview"):
                        render_confirmation_map(clicked[0], clicked[1], "Emergency Location")
            else:
                st.warning("⚠️ Please click on the map to select location")

        # ========== METHOD 2: SEARCH ADDRESS ==========
        elif location_method == "🔍 Search Address":
            # Initialize session state for search results
            if "sos_search_results" not in st.session_state:
                st.session_state.sos_search_results = None
            if "sos_selected_location" not in st.session_state:
                st.session_state.sos_selected_location = None

            search_query = st.text_input(
                "🔍 Search for location",
                placeholder="Type location name (e.g., Anna Nagar, Chennai)",
                key="sos_search"
            )

            # Perform search when query changes
            if search_query and len(search_query) >= 3:
                if st.session_state.sos_search_results is None or st.session_state.get(
                        "last_search_query") != search_query:
                    with st.spinner("🔍 Searching locations..."):
                        results = search_locations(search_query, limit=5)
                        st.session_state.sos_search_results = results
                        st.session_state.last_search_query = search_query

            # Check if location was selected
            if st.session_state.sos_selected_location:
                selected_coords = st.session_state.sos_selected_location["coords"]
                full_address = st.session_state.sos_selected_location["address"]
                location_name = st.session_state.sos_selected_location["address"]

                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.success(f"✅ Selected: {full_address}")
                    st.info(f"📍 Coordinates: {selected_coords[0]:.6f}, {selected_coords[1]:.6f}")
                with col_b:
                    if st.button("🔄 Search Again", key="clear_sos_selection"):
                        st.session_state.sos_selected_location = None
                        st.session_state.sos_search_results = None
                        st.rerun()

            # Display search results
            elif st.session_state.sos_search_results:
                results = st.session_state.sos_search_results

                if results:
                    st.markdown("**📍 Select from results:**")

                    for idx, result in enumerate(results):
                        col1, col2 = st.columns([5, 1])

                        with col1:
                            st.write(f"📍 {result['name']}")
                            st.caption(f"📍 {result['lat']:.5f}, {result['lon']:.5f}")

                        with col2:
                            if st.button("Select", key=f"select_sos_{idx}", type="primary"):
                                # Store selection in session state
                                st.session_state.sos_selected_location = {
                                    "coords": (result['lat'], result['lon']),
                                    "address": result['name']
                                }
                                st.rerun()
                else:
                    st.warning("❌ No results found. Try different keywords or use map click.")

            elif not search_query:
                st.info("💡 Type at least 3 characters to search")
            elif len(search_query) < 3:
                st.info("💡 Type at least 3 characters to search")

        # ========== METHOD 3: USE GPS ==========
        else:  # Use My GPS
            st.info("📱 **Click the '📍 Show my location' button** on the map below")
            st.caption("Your browser will ask permission to access your location")

            map_data = create_location_picker(
                label="Use your current location",
                height=400,
                enable_locate=True
            )

            clicked = get_clicked_location(map_data)
            if clicked:
                selected_coords = clicked
                with st.spinner("🔍 Getting your full address..."):
                    address = reverse_geocode(clicked[0], clicked[1])
                    if address:
                        full_address = address
                        location_name = address
                        st.success(f"✅ **Your location:**")
                        st.info(address)
                    else:
                        full_address = f"GPS: {clicked[0]:.6f}, {clicked[1]:.6f}"
                        location_name = full_address
                        st.warning("⚠️ Could not get address")

        # Show warning if no location selected
        # Safely get selected location from session state
        session_location = st.session_state.get("sos_selected_location") or {}

        if not selected_coords and not session_location.get("coords"):
            st.warning("⚠️ **Please select a location** before proceeding to emergency details")

        # Show selected location summary
        final_coords = selected_coords or session_location.get("coords")
        final_address = full_address or session_location.get("address")

        if final_coords and final_address:
            st.markdown("---")
            st.markdown("### ✅ Selected Location Summary")
            st.success(f"**📍 Address:** {final_address}")
            st.info(f"**🗺️ Coordinates:** {final_coords[0]:.6f}, {final_coords[1]:.6f}")
            st.caption(f"**📱 Method:** {location_method}")

            # Update the variables for form submission
            selected_coords = final_coords
            full_address = final_address
            location_name = final_address

        st.markdown("---")
        st.markdown("### 📋 Step 2: Emergency Details")

        # Emergency form
        with st.form("create_sos_form"):
            col1, col2 = st.columns(2)

            with col1:
                severity = st.selectbox("🚨 Severity Level", ["Medium", "High", "Critical"])
                emergency_type = st.selectbox(
                    "📋 Emergency Type",
                    ["Injured Dog", "Aggressive Dog", "Dog in Danger", "Accident", "Disease", "Other"]
                )

            with col2:
                contact = st.text_input("📞 Contact Number", placeholder="Your phone (optional)")
                estimated_dogs = st.number_input("🐕 Number of dogs", 1, 20, 1)

            desc = st.text_area(
                "📝 Describe the emergency",
                placeholder="What happened? Current condition? Any immediate dangers?",
                height=100
            )

            media = st.file_uploader(
                "📷 Attach Photo/Video (Optional)",
                type=["jpg", "jpeg", "png", "mp4"],
                help="Photos help responders prepare better"
            )

            col_a, col_b = st.columns(2)

            with col_a:
                submit = st.form_submit_button(
                    "🚨 CREATE SOS ALERT",
                    type="primary",
                    width="stretch",
                    disabled=(selected_coords is None)
                )

            with col_b:
                if st.form_submit_button("❌ Cancel", width="stretch"):
                    st.rerun()

            # Handle submission
            if submit and selected_coords:
                sid = f"SOS-{int(time.time())}"

                # Handle media
                attachment = None
                if media:
                    attachment = {
                        "name": media.name,
                        "type": media.type,
                        "data": encode_file(media.getvalue())
                    }

                severity_scores = {"Medium": 50, "High": 75, "Critical": 90}

                # Create SOS with FULL ADDRESS
                new_sos = {
                    "id": sid,
                    "risk": severity_scores[severity],
                    "status": "active",
                    "time": str(dt.datetime.now()),
                    "place": location_name or f"{selected_coords[0]:.5f}, {selected_coords[1]:.5f}",
                    "full_address": full_address or location_name,  # NEW: Store full address
                    "severity": severity,
                    "type": emergency_type,
                    "desc": desc,
                    "contact": contact,
                    "created_by": st.session_state.user.get("name"),
                    "role": st.session_state.user.get("role"),
                    "coords": selected_coords,
                    "attachment": attachment,
                    "assigned": None,
                    "location_method": location_method,
                    "estimated_dogs": estimated_dogs
                }

                sos.insert(0, new_sos)
                storage.write("sos", sos)

                # Create task
                tasks = storage.read("tasks", [])
                tasks.append({
                    "id": f"TASK-{sid}",
                    "sos_id": sid,
                    "place": full_address or location_name or "Unknown",
                    "severity": severity,
                    "desc": desc,
                    "volunteer": None,
                    "status": "pending",
                    "time": str(dt.datetime.now())
                })
                storage.write("tasks", tasks)

                # Update hotspot
                hotspots = storage.read("hotspots", [])
                hotspots.append({
                    "lat": selected_coords[0],
                    "lon": selected_coords[1],
                    "intensity": severity_scores[severity] / 100,
                    "label": f"SOS: {emergency_type}",
                    "category": "Emergency",
                    "created_at": str(dt.datetime.now())
                })
                storage.write("hotspots", hotspots)

                # ========== ENHANCED NOTIFICATIONS WITH SMART MAP LINKS ==========
                responders = [u for u in users if u.get("role") in ["volunteer", "vet", "admin"]]
                notification_count = 0
                email_sent = 0
                sms_sent = 0
                failed_notifications = []
                notified_users = []

                # Create Google Maps coordinates link (more reliable than full address)
                # Using geo: URI scheme which opens default maps app on mobile
                maps_coords = f"{selected_coords[0]},{selected_coords[1]}"

                for user in responders:
                    user_email = user.get("email")
                    user_phone = user.get("phone")
                    user_name = user.get("name", "Responder")
                    user_role = user.get("role", "unknown")

                    user_notified = False

                    # EMAIL NOTIFICATION - Send to ALL responders with email
                    if user_email:  # If email exists and not empty after strip
                        try:
                            notify.send_email(
                                user_email,
                                f"🚨 EMERGENCY: {sid}",
                                f"""
                                <h2 style="color: #ef4444;">🚨 NEW EMERGENCY ALERT</h2>
                                <div style="background: #fee2e2; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444;">
                                    <p><strong>🆔 SOS ID:</strong> {sid}</p>
                                    <p><strong>📋 Type:</strong> {emergency_type}</p>
                                    <p><strong>⚠️ Severity:</strong> <span style="color: #ef4444; font-weight: bold; font-size: 18px;">{severity}</span></p>

                                    <hr style="border: none; border-top: 2px solid #fecaca; margin: 16px 0;">

                                    <h3 style="color: #dc2626; margin-top: 16px;">📍 LOCATION DETAILS</h3>
                                    <div style="background: white; padding: 16px; border-radius: 8px; margin: 12px 0;">
                                        <p style="margin: 8px 0;"><strong>📍 Emergency Location:</strong></p>
                                        <p style="font-size: 16px; color: #1e293b; font-weight: 600; margin: 4px 0 12px 0;">
                                            {full_address or location_name}
                                        </p>

                                        <div style="background: #dbeafe; padding: 12px; border-radius: 6px; margin: 12px 0;">
                                            <p style="margin: 0 0 8px 0; color: #1e40af; font-weight: 600;">🗺️ Navigate to Location:</p>
                                            <a href="geo:{maps_coords}" 
                                               style="display: inline-block; padding: 10px 20px; 
                                                      background: #2563eb; color: white; text-decoration: none; 
                                                      border-radius: 6px; font-weight: 600; margin-right: 8px;">
                                                📱 Open in Maps App
                                            </a>
                                            <p style="margin: 8px 0 0 0; font-size: 11px; color: #64748b;">
                                                Works with Google Maps, Apple Maps, or default maps app
                                            </p>
                                        </div>

                                        <p style="margin: 12px 0 4px 0;"><strong>🗺️ Coordinates (if needed):</strong></p>
                                        <p style="font-size: 14px; color: #475569; font-family: monospace;">{selected_coords[0]:.6f}, {selected_coords[1]:.6f}</p>

                                        <p style="margin: 12px 0 4px 0;"><strong>📱 Location Method:</strong> {location_method}</p>
                                    </div>

                                    <hr style="border: none; border-top: 2px solid #fecaca; margin: 16px 0;">

                                    <p><strong>📝 Description:</strong> {desc or 'No description provided'}</p>
                                    <p><strong>🐕 Estimated Dogs:</strong> {estimated_dogs}</p>
                                    {f"<p><strong>📞 Contact:</strong> {contact}</p>" if contact else ""}
                                    <p><strong>👤 Reported by:</strong> {st.session_state.user.get('name')} ({st.session_state.user.get('role')})</p>
                                    <p><strong>🕐 Time:</strong> {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                                </div>

                                <div style="background: #fef3c7; padding: 16px; border-radius: 8px; margin-top: 16px; border-left: 4px solid #f59e0b;">
                                    <p style="margin: 0;"><strong>⚡ ACTION REQUIRED:</strong></p>
                                    <p style="margin: 8px 0 0 0;">Click "Open in Maps App" button above to start navigation, then login to SafePaws AI to accept this emergency.</p>
                                </div>

                                <p style="margin-top: 16px; font-size: 12px; color: #64748b;">
                                    The maps button works on all devices and opens your default navigation app.
                                </p>
                                """
                            )
                            email_sent += 1
                            user_notified = True
                            notified_users.append(f"✅ {user_name} ({user_role}) - Email sent to {user_email}")
                        except Exception as e:
                            failed_notifications.append(
                                f"❌ Email to {user_name} ({user_role} - {user_email}): {str(e)}")
                    else:
                        failed_notifications.append(f"⚠️ {user_name} ({user_role}): No email address")

                    # SMS NOTIFICATION - Send to ALL responders with phone
                    if user_phone:  # If phone exists and not empty after strip
                        try:
                            # Create place name for SMS
                            place_short = full_address if full_address and len(full_address) < 50 else (
                                location_name if location_name and len(location_name) < 50 else "Emergency Location"
                            )

                            # Use geo: URI which works across all platforms without triggering Twilio filters
                            notify.send_sms(
                                user_phone,
                                f"🚨 URGENT SOS {sid}\n{emergency_type} - {severity}\nCoords: {maps_coords}\nLogin to SafePaws to accept!"
                            )
                            sms_sent += 1
                            user_notified = True
                            notified_users.append(f"✅ {user_name} ({user_role}) - SMS sent to {user_phone}")
                        except Exception as e:
                            failed_notifications.append(f"❌ SMS to {user_name} ({user_role} - {user_phone}): {str(e)}")
                    else:
                        failed_notifications.append(f"⚠️ {user_name} ({user_role}): No phone number")

                    if user_notified:
                        notification_count += 1

                create_notification(
                    "emergency",
                    f"🚨 NEW SOS: {sid} ({severity}) @ {full_address or location_name}",
                    "high"
                )

                # Display notification summary
                st.success(f"✅ **SOS {sid} created successfully!**")
                st.info(f"📍 **Location:** {full_address or location_name}")

                # Show detailed notification report
                col_notify1, col_notify2, col_notify3 = st.columns(3)
                with col_notify1:
                    st.metric("📧 Emails Sent", email_sent, f"of {len(responders)} responders")
                with col_notify2:
                    st.metric("📱 SMS Sent", sms_sent)
                with col_notify3:
                    st.metric("👥 Users Notified", notification_count, f"of {len(responders)} total")

                # Show WHO was notified
                if notified_users:
                    with st.expander("✅ Successfully Notified Users", expanded=True):
                        for notification in notified_users:
                            st.success(notification)

                # Show failed notifications if any
                if failed_notifications:
                    with st.expander("⚠️ Notification Issues", expanded=True):
                        for fail in failed_notifications:
                            if fail.startswith("❌"):
                                st.error(fail)
                            else:
                                st.warning(fail)

                st.balloons()

                audit_log("SOS_CREATE", {
                    "id": sid,
                    "severity": severity,
                    "coords": selected_coords,
                    "full_address": full_address,
                    "method": location_method,
                    "notified": notification_count
                })

                time.sleep(2)
                st.rerun()

    # ========== DISPLAY ACTIVE SOS MAP ==========
    if sos:
        st.markdown("### 🗺️ Active SOS Locations")

        # Filter active SOS
        active_sos_list = [s for s in sos if s.get("status") in ["active", "dispatched"]]

        if active_sos_list:
            # Prepare markers
            sos_markers = []
            for s in active_sos_list:
                coords = s.get("coords")
                if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    severity_colors = {
                        "Critical": "#ef4444",
                        "High": "#f59e0b",
                        "Medium": "#10b981"
                    }

                    # Use full_address if available, fallback to place
                    display_address = s.get("full_address") or s.get("place", "Unknown")

                    sos_markers.append({
                        "lat": coords[0],
                        "lon": coords[1],
                        "label": f"🚨 {s['id']}\n{s.get('type', 'Emergency')}\n📍 {display_address}\nSeverity: {s.get('severity', 'N/A')}\nStatus: {s.get('status', 'N/A')}",
                        "color": severity_colors.get(s.get('severity'), '#64748b'),
                        "icon": "exclamation-triangle"
                    })

            if sos_markers:
                # Calculate center
                avg_lat = sum(m['lat'] for m in sos_markers) / len(sos_markers)
                avg_lon = sum(m['lon'] for m in sos_markers) / len(sos_markers)

                # Render map (view only, no interaction)
                st.markdown(f"**Showing {len(sos_markers)} active SOS locations on map**")
                create_location_picker(
                    default_lat=avg_lat,
                    default_lon=avg_lon,
                    zoom=12,
                    existing_markers=sos_markers,
                    height=500,
                    label="Active Emergency Locations",
                    enable_search=False,
                    enable_locate=False
                )
            else:
                st.info("No active SOS with valid coordinates")
        else:
            st.success("✅ No active emergencies!")

    # ========== SOS LIST ==========
    st.markdown("---")
    st.markdown("### 📋 Emergency List")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["active", "dispatched", "resolved", "closed"],
            default=["active", "dispatched"]
        )

    with col2:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["Critical", "High", "Medium"],
            default=["Critical", "High", "Medium"]
        )

    with col3:
        sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Severity"])

    # Apply filters
    filtered_sos = [
        s for s in sos
        if s.get("status") in status_filter and s.get("severity") in severity_filter
    ]

    # Sort
    if sort_by == "Newest First":
        filtered_sos.sort(key=lambda x: x.get("time", ""), reverse=True)
    elif sort_by == "Oldest First":
        filtered_sos.sort(key=lambda x: x.get("time", ""))
    else:  # Severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2}
        filtered_sos.sort(key=lambda x: severity_order.get(x.get("severity", "Medium"), 3))

    # Display SOS cards
    if filtered_sos:
        for s in filtered_sos:
            severity_color = {
                "Critical": "#ef4444",
                "High": "#f59e0b",
                "Medium": "#10b981"
            }.get(s.get("severity", "Medium"), "#64748b")

            # Get full address or fallback
            display_location = s.get("full_address") or s.get("place", "Unknown")
            coords = s.get("coords")
            coords_display = f"{coords[0]:.5f}, {coords[1]:.5f}" if coords else "No coords"

            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.markdown(f"""
                <div style="padding: 16px; background: rgba(51, 65, 85, 0.3); 
                            border-left: 4px solid {severity_color}; border-radius: 8px;">
                    <strong style="font-size: 18px;">{s['id']}</strong><br>
                    <span style="color: #94a3b8;">
                        🚨 {s.get('type', 'Emergency')} • {s.get('severity', 'N/A')} Severity
                    </span><br>
                    <span style="color: #94a3b8; font-size: 12px;">
                        📍 {display_location}<br>
                        🗺️ {coords_display}<br>
                        🕐 {str(s.get('time', ''))[:16]}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                # ===== ADD IMAGE/VIDEO THUMBNAIL =====
                if s.get("attachment"):
                    with st.expander("📸 View Photo/Video"):
                        decode_and_display_attachment(s["attachment"])

            with col2:
                status_badge_html = {
                    "active": '<span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">ACTIVE</span>',
                    "dispatched": '<span style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">DISPATCHED</span>',
                    "resolved": '<span style="background: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">RESOLVED</span>',
                    "closed": '<span style="background: #64748b; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700;">CLOSED</span>'
                }
                st.markdown(status_badge_html.get(s.get("status", "active"), ""), unsafe_allow_html=True)

                if s.get("assigned"):
                    st.caption(f"👤 Assigned: {s['assigned']}")

            with col3:
                if st.button("📋 Details", key=f"view_{s['id']}"):
                    st.session_state.selected_sos = s['id']

            with col4:
                # ADMIN/VET: Assign volunteers to active SOS
                if has_role("admin", "vet") and s.get("status") == "active":
                    assignee = st.selectbox(
                        "Assign to",
                        [""] + [v.get("name") for v in volunteers + vets],
                        key=f"assign_{s['id']}"
                    )

                    if assignee and st.button("✅", key=f"confirm_{s['id']}"):
                        s["assigned"] = assignee
                        s["status"] = "dispatched"
                        storage.write("sos", sos)

                        if assignee:
                            # Create/update task
                            tasks = storage.read("tasks", [])
                            task_exists = any(t.get("sos_id") == s["id"] for t in tasks)
                            if not task_exists:
                                tasks.append({
                                    "id": f"TASK-{s['id']}",
                                    "sos_id": s["id"],
                                    "place": s.get("full_address") or s.get("place", "Unknown"),
                                    "severity": s.get("severity", "High"),
                                    "desc": s.get("desc", "Emergency response"),
                                    "volunteer": assignee,
                                    "status": "assigned",
                                    "time": str(dt.datetime.now())
                                })
                                storage.write("tasks", tasks)

                        create_notification("info", f"SOS {s['id']} assigned to {assignee}", "normal")
                        st.rerun()

                # VOLUNTEER/VET: Accept active SOS
                elif has_role("volunteer", "vet") and s.get("status") == "active":
                    if st.button("✅ Accept", key=f"accept_{s['id']}", type="primary"):
                        s["assigned"] = st.session_state.user.get("name")
                        s["status"] = "dispatched"
                        storage.write("sos", sos)
                        st.success("✅ SOS accepted!")
                        st.rerun()

                # NEW: MARK AS RESOLVED for dispatched SOS
                elif s.get("status") == "dispatched":
                    # Show who it's assigned to
                    if s.get("assigned"):
                        st.caption(f"👤 {s['assigned']}")

                    # Allow assigned volunteer/vet or admin to resolve
                    can_resolve = (
                            has_role("admin") or
                            (has_role("volunteer", "vet") and s.get("assigned") == st.session_state.user.get("name"))
                    )

                    if can_resolve:
                        if st.button("✅ Resolve", key=f"resolve_{s['id']}", type="primary", use_container_width=True):
                            s["status"] = "resolved"
                            s["resolved_at"] = str(dt.datetime.now())
                            s["resolved_by"] = st.session_state.user.get("name")
                            storage.write("sos", sos)

                            # Update associated task
                            tasks = storage.read("tasks", [])
                            for task in tasks:
                                if task.get("sos_id") == s["id"]:
                                    task["status"] = "completed"
                                    task["completed_at"] = str(dt.datetime.now())
                            storage.write("tasks", tasks)

                            create_notification("success", f"✅ SOS {s['id']} resolved!", "normal")
                            st.success("✅ Emergency resolved!")
                            st.balloons()

                            audit_log("SOS_RESOLVE", {
                                "id": s["id"],
                                "resolved_by": st.session_state.user.get("name"),
                                "time": str(dt.datetime.now())
                            })

                            st.rerun()
                    else:
                        st.info("🔒 Assigned to another volunteer")

                # RESOLVED/CLOSED: Show status only
                elif s.get("status") in ["resolved", "closed"]:
                    if s.get("resolved_by"):
                        st.caption(f"✅ Resolved by: {s['resolved_by']}")
                    if s.get("resolved_at"):
                        st.caption(f"🕐 {s['resolved_at'][:16]}")

        st.markdown("<br>", unsafe_allow_html=True)

    else:
        st.info("No SOS alerts match the filters")

    # ========== DETAILED VIEW MODAL ==========
    if "selected_sos" in st.session_state and st.session_state.selected_sos:
        selected_sos_id = st.session_state.selected_sos
        selected_sos_data = next((s for s in sos if s["id"] == selected_sos_id), None)

        if selected_sos_data:
            st.markdown("---")
            st.markdown(f"### 🔍 Detailed View: {selected_sos_id}")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**🚨 Type:** {selected_sos_data.get('type', 'Emergency')}")
                st.markdown(f"**⚠️ Severity:** {selected_sos_data.get('severity', 'N/A')}")
                st.markdown(
                    f"**📍 Location:** {selected_sos_data.get('full_address') or selected_sos_data.get('place', 'Unknown')}")

                if selected_sos_data.get("coords"):
                    coords = selected_sos_data["coords"]
                    st.markdown(f"**🗺️ Coordinates:** {coords[0]:.6f}, {coords[1]:.6f}")

                st.markdown(f"**📝 Description:** {selected_sos_data.get('desc', 'No description')}")
                st.markdown(f"**🐕 Estimated Dogs:** {selected_sos_data.get('estimated_dogs', 'N/A')}")

                if selected_sos_data.get("contact"):
                    st.markdown(f"**📞 Contact:** {selected_sos_data['contact']}")

                st.markdown(f"**👤 Created by:** {selected_sos_data.get('created_by', 'Unknown')}")
                st.markdown(f"**🕐 Time:** {selected_sos_data.get('time', 'N/A')}")
                st.markdown(f"**📊 Status:** {selected_sos_data.get('status', 'N/A').upper()}")

                if selected_sos_data.get("assigned"):
                    st.markdown(f"**👥 Assigned to:** {selected_sos_data['assigned']}")

            with col2:
                # ===== DISPLAY ATTACHMENT IN DETAIL VIEW =====
                if selected_sos_data.get("attachment"):
                    st.markdown("**📸 Attached Media:**")
                    decode_and_display_attachment(selected_sos_data["attachment"])
                else:
                    st.info("📷 No media attached")

            # Show map if coordinates available
            if selected_sos_data.get("coords"):
                st.markdown("---")
                st.markdown("**🗺️ Location Map:**")
                coords = selected_sos_data["coords"]

                severity_colors = {
                    "Critical": "#ef4444",
                    "High": "#f59e0b",
                    "Medium": "#10b981"
                }

                marker = [{
                    "lat": coords[0],
                    "lon": coords[1],
                    "label": f"🚨 {selected_sos_id}\n{selected_sos_data.get('type', 'Emergency')}",
                    "color": severity_colors.get(selected_sos_data.get('severity'), '#64748b'),
                    "icon": "exclamation-triangle"
                }]

                create_location_picker(
                    default_lat=coords[0],
                    default_lon=coords[1],
                    zoom=15,
                    existing_markers=marker,
                    height=400,
                    label="Emergency Location",
                    enable_search=False,
                    enable_locate=False
                )

            # Close button
            st.markdown("---")
            if st.button("❌ Close Details", width="stretch"):
                del st.session_state.selected_sos
                st.rerun()