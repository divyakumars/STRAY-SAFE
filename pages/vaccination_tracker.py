# pages/vaccination_tracker.py - Professional Vaccination Management System

import streamlit as st
import pandas as pd
import datetime as dt
import time
import calendar
import json
from utils import storage
from components import page_header, has_role, create_notification, audit_log, generate_qr_code


def render():
    """Professional vaccination tracker with calendar, maps, and analytics"""
    if not has_role('admin', 'vet', 'volunteer'):
        st.error("⛔ Access Denied: Only admins, vets, and volunteers can access this page")
        return

    user_role = st.session_state.user.get("role")
    user_name = st.session_state.user.get("name", "User")

    # Initialize session state for campaign creation
    if "show_campaign_success" not in st.session_state:
        st.session_state.show_campaign_success = False
    if "new_campaign_id" not in st.session_state:
        st.session_state.new_campaign_id = None
    if "new_campaign_data" not in st.session_state:
        st.session_state.new_campaign_data = None

    page_header("💉", "Vaccination Management System",
                "Professional campaign scheduling, tracking, and analytics", user_role)

    # Load data
    campaigns = storage.read("campaigns", [])
    today = dt.date.today()

    # Normalize campaign data
    for c in campaigns:
        c.setdefault("id", f"VC-{int(time.time() * 1000)}")
        c.setdefault("zone", "Unknown")
        c.setdefault("date", str(today))
        c.setdefault("status", "Scheduled")
        c.setdefault("target", 0)
        c.setdefault("completed", 0)
        c.setdefault("volunteers_assigned", [])
        c.setdefault("location", {"lat": 13.0827, "lon": 80.2707})
        c.setdefault("vaccine_type", "Rabies")
        c.setdefault("time_slot", "09:00-12:00")
        c.setdefault("coordinator", "")

        # Add location name if missing
        if "location_name" not in c:
            loc = c.get("location", {})
            c[
                "location_name"] = f"{c.get('zone', 'Unknown')} Area (Lat {loc.get('lat', 0):.2f}, Lon {loc.get('lon', 0):.2f})"

        # Auto-update status based on date
        try:
            camp_date = dt.date.fromisoformat(str(c["date"]))
            if camp_date < today and c.get("status") == "Scheduled":
                c["status"] = "Overdue"
            elif camp_date == today and c.get("status") == "Scheduled":
                c["status"] = "In Progress"
        except:
            pass

    storage.write("campaigns", campaigns)

    # ==================== TOP METRICS DASHBOARD ====================
    st.markdown("### 📊 Live Dashboard")

    # Calculate real-time metrics
    total_campaigns = len(campaigns)
    scheduled = sum(1 for c in campaigns if c.get("status") == "Scheduled")
    in_progress = sum(1 for c in campaigns if c.get("status") == "In Progress")
    completed = sum(1 for c in campaigns if c.get("status") == "Completed")
    overdue = sum(1 for c in campaigns if c.get("status") == "Overdue")
    total_vaccinated = sum(c.get("completed", 0) for c in campaigns)
    total_target = sum(c.get("target", 0) for c in campaigns)
    completion_rate = (total_vaccinated / total_target * 100) if total_target > 0 else 0

    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Campaigns", total_campaigns, help="All campaigns created")
    with col2:
        st.metric("Dogs Vaccinated", f"{total_vaccinated:,}", help="Total dogs vaccinated")
    with col3:
        st.metric("Completion Rate", f"{completion_rate:.1f}%",
                  delta=f"{total_vaccinated}/{total_target:,}")
    with col4:
        st.metric("Active Today", in_progress, delta="In Progress", delta_color="normal")
    with col5:
        remaining = max(0, total_target - total_vaccinated)
        st.metric("Remaining", f"{remaining:,}", help="Dogs yet to be vaccinated")

    # Status breakdown
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info(f"🟢 **Scheduled**: {scheduled}")
    with col2:
        st.warning(f"🟡 **In Progress**: {in_progress}")
    with col3:
        st.success(f"✅ **Completed**: {completed}")
    with col4:
        if overdue > 0:
            st.error(f"🔴 **Overdue**: {overdue}")
        else:
            st.success(f"✅ **No Overdue Campaigns**")

    # Overall progress bar
    st.markdown("### 🎯 Overall Vaccination Progress")
    progress = min(1.0, total_vaccinated / total_target) if total_target > 0 else 0
    st.progress(progress)
    st.caption(f"{total_vaccinated:,} of {total_target:,} dogs vaccinated ({completion_rate:.1f}% complete)")

    # Notification banner for volunteers/vets about available campaigns
    if user_role in ["volunteer", "vet"]:
        available_to_join = [c for c in campaigns
                             if c.get("status") in ["Scheduled", "In Progress"]
                             and user_name not in c.get("volunteers_assigned", [])
                             and len(c.get("volunteers_assigned", [])) < c.get("volunteers_needed", 0)]

        user_campaigns = [c for c in campaigns if user_name in c.get("volunteers_assigned", [])]

        col1, col2 = st.columns(2)
        with col1:
            if available_to_join:
                st.info(
                    f"🎯 **{len(available_to_join)} campaign(s) need volunteers!** Check the 'Available Campaigns' tab to join.")
        with col2:
            if user_campaigns:
                upcoming_campaigns = [c for c in user_campaigns if c.get("status") == "Scheduled"]
                if upcoming_campaigns:
                    st.success(
                        f"✅ **You're assigned to {len(user_campaigns)} campaign(s)** ({len(upcoming_campaigns)} upcoming)")

    st.markdown("---")

    # ==================== MAIN TABS ====================
    tabs = st.tabs(["📅 Calendar View", "🗺️ Map View", "📋 Campaign List", "📊 Analytics", "➕ Create Campaign",
                    "👥 Available Campaigns"])

    # ==================== TAB 1: CALENDAR VIEW ====================
    with tabs[0]:
        st.markdown("### 📅 Campaign Calendar")

        # Calendar controls
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Month/Year selector
            current_month = st.selectbox(
                "Select Month",
                options=list(range(1, 13)),
                index=today.month - 1,
                format_func=lambda x: calendar.month_name[x]
            )

        with col2:
            current_year = st.selectbox(
                "Select Year",
                options=[2024, 2025, 2026],
                index=1 if today.year == 2025 else 0
            )

        with col3:
            view_mode = st.radio("View", ["Month", "Week"], horizontal=True)

        # Create calendar
        if view_mode == "Month":
            render_month_calendar(campaigns, current_year, current_month)
        else:
            render_week_calendar(campaigns, current_year, current_month)

    # ==================== TAB 2: MAP VIEW ====================
    with tabs[1]:
        st.markdown("### 🗺️ Geographic Coverage Map")

        if campaigns:
            # Get all unique zones dynamically
            unique_zones = list(set(c.get("zone", "Unknown") for c in campaigns))
            unique_zones.sort()

            # Calculate coverage per zone
            zone_data = {}
            for zone_name in unique_zones:
                zone_campaigns = [c for c in campaigns if c.get("zone") == zone_name]
                zone_vaccinated = sum(c.get("completed", 0) for c in zone_campaigns)
                zone_target = sum(c.get("target", 0) for c in zone_campaigns)
                zone_data[zone_name] = {
                    "campaigns": len(zone_campaigns),
                    "vaccinated": zone_vaccinated,
                    "target": zone_target,
                    "coverage": (zone_vaccinated / zone_target * 100) if zone_target > 0 else 0
                }

            # Display zone cards
            st.markdown("#### Zone Coverage Status")

            # Show zones in rows of 5
            zones_list = list(zone_data.items())
            for i in range(0, len(zones_list), 5):
                cols = st.columns(min(5, len(zones_list) - i))
                for idx, (zone_name, zone_info) in enumerate(zones_list[i:i + 5]):
                    with cols[idx]:
                        coverage = zone_info["coverage"]
                        status = "🟢" if coverage >= 80 else "🟡" if coverage >= 50 else "🔴"
                        st.markdown(f"""
                        **{status} {zone_name}**  
                        Coverage: **{coverage:.0f}%**  
                        {zone_info["vaccinated"]}/{zone_info["target"]} dogs  
                        {zone_info["campaigns"]} campaigns
                        """)

            st.markdown("---")

            # Zone and status filters for map
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                selected_zones_map = st.multiselect(
                    "Filter by zones:",
                    options=unique_zones,
                    default=unique_zones,
                    help="Select zones to display on the map"
                )
            with col2:
                status_options = ["Scheduled", "In Progress", "Completed", "Overdue"]
                selected_statuses = st.multiselect(
                    "Filter by status:",
                    options=status_options,
                    default=status_options,
                    help="Select campaign statuses to display"
                )
            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                view_type = st.radio("View", ["All", "Color by Status"], horizontal=True, label_visibility="collapsed")

            # Filter campaigns by selected zones and statuses
            filtered_campaigns = [c for c in campaigns
                                  if c.get("zone") in selected_zones_map
                                  and c.get("status") in selected_statuses]

            if filtered_campaigns:
                if view_type == "All":
                    # Simple map view - all points same color
                    map_df = pd.DataFrame([
                        {
                            "lat": c.get("location", {}).get("lat", 13.0827),
                            "lon": c.get("location", {}).get("lon", 80.2707),
                        }
                        for c in filtered_campaigns
                    ])

                    if not map_df.empty:
                        st.map(map_df, zoom=11, use_container_width=True)
                        st.caption(f"📍 Showing {len(filtered_campaigns)} campaign location(s)")

                else:
                    # Color-coded view by status
                    st.markdown("#### 📊 Color-Coded Campaign Map")

                    # Separate campaigns by status
                    status_groups = {
                        "Scheduled": {"color": "🟢", "campaigns": []},
                        "In Progress": {"color": "🟡", "campaigns": []},
                        "Completed": {"color": "✅", "campaigns": []},
                        "Overdue": {"color": "🔴", "campaigns": []}
                    }

                    for camp in filtered_campaigns:
                        status = camp.get("status", "Scheduled")
                        if status in status_groups:
                            status_groups[status]["campaigns"].append(camp)

                    # Display separate maps for each status with colored headers
                    for status, data in status_groups.items():
                        if data["campaigns"]:
                            # Status header with color indicator
                            if status == "Scheduled":
                                st.success(f"{data['color']} **{status}** - {len(data['campaigns'])} campaign(s)")
                            elif status == "In Progress":
                                st.warning(f"{data['color']} **{status}** - {len(data['campaigns'])} campaign(s)")
                            elif status == "Completed":
                                st.info(f"{data['color']} **{status}** - {len(data['campaigns'])} campaign(s)")
                            elif status == "Overdue":
                                st.error(f"{data['color']} **{status}** - {len(data['campaigns'])} campaign(s)")

                            # Create map for this status
                            status_df = pd.DataFrame([
                                {
                                    "lat": c.get("location", {}).get("lat", 13.0827),
                                    "lon": c.get("location", {}).get("lon", 80.2707),
                                }
                                for c in data["campaigns"]
                            ])

                            # Show mini map
                            st.map(status_df, zoom=11, use_container_width=True)

                            # List campaigns under this status
                            with st.expander(f"View {len(data['campaigns'])} campaign(s)"):
                                for camp in data["campaigns"]:
                                    st.write(
                                        f"• **{camp.get('id')}** - {camp.get('location_name', 'N/A')} ({camp.get('zone')})")
                                    st.caption(
                                        f"   {camp.get('completed')}/{camp.get('target')} dogs • {camp.get('date')}")

                            st.markdown("---")

                # Show campaign details below map
                st.markdown("#### 📍 All Campaign Locations")

                # Summary count by status
                status_counts = {}
                for camp in filtered_campaigns:
                    status = camp.get("status", "Unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🟢 Scheduled", status_counts.get("Scheduled", 0))
                with col2:
                    st.metric("🟡 In Progress", status_counts.get("In Progress", 0))
                with col3:
                    st.metric("✅ Completed", status_counts.get("Completed", 0))
                with col4:
                    st.metric("🔴 Overdue", status_counts.get("Overdue", 0))

                st.markdown("---")

                # Campaign details list
                for camp in filtered_campaigns:
                    status = camp.get("status", "Unknown")
                    status_emoji = {
                        "Scheduled": "🟢",
                        "In Progress": "🟡",
                        "Completed": "✅",
                        "Overdue": "🔴"
                    }.get(status, "⚪")

                    with st.expander(f"{status_emoji} {camp.get('id')} - {camp.get('location_name', 'N/A')}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Zone:** {camp.get('zone')}")
                            st.write(f"**Date:** {camp.get('date')}")
                            st.write(f"**Time:** {camp.get('time_slot', 'N/A')}")
                        with col2:
                            st.write(f"**Status:** {status}")
                            st.write(f"**Progress:** {camp.get('completed')}/{camp.get('target')}")
                            st.write(f"**Vaccine:** {camp.get('vaccine_type', 'N/A')}")
                        with col3:
                            loc = camp.get('location', {})
                            st.write(f"**Coordinator:** {camp.get('coordinator', 'N/A')}")
                            st.write(f"**Coordinates:**")
                            st.caption(f"Lat: {loc.get('lat', 'N/A'):.4f}")
                            st.caption(f"Lon: {loc.get('lon', 'N/A'):.4f}")

                # Legend explanation
                st.markdown("---")
                st.markdown("**📋 Status Indicators:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("🟢 **Scheduled**")
                    st.caption("Upcoming campaign, not started yet")
                with col2:
                    st.markdown("🟡 **In Progress**")
                    st.caption("Currently active today")
                with col3:
                    st.markdown("✅ **Completed**")
                    st.caption("Successfully finished")
                with col4:
                    st.markdown("🔴 **Overdue**")
                    st.caption("Past due date, needs attention")
            else:
                st.info("No campaigns match the selected filters. Try adjusting zone or status filters.")
        else:
            st.info("No campaigns to display on map. Create your first campaign to see it here!")

    # ==================== TAB 3: CAMPAIGN LIST ====================
    with tabs[2]:
        st.markdown("### 📋 All Campaigns")

        # Search and filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search_query = st.text_input("🔍 Search campaigns", placeholder="Search by ID, zone, coordinator...")

        with col2:
            status_filter = st.multiselect(
                "Filter by Status",
                options=["Scheduled", "In Progress", "Completed", "Overdue"],
                default=["Scheduled", "In Progress", "Overdue"]
            )

        with col3:
            # Get all unique zones from campaigns dynamically
            all_zones = list(set(c.get("zone", "Unknown") for c in campaigns))
            all_zones.sort()
            zone_filter = st.multiselect("Filter by Zone", options=all_zones,
                                         default=all_zones if len(all_zones) <= 5 else all_zones[:5])

        # Filter campaigns
        filtered = campaigns
        if search_query:
            filtered = [c for c in filtered
                        if search_query.lower() in c.get("id", "").lower()
                        or search_query.lower() in c.get("zone", "").lower()
                        or search_query.lower() in c.get("coordinator", "").lower()]

        if status_filter:
            filtered = [c for c in filtered if c.get("status") in status_filter]

        if zone_filter:
            filtered = [c for c in filtered if c.get("zone") in zone_filter]

        # Sort options
        col1, col2 = st.columns([1, 3])
        with col1:
            sort_by = st.selectbox("Sort by", ["Date", "Zone", "Progress", "Status"])

        # Sort campaigns
        if sort_by == "Date":
            filtered.sort(key=lambda x: x.get("date", ""))
        elif sort_by == "Zone":
            filtered.sort(key=lambda x: x.get("zone", ""))
        elif sort_by == "Progress":
            filtered.sort(key=lambda x: (x.get("completed", 0) / x.get("target", 1) if x.get("target", 0) > 0 else 0),
                          reverse=True)
        elif sort_by == "Status":
            status_order = {"In Progress": 0, "Scheduled": 1, "Overdue": 2, "Completed": 3}
            filtered.sort(key=lambda x: status_order.get(x.get("status"), 4))

        st.markdown(f"**Showing {len(filtered)} of {len(campaigns)} campaigns**")

        # Display campaigns
        if filtered:
            for campaign in filtered:
                render_campaign_card(campaign, user_role, user_name)
        else:
            st.info("No campaigns match your filters")

    # ==================== TAB 4: ANALYTICS ====================
    with tabs[3]:
        st.markdown("### 📊 Vaccination Analytics")

        if campaigns:
            # Trend analysis
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📈 Vaccination Trend")

                # Create trend data
                trend_data = {}
                for c in campaigns:
                    date = c.get("date", str(today))[:7]  # YYYY-MM
                    if date not in trend_data:
                        trend_data[date] = {"target": 0, "completed": 0}
                    trend_data[date]["target"] += c.get("target", 0)
                    trend_data[date]["completed"] += c.get("completed", 0)

                if trend_data:
                    trend_df = pd.DataFrame([
                        {"Month": k, "Target": v["target"], "Completed": v["completed"]}
                        for k, v in sorted(trend_data.items())
                    ])
                    st.line_chart(trend_df.set_index("Month"))

            with col2:
                st.markdown("#### 🎯 Zone Performance")

                # Zone performance data
                zone_performance = {}
                for c in campaigns:
                    zone = c.get("zone", "Unknown")
                    if zone not in zone_performance:
                        zone_performance[zone] = {"completed": 0, "target": 0}
                    zone_performance[zone]["completed"] += c.get("completed", 0)
                    zone_performance[zone]["target"] += c.get("target", 0)

                if zone_performance:
                    perf_df = pd.DataFrame([
                        {
                            "Zone": k,
                            "Completion Rate": (v["completed"] / v["target"] * 100) if v["target"] > 0 else 0
                        }
                        for k, v in zone_performance.items()
                    ])
                    st.bar_chart(perf_df.set_index("Zone"))

            st.markdown("---")

            # Status distribution
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📊 Campaign Status Distribution")
                status_counts = {}
                for c in campaigns:
                    status = c.get("status", "Unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1

                if status_counts:
                    status_df = pd.DataFrame([
                        {"Status": k, "Count": v}
                        for k, v in status_counts.items()
                    ])
                    st.bar_chart(status_df.set_index("Status"))

            with col2:
                st.markdown("#### 💉 Vaccine Type Distribution")
                vaccine_types = {}
                for c in campaigns:
                    vtype = c.get("vaccine_type", "Unknown")
                    vaccine_types[vtype] = vaccine_types.get(vtype, 0) + c.get("completed", 0)

                if vaccine_types:
                    vaccine_df = pd.DataFrame([
                        {"Vaccine": k, "Doses": v}
                        for k, v in vaccine_types.items()
                    ])
                    st.bar_chart(vaccine_df.set_index("Vaccine"))

            st.markdown("---")

            # Top performers
            st.markdown("#### 🏆 Top Performing Campaigns")

            performing_campaigns = sorted(
                [c for c in campaigns if c.get("target", 0) > 0],
                key=lambda x: (x.get("completed", 0) / x.get("target", 1)),
                reverse=True
            )[:5]

            if performing_campaigns:
                for idx, c in enumerate(performing_campaigns, 1):
                    completion = (c.get("completed", 0) / c.get("target", 1) * 100)
                    st.success(
                        f"{idx}. **{c.get('id')}** - {c.get('zone')} | {completion:.1f}% complete ({c.get('completed')}/{c.get('target')})")
        else:
            st.info("No data available for analytics")

    # ==================== TAB 5: CREATE CAMPAIGN ====================
    with tabs[4]:
        st.markdown("### ➕ Create New Vaccination Campaign")

        if user_role in ["admin", "vet"]:
            # Get all existing zones from campaigns for suggestions
            existing_zones = list(set([c.get("zone", "") for c in campaigns if c.get("zone")]))
            existing_zones.sort()

            with st.form("create_campaign_form"):
                st.markdown("#### Campaign Details")
                col1, col2 = st.columns(2)

                with col1:
                    # Free-form zone input with suggestions
                    zone_input_method = st.radio("Zone Selection:", ["Enter New Zone", "Select Existing Zone"],
                                                 horizontal=True, key="zone_method")

                    if zone_input_method == "Enter New Zone":
                        zone = st.text_input("Zone Name *",
                                             placeholder="Enter zone/area name (e.g., T.Nagar, Adyar, etc.)")
                    else:
                        if existing_zones:
                            zone = st.selectbox("Select Existing Zone *", existing_zones)
                        else:
                            st.info("No existing zones. Please enter a new zone.")
                            zone = st.text_input("Zone Name *", placeholder="Enter zone/area name")

                    campaign_date = st.date_input("Campaign Date *", min_value=today)
                    time_slot = st.selectbox("Time Slot *",
                                             ["09:00-12:00", "12:00-15:00", "15:00-18:00", "Full Day (09:00-18:00)"])
                    target = st.number_input("Target (Dogs) *", min_value=1, value=50, step=10)

                with col2:
                    vaccine_type = st.selectbox("Vaccine Type *",
                                                ["Rabies", "Distemper", "Parvovirus", "Combination (DHPP)", "Other"])

                    if vaccine_type == "Other":
                        vaccine_type = st.text_input("Specify Vaccine Type *")

                    coordinator = st.text_input("Coordinator Name", value=user_name)
                    volunteers_needed = st.number_input("Volunteers Needed", min_value=1, value=5, step=1)
                    notes = st.text_area("Campaign Notes (Optional)")

                st.markdown("---")
                st.markdown("#### 📍 Location Selection")

                # Store search results in session state
                if "place_search_results" not in st.session_state:
                    st.session_state.place_search_results = []
                if "selected_place" not in st.session_state:
                    st.session_state.selected_place = None

                location_method = st.radio(
                    "Choose location input method:",
                    ["🔍 Search Place", "📍 Manual Coordinates"],
                    horizontal=True
                )

                if location_method == "🔍 Search Place":
                    st.markdown("**Search for a location:**")

                    # Place search input
                    place_query = st.text_input(
                        "Enter place name, landmark, or address",
                        placeholder="e.g., Pondy Bazaar, Anna Nagar Tower, Marina Beach...",
                        key="place_search_input"
                    )

                    # Common Chennai locations database for quick search
                    chennai_places = {
                        # T.Nagar
                        "Pondy Bazaar": {"lat": 13.0448, "lon": 80.2341, "zone": "T.Nagar"},
                        "Panagal Park": {"lat": 13.0389, "lon": 80.2336, "zone": "T.Nagar"},
                        "T.Nagar Bus Stand": {"lat": 13.0418, "lon": 80.2341, "zone": "T.Nagar"},
                        "Mambalam Railway Station": {"lat": 13.0331, "lon": 80.2242, "zone": "T.Nagar"},
                        "Ranganathan Street": {"lat": 13.0442, "lon": 80.2349, "zone": "T.Nagar"},

                        # Anna Nagar
                        "Anna Nagar Tower": {"lat": 13.0850, "lon": 80.2101, "zone": "Anna Nagar"},
                        "Shanti Colony": {"lat": 13.0913, "lon": 80.2092, "zone": "Anna Nagar"},
                        "Anna Nagar Bus Depot": {"lat": 13.0891, "lon": 80.2144, "zone": "Anna Nagar"},
                        "Thirumangalam": {"lat": 13.0867, "lon": 80.2055, "zone": "Anna Nagar"},
                        "Anna Nagar Roundana": {"lat": 13.0879, "lon": 80.2103, "zone": "Anna Nagar"},

                        # Adyar
                        "Adyar Bridge": {"lat": 13.0067, "lon": 80.2578, "zone": "Adyar"},
                        "Kotturpuram": {"lat": 13.0129, "lon": 80.2493, "zone": "Adyar"},
                        "Kasturba Nagar": {"lat": 13.0101, "lon": 80.2581, "zone": "Adyar"},
                        "Besant Nagar Beach": {"lat": 13.0001, "lon": 80.2668, "zone": "Adyar"},
                        "Adyar Cancer Institute": {"lat": 13.0093, "lon": 80.2571, "zone": "Adyar"},

                        # Velachery
                        "Velachery Bus Stand": {"lat": 12.9750, "lon": 80.2200, "zone": "Velachery"},
                        "Phoenix Mall": {"lat": 12.9822, "lon": 80.2207, "zone": "Velachery"},
                        "Vijaya Nagar": {"lat": 12.9718, "lon": 80.2156, "zone": "Velachery"},
                        "Taramani": {"lat": 12.9916, "lon": 80.2443, "zone": "Velachery"},
                        "Velachery Railway Station": {"lat": 12.9753, "lon": 80.2183, "zone": "Velachery"},

                        # Tambaram
                        "Tambaram Railway Station": {"lat": 12.9229, "lon": 80.1275, "zone": "Tambaram"},
                        "Tambaram Sanatorium": {"lat": 12.9375, "lon": 80.1264, "zone": "Tambaram"},
                        "Selaiyur": {"lat": 12.9058, "lon": 80.1456, "zone": "Tambaram"},
                        "Chrompet": {"lat": 12.9516, "lon": 80.1462, "zone": "Tambaram"},
                        "Tambaram East": {"lat": 12.9268, "lon": 80.1341, "zone": "Tambaram"},

                        # Other popular areas
                        "Marina Beach": {"lat": 13.0499, "lon": 80.2824, "zone": "Marina"},
                        "Central Railway Station": {"lat": 13.0827, "lon": 80.2707, "zone": "Central"},
                        "Mylapore": {"lat": 13.0339, "lon": 80.2677, "zone": "Mylapore"},
                        "Nungambakkam": {"lat": 13.0569, "lon": 80.2425, "zone": "Nungambakkam"},
                        "Guindy": {"lat": 13.0067, "lon": 80.2206, "zone": "Guindy"},
                        "Porur": {"lat": 13.0358, "lon": 80.1560, "zone": "Porur"},
                        "Perungudi": {"lat": 12.9610, "lon": 80.2446, "zone": "Perungudi"},
                        "Sholinganallur": {"lat": 12.9010, "lon": 80.2279, "zone": "Sholinganallur"},
                        "OMR": {"lat": 12.9395, "lon": 80.2343, "zone": "OMR"},
                        "ECR": {"lat": 12.8500, "lon": 80.2400, "zone": "ECR"},
                    }

                    # Search function
                    if place_query:
                        # Simple fuzzy search
                        search_results = []
                        query_lower = place_query.lower()

                        for place_name, place_data in chennai_places.items():
                            if query_lower in place_name.lower():
                                search_results.append({
                                    "name": place_name,
                                    "zone": place_data["zone"],
                                    "lat": place_data["lat"],
                                    "lon": place_data["lon"]
                                })

                        if search_results:
                            st.success(f"✅ Found {len(search_results)} matching location(s)")

                            # Display search results
                            st.markdown("**Select a location:**")
                            for idx, result in enumerate(search_results):
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    st.markdown(f"**{result['name']}**")
                                    st.caption(
                                        f"📍 {result['zone']} • Lat: {result['lat']:.4f}, Lon: {result['lon']:.4f}")
                                with col_b:
                                    select_key = f"select_{idx}_{result['name']}"
                                    if st.checkbox("Select", key=select_key):
                                        st.session_state.selected_place = result

                            # Show selected place
                            if st.session_state.selected_place:
                                selected = st.session_state.selected_place
                                st.success(f"✅ Selected: **{selected['name']}** in {selected['zone']}")

                                latitude = selected['lat']
                                longitude = selected['lon']
                                location_name = selected['name']

                                # If zone wasn't filled, suggest the place's zone
                                if not zone and zone_input_method == "Enter New Zone":
                                    st.info(f"💡 Suggested zone: **{selected['zone']}**")

                                # Show map preview
                                preview_df = pd.DataFrame([{"lat": latitude, "lon": longitude}])
                                st.map(preview_df, zoom=15)
                            else:
                                st.info("👆 Check the box next to a location to select it")
                                # Default values if nothing selected
                                latitude = 13.0827
                                longitude = 80.2707
                                location_name = "Custom Location"
                        else:
                            st.warning(f"No results found for '{place_query}'")
                            st.info("💡 Try searching for: landmarks, area names, or famous places in Chennai")

                            # Show some suggestions
                            st.markdown("**Popular locations:**")
                            suggestions = ["Pondy Bazaar", "Anna Nagar Tower", "Marina Beach", "Phoenix Mall",
                                           "Tambaram Station"]
                            st.caption(", ".join(suggestions))

                            # Default values
                            latitude = 13.0827
                            longitude = 80.2707
                            location_name = "Custom Location"
                    else:
                        st.info("👆 Type a place name to search (e.g., 'Pondy Bazaar', 'Anna Tower', 'Marina')")

                        # Show browse options
                        st.markdown("**Or browse popular areas:**")

                        # Group by zone
                        zones_list = {}
                        for place_name, place_data in chennai_places.items():
                            zone_name = place_data["zone"]
                            if zone_name not in zones_list:
                                zones_list[zone_name] = []
                            zones_list[zone_name].append(place_name)

                        # Show expandable zone lists
                        for zone_name, places in sorted(zones_list.items()):
                            with st.expander(f"📍 {zone_name} ({len(places)} locations)"):
                                for place in sorted(places):
                                    st.caption(f"• {place}")

                        # Default values
                        latitude = 13.0827
                        longitude = 80.2707
                        location_name = "Custom Location"

                else:  # Manual Coordinates
                    st.markdown("**Enter coordinates manually:**")

                    col1, col2 = st.columns(2)
                    with col1:
                        latitude = st.number_input("Latitude *", value=13.0827, format="%.4f",
                                                   help="Example: 13.0827 for Chennai Central")
                    with col2:
                        longitude = st.number_input("Longitude *", value=80.2707, format="%.4f",
                                                    help="Example: 80.2707 for Chennai Central")

                    location_name = st.text_input("Location Name/Description",
                                                  placeholder="e.g., Near XYZ Hospital, ABC Street corner...")

                    # Preview map
                    preview_df = pd.DataFrame([{"lat": latitude, "lon": longitude}])
                    st.map(preview_df, zoom=14)
                    st.caption(f"📍 Location: Lat {latitude:.4f}, Lon {longitude:.4f}")

                    # Reverse geocode hint (show general area)
                    st.info("💡 Tip: Use Google Maps to find exact coordinates of your location")

                st.markdown("---")
                submit_button = st.form_submit_button("🚀 Create Campaign", type="primary", use_container_width=True)

                if submit_button:
                    # Validation
                    if not zone:
                        st.error("❌ Please enter a zone name")
                    elif not location_name or location_name == "Custom Location":
                        if location_method == "🔍 Search Place":
                            st.error("❌ Please search and select a location")
                        else:
                            location_name = f"Custom Location (Lat {latitude:.4f}, Lon {longitude:.4f})"
                    else:
                        new_campaign = {
                            "id": f"VC-{int(time.time() * 1000)}",
                            "zone": zone.strip(),
                            "date": str(campaign_date),
                            "time_slot": time_slot,
                            "status": "Scheduled",
                            "target": target,
                            "completed": 0,
                            "vaccine_type": vaccine_type,
                            "coordinator": coordinator or user_name,
                            "volunteers_needed": volunteers_needed,
                            "volunteers_assigned": [],
                            "notes": notes,
                            "location": {"lat": latitude, "lon": longitude},
                            "location_name": location_name,
                            "created_by": user_name,
                            "created_at": str(dt.datetime.now())
                        }

                        campaigns.append(new_campaign)
                        storage.write("campaigns", campaigns)

                        # Reset selected place
                        st.session_state.selected_place = None

                        # Store campaign ID for QR generation outside form
                        st.session_state.new_campaign_id = new_campaign['id']
                        st.session_state.new_campaign_data = new_campaign
                        st.session_state.show_campaign_success = True

                        # Create notification
                        create_notification(
                            "campaign_created",
                            f"New vaccination campaign created: {new_campaign['id']} in {zone}",
                            "high"
                        )

                        # Audit log
                        audit_log("CAMPAIGN_CREATE", {
                            "id": new_campaign['id'],
                            "zone": zone,
                            "date": str(campaign_date),
                            "target": target,
                            "location": location_name
                        })

                        st.rerun()

            # Show success message and QR code outside the form
            if st.session_state.get("show_campaign_success", False):
                campaign_data = st.session_state.get("new_campaign_data", {})
                campaign_id = st.session_state.get("new_campaign_id", "")

                st.success(f"✅ Campaign {campaign_id} created successfully!")

                # Generate QR code
                qr_data = f"SafePaws Campaign: {campaign_id}\nZone: {campaign_data.get('zone')}\nLocation: {campaign_data.get('location_name')}\nDate: {campaign_data.get('date')}\nTarget: {campaign_data.get('target')}"
                qr_img = generate_qr_code(qr_data)

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(qr_img, caption=f"QR Code for {campaign_id}", width=200)
                    # Download button outside form
                    st.download_button(
                        "📥 Download QR Code",
                        qr_img,
                        file_name=f"campaign_qr_{campaign_id}.png",
                        mime="image/png",
                        key=f"download_qr_{campaign_id}"
                    )
                with col2:
                    st.info("📱 Share this QR code with volunteers and team members for quick campaign access!")
                    st.markdown(f"""
                    **Campaign Summary:**
                    - 🏘️ Zone: {campaign_data.get('zone', 'N/A')}
                    - 📍 Location: {campaign_data.get('location_name', 'N/A')}
                    - 📅 Date: {campaign_data.get('date', 'N/A')}
                    - ⏰ Time: {campaign_data.get('time_slot', 'N/A')}
                    - 🎯 Target: {campaign_data.get('target', 0)} dogs
                    - 💉 Vaccine: {campaign_data.get('vaccine_type', 'N/A')}
                    - 👤 Coordinator: {campaign_data.get('coordinator', 'N/A')}
                    """)

                if st.button("➕ Create Another Campaign", type="primary"):
                    st.session_state.show_campaign_success = False
                    st.session_state.new_campaign_id = None
                    st.session_state.new_campaign_data = None
                    st.session_state.selected_place = None
                    st.rerun()
        else:
            st.warning("⚠️ Only admins and vets can create new campaigns")

    # ==================== TAB 6: AVAILABLE CAMPAIGNS (For Volunteers/Vets) ====================
    with tabs[5]:
        st.markdown("### 👥 Available Campaigns - Join a Campaign")

        if user_role in ["volunteer", "vet"]:
            st.info("💡 Browse campaigns below and click 'Join Campaign' to volunteer!")

            # Filter options for volunteers
            col1, col2, col3 = st.columns(3)

            with col1:
                volunteer_zone_filter = st.multiselect(
                    "Filter by Zone",
                    options=list(set(c.get("zone", "Unknown") for c in campaigns)),
                    default=[]
                )

            with col2:
                volunteer_date_filter = st.selectbox(
                    "Filter by Date",
                    ["All Dates", "Upcoming Week", "This Month", "Custom Date"]
                )

            with col3:
                show_joined = st.checkbox("Show Only My Campaigns", value=False)

            # Filter campaigns based on selections
            available_campaigns = campaigns.copy()

            # Zone filter
            if volunteer_zone_filter:
                available_campaigns = [c for c in available_campaigns if c.get("zone") in volunteer_zone_filter]

            # Date filter
            if volunteer_date_filter == "Upcoming Week":
                week_later = today + dt.timedelta(days=7)
                available_campaigns = [c for c in available_campaigns
                                       if today <= dt.date.fromisoformat(c.get("date", str(today))) <= week_later]
            elif volunteer_date_filter == "This Month":
                available_campaigns = [c for c in available_campaigns
                                       if dt.date.fromisoformat(c.get("date", str(today))).month == today.month]

            # Show only campaigns user has joined
            if show_joined:
                available_campaigns = [c for c in available_campaigns
                                       if user_name in c.get("volunteers_assigned", [])]
            else:
                # Show campaigns that still need volunteers
                available_campaigns = [c for c in available_campaigns
                                       if c.get("status") in ["Scheduled", "In Progress"]]

            # Sort by date
            available_campaigns.sort(key=lambda x: x.get("date", ""))

            if available_campaigns:
                st.markdown(f"**Found {len(available_campaigns)} campaign(s)**")
                st.markdown("---")

                for campaign in available_campaigns:
                    volunteers_assigned = campaign.get("volunteers_assigned", [])
                    volunteers_needed = campaign.get("volunteers_needed", 0)
                    is_joined = user_name in volunteers_assigned
                    spots_left = max(0, volunteers_needed - len(volunteers_assigned))

                    # Campaign card for volunteers
                    status = campaign.get("status", "Scheduled")
                    status_colors = {
                        "Scheduled": "#10b981",
                        "In Progress": "#f59e0b",
                        "Completed": "#6366f1",
                        "Overdue": "#ef4444"
                    }
                    color = status_colors.get(status, "#64748b")

                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.markdown(f"### 💉 {campaign.get('id', 'N/A')}")
                            st.caption(f"📍 {campaign.get('zone', 'Unknown')} - {campaign.get('location_name', 'N/A')}")
                            st.caption(f"📅 {campaign.get('date', 'N/A')} | ⏰ {campaign.get('time_slot', 'N/A')}")

                        with col2:
                            st.markdown(f"**Status**")
                            st.markdown(
                                f"<span style='background: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 700;'>{status}</span>",
                                unsafe_allow_html=True)

                        with col3:
                            if is_joined:
                                st.success("✅ You're Joined!")
                            elif spots_left > 0:
                                st.warning(f"🎯 {spots_left} spots left")
                            else:
                                st.error("❌ Full")

                        # Details
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.markdown(f"**💉 Vaccine:** {campaign.get('vaccine_type', 'N/A')}")
                        with col2:
                            st.markdown(f"**🎯 Target:** {campaign.get('target', 0)} dogs")
                        with col3:
                            st.markdown(f"**👤 Coordinator:** {campaign.get('coordinator', 'N/A')}")
                        with col4:
                            st.markdown(f"**👥 Volunteers:** {len(volunteers_assigned)}/{volunteers_needed}")

                        # Notes
                        if campaign.get('notes'):
                            with st.expander("📝 Campaign Notes"):
                                st.write(campaign.get('notes'))

                        # Action buttons
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if is_joined:
                                if st.button("❌ Leave Campaign", key=f"leave_{campaign.get('id')}",
                                             use_container_width=True, type="secondary"):
                                    # Remove volunteer from campaign
                                    campaigns_data = storage.read("campaigns", [])
                                    for c in campaigns_data:
                                        if c.get("id") == campaign.get("id"):
                                            if user_name in c.get("volunteers_assigned", []):
                                                c["volunteers_assigned"].remove(user_name)
                                            break

                                    storage.write("campaigns", campaigns_data)

                                    # Notification
                                    create_notification(
                                        "volunteer_left",
                                        f"{user_name} left campaign {campaign.get('id')}",
                                        "normal"
                                    )

                                    audit_log("VOLUNTEER_LEFT",
                                              {"campaign": campaign.get('id'), "volunteer": user_name})

                                    st.success("You've left the campaign")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                if spots_left > 0:
                                    if st.button("✅ Join Campaign", key=f"join_{campaign.get('id')}",
                                                 use_container_width=True, type="primary"):
                                        # Add volunteer to campaign
                                        campaigns_data = storage.read("campaigns", [])
                                        for c in campaigns_data:
                                            if c.get("id") == campaign.get("id"):
                                                if "volunteers_assigned" not in c:
                                                    c["volunteers_assigned"] = []
                                                if user_name not in c["volunteers_assigned"]:
                                                    c["volunteers_assigned"].append(user_name)
                                                break

                                        storage.write("campaigns", campaigns_data)

                                        # Notification
                                        create_notification(
                                            "volunteer_joined",
                                            f"{user_name} joined campaign {campaign.get('id')}",
                                            "high"
                                        )

                                        audit_log("VOLUNTEER_JOINED",
                                                  {"campaign": campaign.get('id'), "volunteer": user_name})

                                        st.success("🎉 You've joined the campaign!")
                                        st.balloons()
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.button("❌ Campaign Full", key=f"full_{campaign.get('id')}",
                                              use_container_width=True, disabled=True)

                        with col2:
                            if st.button("🗺️ View Location", key=f"vloc_{campaign.get('id')}",
                                         use_container_width=True):
                                st.session_state[f"show_loc_{campaign.get('id')}"] = True

                        with col3:
                            if st.button("👥 View Volunteers", key=f"vvol_{campaign.get('id')}",
                                         use_container_width=True):
                                st.session_state[f"show_vol_{campaign.get('id')}"] = True

                        # Show location
                        if st.session_state.get(f"show_loc_{campaign.get('id')}", False):
                            loc = campaign.get('location', {})
                            if loc:
                                map_df = pd.DataFrame(
                                    [{"lat": loc.get('lat', 13.0827), "lon": loc.get('lon', 80.2707)}])
                                st.map(map_df, zoom=15)
                                st.caption(f"📍 {campaign.get('location_name', 'N/A')}")

                            if st.button("Close", key=f"close_loc_{campaign.get('id')}"):
                                st.session_state[f"show_loc_{campaign.get('id')}"] = False
                                st.rerun()

                        # Show volunteers
                        if st.session_state.get(f"show_vol_{campaign.get('id')}", False):
                            st.markdown("**Volunteers Assigned:**")
                            if volunteers_assigned:
                                for vol in volunteers_assigned:
                                    st.write(f"✅ {vol}")
                            else:
                                st.info("No volunteers assigned yet")

                            if st.button("Close", key=f"close_vol_{campaign.get('id')}"):
                                st.session_state[f"show_vol_{campaign.get('id')}"] = False
                                st.rerun()

                        st.markdown("---")
            else:
                st.info("No campaigns available matching your filters. Try adjusting the filters or check back later!")

        elif user_role == "admin":
            st.info("ℹ️ As an admin, you can assign volunteers from the Campaign List tab or create new campaigns.")
        else:
            st.warning("⚠️ This tab is for volunteers and vets to join campaigns.")


def render_month_calendar(campaigns, year, month):
    """Render a professional month calendar view"""

    # Get calendar data
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    st.markdown(f"## {month_name} {year}")

    # Days of week header
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for idx, day in enumerate(days):
        with cols[idx]:
            st.markdown(f"**{day}**")

    # Render each week
    for week in cal:
        cols = st.columns(7)
        for idx, day in enumerate(week):
            with cols[idx]:
                if day == 0:
                    st.markdown("")  # Empty cell
                else:
                    # Check if there are campaigns on this day
                    day_date = dt.date(year, month, day)
                    day_campaigns = [c for c in campaigns
                                     if c.get("date", "")[:10] == str(day_date)]

                    # Render day cell
                    if day_campaigns:
                        status_emoji = {
                            "Completed": "✅",
                            "In Progress": "🟡",
                            "Scheduled": "🟢",
                            "Overdue": "🔴"
                        }

                        # Get primary status
                        primary_status = day_campaigns[0].get("status", "Scheduled")
                        emoji = status_emoji.get(primary_status, "📅")

                        st.markdown(f"""
                        <div style="background: rgba(99, 102, 241, 0.1); padding: 8px; 
                                    border-radius: 8px; border: 2px solid #6366f1; min-height: 60px;">
                            <div style="font-weight: 700; font-size: 16px;">{day}</div>
                            <div style="font-size: 20px; margin: 4px 0;">{emoji}</div>
                            <div style="font-size: 11px; color: #94a3b8;">{len(day_campaigns)} campaign(s)</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Show campaign details on click
                        if st.button(f"📋", key=f"day_{year}_{month}_{day}", use_container_width=True):
                            with st.expander(f"Campaigns on {day_date}", expanded=True):
                                for camp in day_campaigns:
                                    st.write(f"**{camp.get('id')}** - {camp.get('zone')}")
                                    st.caption(f"📍 {camp.get('location_name', 'Custom Location')}")
                                    st.caption(
                                        f"Status: {camp.get('status')} | {camp.get('completed')}/{camp.get('target')} dogs | ⏰ {camp.get('time_slot', 'N/A')}")
                                    st.caption(
                                        f"💉 {camp.get('vaccine_type', 'N/A')} | 👤 {camp.get('coordinator', 'N/A')}")
                    else:
                        # Empty day
                        st.markdown(f"""
                        <div style="padding: 8px; min-height: 60px; opacity: 0.5;">
                            <div style="font-weight: 400; font-size: 16px;">{day}</div>
                        </div>
                        """, unsafe_allow_html=True)


def render_week_calendar(campaigns, year, month):
    """Render a week view calendar"""
    st.markdown("### Week View")

    # Get current week
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())

    # Week selector
    week_offset = st.slider("Select Week", min_value=-4, max_value=8, value=0,
                            help="Navigate through weeks")
    week_start = week_start + dt.timedelta(weeks=week_offset)

    # Display week days
    for i in range(7):
        day = week_start + dt.timedelta(days=i)
        day_campaigns = [c for c in campaigns if c.get("date", "")[:10] == str(day)]

        st.markdown(f"### {day.strftime('%A, %B %d, %Y')}")

        if day_campaigns:
            for camp in day_campaigns:
                render_campaign_card(camp, "admin", "Admin")
        else:
            st.info("No campaigns scheduled")

        st.markdown("---")


def render_campaign_card(campaign, user_role, user_name):
    """Render a professional campaign card"""

    status_colors = {
        "Scheduled": "#10b981",
        "In Progress": "#f59e0b",
        "Completed": "#6366f1",
        "Overdue": "#ef4444"
    }

    status = campaign.get("status", "Unknown")
    color = status_colors.get(status, "#64748b")
    progress_pct = (campaign.get("completed", 0) / campaign.get("target", 1) * 100) if campaign.get("target",
                                                                                                    0) > 0 else 0

    with st.container():
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"### 💉 {campaign.get('id', 'N/A')}")
            location_name = campaign.get('location_name', 'Custom Location')
            st.caption(f"📍 {campaign.get('zone', 'Unknown Zone')} - {location_name}")
            st.caption(f"📅 {campaign.get('date', 'N/A')} | ⏰ {campaign.get('time_slot', 'N/A')}")

        with col2:
            st.markdown(f"**Status**")
            st.markdown(
                f"<span style='background: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 700;'>{status}</span>",
                unsafe_allow_html=True)

        with col3:
            st.metric("Progress", f"{progress_pct:.0f}%", f"{campaign.get('completed')}/{campaign.get('target')}")

        # Progress bar
        st.progress(min(1.0, progress_pct / 100))

        # Details
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"**💉 Vaccine:** {campaign.get('vaccine_type', 'N/A')}")
        with col2:
            st.markdown(f"**👤 Coordinator:** {campaign.get('coordinator', 'N/A')}")
        with col3:
            volunteers = len(campaign.get('volunteers_assigned', []))
            needed = campaign.get('volunteers_needed', 0)
            st.markdown(f"**👥 Volunteers:** {volunteers}/{needed}")
        with col4:
            st.markdown(f"**📝 Created by:** {campaign.get('created_by', 'N/A')}")

        # Show location coordinates
        if campaign.get('location'):
            loc = campaign.get('location', {})
            st.caption(f"🗺️ Coordinates: {loc.get('lat', 'N/A'):.4f}, {loc.get('lon', 'N/A'):.4f}")

        # Action buttons
        volunteers_assigned = campaign.get("volunteers_assigned", [])
        volunteers_needed = campaign.get("volunteers_needed", 0)
        is_user_joined = user_name in volunteers_assigned
        spots_left = max(0, volunteers_needed - len(volunteers_assigned))

        # Different buttons based on user role
        if user_role == "admin":
            # Admin gets all control buttons
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("📝 Update Progress", key=f"update_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"updating_{campaign.get('id')}"] = True

            with col2:
                if st.button("👥 Assign Volunteers", key=f"assign_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"assigning_{campaign.get('id')}"] = True

            with col3:
                if st.button("🗺️ View Map", key=f"map_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_map_{campaign.get('id')}"] = True

            with col4:
                if st.button("📱 QR Code", key=f"qr_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_qr_{campaign.get('id')}"] = True

            with col5:
                if st.button("🗑️ Delete", key=f"delete_{campaign.get('id')}", use_container_width=True,
                             type="secondary"):
                    campaigns = storage.read("campaigns", [])
                    campaigns = [c for c in campaigns if c.get("id") != campaign.get("id")]
                    storage.write("campaigns", campaigns)
                    audit_log("CAMPAIGN_DELETE", {"id": campaign.get("id")})
                    st.success("Campaign deleted!")
                    st.rerun()

        elif user_role in ["volunteer", "vet"]:
            # Volunteers/Vets get join/leave and view buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if is_user_joined:
                    if st.button("❌ Leave Campaign", key=f"leave_card_{campaign.get('id')}", use_container_width=True,
                                 type="secondary"):
                        campaigns = storage.read("campaigns", [])
                        for c in campaigns:
                            if c.get("id") == campaign.get("id"):
                                if user_name in c.get("volunteers_assigned", []):
                                    c["volunteers_assigned"].remove(user_name)
                                break
                        storage.write("campaigns", campaigns)
                        create_notification("volunteer_left", f"{user_name} left campaign {campaign.get('id')}",
                                            "normal")
                        audit_log("VOLUNTEER_LEFT", {"campaign": campaign.get('id'), "volunteer": user_name})
                        st.success("You've left the campaign")
                        time.sleep(1)
                        st.rerun()
                else:
                    if spots_left > 0 and campaign.get("status") in ["Scheduled", "In Progress"]:
                        if st.button("✅ Join Campaign", key=f"join_card_{campaign.get('id')}", use_container_width=True,
                                     type="primary"):
                            campaigns = storage.read("campaigns", [])
                            for c in campaigns:
                                if c.get("id") == campaign.get("id"):
                                    if "volunteers_assigned" not in c:
                                        c["volunteers_assigned"] = []
                                    if user_name not in c["volunteers_assigned"]:
                                        c["volunteers_assigned"].append(user_name)
                                    break
                            storage.write("campaigns", campaigns)
                            create_notification("volunteer_joined", f"{user_name} joined campaign {campaign.get('id')}",
                                                "high")
                            audit_log("VOLUNTEER_JOINED", {"campaign": campaign.get('id'), "volunteer": user_name})
                            st.success("🎉 You've joined!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.button("❌ No Spots Available", key=f"nospots_{campaign.get('id')}", use_container_width=True,
                                  disabled=True)

            with col2:
                if st.button("🗺️ View Map", key=f"map_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_map_{campaign.get('id')}"] = True

            with col3:
                if st.button("📱 QR Code", key=f"qr_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_qr_{campaign.get('id')}"] = True

            with col4:
                if st.button("👥 Volunteers", key=f"vollist_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_volunteers_{campaign.get('id')}"] = True

        else:
            # Regular users get view-only buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🗺️ View Map", key=f"map_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_map_{campaign.get('id')}"] = True

            with col2:
                if st.button("📱 QR Code", key=f"qr_{campaign.get('id')}", use_container_width=True):
                    st.session_state[f"viewing_qr_{campaign.get('id')}"] = True

            with col3:
                st.info("Contact admin to join")

        # View Map
        if st.session_state.get(f"viewing_map_{campaign.get('id')}", False):
            loc = campaign.get('location', {})
            if loc:
                map_df = pd.DataFrame([{"lat": loc.get('lat', 13.0827), "lon": loc.get('lon', 80.2707)}])
                st.map(map_df, zoom=15)
                st.caption(f"📍 Campaign Location: {campaign.get('location_name', 'N/A')}")

            if st.button("✖️ Close Map", key=f"close_map_{campaign.get('id')}"):
                st.session_state[f"viewing_map_{campaign.get('id')}"] = False
                st.rerun()

        # View QR Code
        if st.session_state.get(f"viewing_qr_{campaign.get('id')}", False):
            qr_data = f"SafePaws Campaign: {campaign.get('id')}\nZone: {campaign.get('zone')}\nLocation: {campaign.get('location_name', 'N/A')}\nDate: {campaign.get('date')}\nTarget: {campaign.get('target')}"
            qr_img = generate_qr_code(qr_data)

            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(qr_img, width=200)
            with col2:
                st.download_button(
                    "📥 Download QR Code",
                    qr_img,
                    file_name=f"campaign_qr_{campaign.get('id')}.png",
                    mime="image/png",
                    key=f"download_qr_card_{campaign.get('id')}"
                )
                st.info("Scan this QR code to access campaign details quickly!")

            if st.button("✖️ Close", key=f"close_qr_{campaign.get('id')}"):
                st.session_state[f"viewing_qr_{campaign.get('id')}"] = False
                st.rerun()

        # View Volunteers List
        if st.session_state.get(f"viewing_volunteers_{campaign.get('id')}", False):
            st.markdown("**👥 Volunteers Assigned to this Campaign:**")
            volunteers = campaign.get("volunteers_assigned", [])

            if volunteers:
                col1, col2 = st.columns([3, 1])
                with col1:
                    for idx, vol in enumerate(volunteers, 1):
                        st.write(f"{idx}. ✅ **{vol}**")
                with col2:
                    st.metric("Total", len(volunteers))
                    st.metric("Needed", campaign.get("volunteers_needed", 0))

                spots_remaining = max(0, campaign.get("volunteers_needed", 0) - len(volunteers))
                if spots_remaining > 0:
                    st.info(f"🎯 {spots_remaining} more volunteer(s) needed!")
                else:
                    st.success("✅ Campaign is fully staffed!")
            else:
                st.info("No volunteers assigned yet. Be the first to join!")

            if st.button("✖️ Close", key=f"close_volunteers_{campaign.get('id')}"):
                st.session_state[f"viewing_volunteers_{campaign.get('id')}"] = False
                st.rerun()

        # Update Progress Form
        if st.session_state.get(f"updating_{campaign.get('id')}", False):
            with st.form(f"update_form_{campaign.get('id')}"):
                st.markdown("#### Update Campaign Progress")

                new_completed = st.number_input(
                    "Dogs Vaccinated",
                    min_value=campaign.get("completed", 0),
                    max_value=campaign.get("target", 100),
                    value=campaign.get("completed", 0),
                    step=1
                )

                new_status = st.selectbox(
                    "Campaign Status",
                    ["Scheduled", "In Progress", "Completed", "Overdue"],
                    index=["Scheduled", "In Progress", "Completed", "Overdue"].index(
                        campaign.get("status", "Scheduled"))
                )

                notes = st.text_area("Update Notes")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Save Update", type="primary", use_container_width=True):
                        campaigns = storage.read("campaigns", [])
                        for c in campaigns:
                            if c.get("id") == campaign.get("id"):
                                c["completed"] = new_completed
                                c["status"] = new_status
                                c["last_updated"] = str(dt.datetime.now())
                                c["updated_by"] = user_name
                                if notes:
                                    c["notes"] = c.get("notes",
                                                       "") + f"\n[{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}"
                                break

                        storage.write("campaigns", campaigns)
                        create_notification(
                            "campaign_updated",
                            f"Campaign {campaign.get('id')} updated: {new_completed}/{campaign.get('target')} dogs vaccinated",
                            "normal"
                        )
                        audit_log("CAMPAIGN_UPDATE",
                                  {"id": campaign.get('id'), "completed": new_completed, "status": new_status})

                        st.session_state[f"updating_{campaign.get('id')}"] = False
                        st.rerun()

                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state[f"updating_{campaign.get('id')}"] = False
                        st.rerun()

        # Volunteer Assignment Form (Admin Only)
        if st.session_state.get(f"assigning_{campaign.get('id')}", False) and user_role == "admin":
            with st.form(f"assign_form_{campaign.get('id')}"):
                st.markdown("#### Assign Volunteers (Admin Only)")

                # Get available volunteers
                users = storage.read("users", [])
                volunteers = [u for u in users if u.get("role") in ["volunteer", "vet"]]
                volunteer_names = [v.get("name", "Unknown") for v in volunteers]

                if not volunteer_names:
                    st.warning("No volunteers or vets registered in the system yet.")
                    volunteer_names = []

                selected_volunteers = st.multiselect(
                    "Select Volunteers to Assign",
                    options=volunteer_names,
                    default=campaign.get("volunteers_assigned", []),
                    help="These volunteers will be officially assigned to this campaign"
                )

                st.info(
                    "💡 Tip: Volunteers can also self-assign by joining campaigns from the 'Available Campaigns' tab")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Assign Selected", type="primary", use_container_width=True):
                        campaigns = storage.read("campaigns", [])
                        for c in campaigns:
                            if c.get("id") == campaign.get("id"):
                                c["volunteers_assigned"] = selected_volunteers
                                break

                        storage.write("campaigns", campaigns)

                        # Create notification for each assigned volunteer
                        for vol in selected_volunteers:
                            if vol not in campaign.get("volunteers_assigned", []):
                                create_notification(
                                    "volunteer_assigned",
                                    f"You have been assigned to campaign {campaign.get('id')} by admin",
                                    "high"
                                )

                        audit_log("VOLUNTEERS_ASSIGNED",
                                  {"campaign_id": campaign.get('id'), "volunteers": selected_volunteers,
                                   "assigned_by": user_name})
                        st.success(f"✅ {len(selected_volunteers)} volunteer(s) assigned!")
                        st.session_state[f"assigning_{campaign.get('id')}"] = False
                        time.sleep(1)
                        st.rerun()

                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state[f"assigning_{campaign.get('id')}"] = False
                        st.rerun()

        st.markdown("---")