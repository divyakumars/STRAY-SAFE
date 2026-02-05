# pages/feeding_schedule.py - PROFESSIONAL CALENDAR-BASED SCHEDULING SYSTEM

import streamlit as st
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
import time
import json
from utils import storage
from components import page_header, kpi_card, has_role, create_notification, audit_log


@st.cache_resource
def load_plotly():
    """Load Plotly for interactive charts"""
    import plotly.express as px
    import plotly.graph_objects as go
    return {'px': px, 'go': go}


def get_week_dates(start_date=None):
    """Get dates for the current week (Monday to Sunday)"""
    if start_date is None:
        today = datetime.now()
    else:
        today = start_date

    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())

    # Generate all 7 days
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    return week_dates


def get_time_slots():
    """Define standard time slots for feeding"""
    return [
        {"label": "Early Morning", "time": "06:00 - 08:00", "emoji": "🌅", "sort": 1},
        {"label": "Morning", "time": "08:00 - 10:00", "emoji": "☀️", "sort": 2},
        {"label": "Late Morning", "time": "10:00 - 12:00", "emoji": "🌤️", "sort": 3},
        {"label": "Afternoon", "time": "12:00 - 14:00", "emoji": "☀️", "sort": 4},
        {"label": "Late Afternoon", "time": "14:00 - 16:00", "emoji": "🌥️", "sort": 5},
        {"label": "Evening", "time": "16:00 - 18:00", "emoji": "🌆", "sort": 6},
        {"label": "Night", "time": "18:00 - 20:00", "emoji": "🌙", "sort": 7},
        {"label": "Late Night", "time": "20:00 - 22:00", "emoji": "🌃", "sort": 8},
    ]


def get_status_color(booked, total_slots):
    """Get color based on booking status"""
    if booked == 0:
        return "#10b981"  # Green - Available
    elif booked < total_slots:
        return "#f59e0b"  # Orange - Partial
    else:
        return "#ef4444"  # Red - Full


def get_status_badge(booked, total_slots):
    """Get status badge HTML"""
    if booked == 0:
        status = "Available"
        color = "#10b981"
        icon = "🟢"
    elif booked < total_slots:
        status = "Partial"
        color = "#f59e0b"
        icon = "🟡"
    else:
        status = "Full"
        color = "#ef4444"
        icon = "🔴"

    return f"""
    <span style='
        background: {color}15;
        color: {color};
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    '>
        {icon} {status}
    </span>
    """


def render_calendar_header(week_dates, current_week_offset):
    """Render the calendar navigation header"""
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("⬅️ Previous Week", use_container_width=True):
            st.session_state.week_offset = current_week_offset - 1
            st.rerun()

    with col2:
        start_date = week_dates[0].strftime("%B %d")
        end_date = week_dates[-1].strftime("%B %d, %Y")
        st.markdown(f"""
        <div style='text-align: center; padding: 10px;'>
            <h3 style='margin: 0; color: #1f2937;'>📅 {start_date} - {end_date}</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📍 Today", use_container_width=True):
            st.session_state.week_offset = 0
            st.rerun()

    with col3:
        if st.button("Next Week ➡️", use_container_width=True):
            st.session_state.week_offset = current_week_offset + 1
            st.rerun()


def render_calendar_grid(week_dates, data, locations):
    """Render the interactive calendar grid"""
    time_slots = get_time_slots()

    st.markdown("""
    <style>
    .calendar-grid {
        display: grid;
        grid-template-columns: 150px repeat(7, 1fr);
        gap: 1px;
        background: #e5e7eb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
        margin: 20px 0;
    }
    .calendar-cell {
        background: white;
        padding: 12px;
        min-height: 80px;
        position: relative;
    }
    .calendar-header {
        background: #1e40af;
        color: white;
        padding: 16px;
        font-weight: 600;
        text-align: center;
    }
    .time-label {
        background: #f3f4f6;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        color: #374151;
        font-size: 0.9em;
    }
    .slot-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 6px;
        cursor: pointer;
        transition: transform 0.2s;
        font-size: 0.85em;
    }
    .slot-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .slot-available {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    .slot-partial {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    .slot-full {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        opacity: 0.6;
    }
    </style>
    """, unsafe_allow_html=True)

    # Day headers
    cols = st.columns([2] + [1] * 7)
    with cols[0]:
        st.markdown("### Time / Day")

    for idx, date in enumerate(week_dates):
        with cols[idx + 1]:
            day_name = date.strftime("%A")
            date_str = date.strftime("%d")
            is_today = date.date() == datetime.now().date()

            st.markdown(f"""
            <div style='
                text-align: center;
                padding: 12px;
                background: {"#3b82f6" if is_today else "#1e40af"};
                color: white;
                border-radius: 8px;
                margin-bottom: 10px;
            '>
                <div style='font-size: 0.9em; opacity: 0.9;'>{day_name[:3]}</div>
                <div style='font-size: 1.5em; font-weight: bold;'>{date_str}</div>
            </div>
            """, unsafe_allow_html=True)

    # Time slots and data
    for time_slot in time_slots:
        cols = st.columns([2] + [1] * 7)

        # Time label
        with cols[0]:
            st.markdown(f"""
            <div style='
                background: #f3f4f6;
                padding: 16px;
                border-radius: 6px;
                text-align: center;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
            '>
                <div style='font-size: 1.2em; margin-bottom: 4px;'>{time_slot['emoji']}</div>
                <div style='font-weight: 600; color: #374151;'>{time_slot['label']}</div>
                <div style='font-size: 0.85em; color: #6b7280;'>{time_slot['time']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Each day column
        for idx, date in enumerate(week_dates):
            with cols[idx + 1]:
                date_str = date.strftime("%Y-%m-%d")

                # Find slots for this date and time
                matching_slots = [
                    slot for slot in data
                    if slot.get('date') == date_str and slot.get('time_label') == time_slot['label']
                ]

                if matching_slots:
                    for slot in matching_slots[:3]:  # Show max 3 locations per cell
                        booked = slot.get('booked', 0)
                        total = slot.get('slots', 1)
                        location = slot.get('location', 'Unknown')

                        if booked == 0:
                            status_class = "slot-available"
                        elif booked < total:
                            status_class = "slot-partial"
                        else:
                            status_class = "slot-full"

                        # Create unique key for button
                        slot_key = f"view_{date_str}_{time_slot['label']}_{location}"

                        if st.button(
                                f"📍 {location}\n{booked}/{total} booked",
                                key=slot_key,
                                use_container_width=True
                        ):
                            st.session_state.selected_slot = slot
                            st.session_state.show_slot_modal = True
                            st.rerun()

                    if len(matching_slots) > 3:
                        st.caption(f"+ {len(matching_slots) - 3} more...")
                else:
                    # Empty slot - allow adding if admin
                    if has_role("admin"):
                        add_key = f"add_{date_str}_{time_slot['label']}"
                        if st.button("➕ Add", key=add_key, use_container_width=True):
                            st.session_state.new_slot_date = date_str
                            st.session_state.new_slot_time = time_slot['label']
                            st.session_state.show_add_modal = True
                            st.rerun()
                    else:
                        st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)


def render_slot_detail_modal(slot):
    """Render detailed view of a feeding slot"""
    st.markdown("### 📍 Feeding Slot Details")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
        '>
            <h2 style='margin: 0 0 8px 0;'>📍 {slot.get('location', 'Unknown Location')}</h2>
            <p style='margin: 0; font-size: 1.1em; opacity: 0.9;'>
                📅 {slot.get('date', 'N/A')} • ⏰ {slot.get('time', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Booking status
        booked = slot.get('booked', 0)
        total = slot.get('slots', 1)
        available = total - booked
        progress = (booked / total) * 100 if total > 0 else 0

        st.markdown("#### 📊 Booking Status")
        st.progress(progress / 100)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Slots", total)
        with col_b:
            st.metric("Booked", booked)
        with col_c:
            st.metric("Available", available, delta=available)

        # Notes
        if slot.get('notes'):
            st.markdown("#### 📝 Notes")
            st.info(slot['notes'])

        # Food requirements
        if slot.get('food_requirements'):
            st.markdown("#### 🍖 Food Requirements")
            st.write(slot['food_requirements'])

    with col2:
        # Action buttons
        user_email = st.session_state.user.get("email")
        bookings = slot.get("bookings", [])
        already_booked = user_email in bookings

        if already_booked:
            st.success("✅ You're registered for this slot!")
            if st.button("❌ Cancel My Booking", type="secondary", use_container_width=True):
                bookings.remove(user_email)
                slot["booked"] -= 1
                data = storage.read("feeding", [])
                # Update the slot in storage
                for s in data:
                    if (s.get('date') == slot.get('date') and
                            s.get('time_label') == slot.get('time_label') and
                            s.get('location') == slot.get('location')):
                        s['bookings'] = bookings
                        s['booked'] = slot['booked']
                        break
                storage.write("feeding", data)
                create_notification("info", f"Cancelled booking: {slot['location']}", "normal")
                st.session_state.show_slot_modal = False
                st.rerun()
        elif booked < total:
            if st.button("✅ Book This Slot", type="primary", use_container_width=True):
                bookings.append(user_email)
                slot["booked"] += 1
                data = storage.read("feeding", [])
                # Update the slot in storage
                for s in data:
                    if (s.get('date') == slot.get('date') and
                            s.get('time_label') == slot.get('time_label') and
                            s.get('location') == slot.get('location')):
                        s['bookings'] = bookings
                        s['booked'] = slot['booked']
                        break
                storage.write("feeding", data)
                create_notification("success", f"Booked slot: {slot['location']}", "normal")
                st.session_state.show_slot_modal = False
                st.rerun()
        else:
            st.error("🔴 This slot is fully booked")

        # Volunteer list
        st.markdown("#### 👥 Registered Volunteers")
        if bookings:
            for i, volunteer_email in enumerate(bookings, 1):
                # Get volunteer name from user data if possible
                volunteer_name = volunteer_email.split('@')[0].title()
                st.markdown(f"**{i}.** {volunteer_name}")
        else:
            st.info("No volunteers registered yet")

        # Admin actions
        if has_role("admin"):
            st.markdown("---")
            st.markdown("#### ⚙️ Admin Actions")

            if st.button("🗑️ Delete Slot", type="secondary", use_container_width=True):
                data = storage.read("feeding", [])
                data = [s for s in data if not (
                        s.get('date') == slot.get('date') and
                        s.get('time_label') == slot.get('time_label') and
                        s.get('location') == slot.get('location')
                )]
                storage.write("feeding", data)
                create_notification("warning", f"Deleted slot: {slot['location']}", "high")
                st.session_state.show_slot_modal = False
                st.rerun()

    if st.button("← Back to Calendar", use_container_width=True):
        st.session_state.show_slot_modal = False
        st.rerun()


def render_add_slot_modal(date_str, time_label):
    """Render form to add a new feeding slot"""
    st.markdown("### ➕ Add New Feeding Slot")

    time_slots = get_time_slots()
    selected_time = next((t for t in time_slots if t['label'] == time_label), time_slots[0])

    st.info(f"📅 Date: **{date_str}** | ⏰ Time: **{selected_time['label']}** ({selected_time['time']})")

    with st.form("add_slot_form"):
        location = st.text_input("📍 Location", placeholder="e.g., T.Nagar Market, Anna Nagar Park")

        col1, col2 = st.columns(2)
        with col1:
            total_slots = st.number_input("Total Volunteer Slots", min_value=1, max_value=20, value=3)
        with col2:
            food_qty = st.number_input("Food Quantity (kg)", min_value=1, max_value=100, value=10)

        notes = st.text_area("📝 Notes", placeholder="Special instructions or requirements...")

        food_requirements = st.text_area(
            "🍖 Food Requirements",
            placeholder="e.g., Dry food, Wet food, Rice mix..."
        )

        col_a, col_b = st.columns(2)
        with col_a:
            submit = st.form_submit_button("➕ Create Slot", type="primary", use_container_width=True)
        with col_b:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit and location:
            new_slot = {
                "location": location,
                "date": date_str,
                "time_label": time_label,
                "time": selected_time['time'],
                "emoji": selected_time['emoji'],
                "slots": int(total_slots),
                "booked": 0,
                "bookings": [],
                "notes": notes,
                "food_qty": food_qty,
                "food_requirements": food_requirements,
                "created_by": st.session_state.user.get("name"),
                "created_at": str(datetime.now())
            }

            data = storage.read("feeding", [])
            data.append(new_slot)
            storage.write("feeding", data)

            create_notification("success", f"New slot created: {location}", "normal")
            audit_log("FEEDING_SLOT_CREATE", {"location": location, "date": date_str, "time": time_label})

            st.session_state.show_add_modal = False
            st.success("✅ Slot created successfully!")
            time.sleep(1)
            st.rerun()

        if cancel:
            st.session_state.show_add_modal = False
            st.rerun()


def render_list_view(data, locations):
    """Render traditional list view of feeding slots"""
    st.markdown("### 📋 List View")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_location = st.selectbox("📍 Location", ["All"] + locations)

    with col2:
        filter_status = st.selectbox("Status", ["All", "Available", "Partial", "Full"])

    with col3:
        filter_date = st.date_input("📅 Date Filter", value=None)

    # Filter data
    filtered_data = data.copy()

    if filter_location != "All":
        filtered_data = [d for d in filtered_data if d.get('location') == filter_location]

    if filter_status == "Available":
        filtered_data = [d for d in filtered_data if d.get('booked', 0) == 0]
    elif filter_status == "Partial":
        filtered_data = [d for d in filtered_data if 0 < d.get('booked', 0) < d.get('slots', 1)]
    elif filter_status == "Full":
        filtered_data = [d for d in filtered_data if d.get('booked', 0) >= d.get('slots', 1)]

    if filter_date:
        date_str = filter_date.strftime("%Y-%m-%d")
        filtered_data = [d for d in filtered_data if d.get('date') == date_str]

    # Sort by date and time
    filtered_data.sort(key=lambda x: (x.get('date', ''), x.get('time_label', '')))

    if filtered_data:
        for slot in filtered_data:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"""
                    <div style='padding: 16px; background: white; border-radius: 8px; border-left: 4px solid {get_status_color(slot.get('booked', 0), slot.get('slots', 1))}; margin-bottom: 12px;'>
                        <h4 style='margin: 0 0 8px 0;'>{slot.get('emoji', '📍')} {slot.get('location', 'Unknown')}</h4>
                        <p style='margin: 0; color: #6b7280; font-size: 0.9em;'>
                            📅 {slot.get('date', 'N/A')} • ⏰ {slot.get('time_label', 'N/A')} ({slot.get('time', 'N/A')})
                        </p>
                        {f"<p style='margin: 8px 0 0 0; color: #374151; font-size: 0.9em;'>📝 {slot.get('notes', '')}</p>" if slot.get('notes') else ''}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    booked = slot.get('booked', 0)
                    total = slot.get('slots', 1)
                    st.markdown(get_status_badge(booked, total), unsafe_allow_html=True)
                    st.caption(f"👥 {booked}/{total} volunteers")

                with col3:
                    user_email = st.session_state.user.get("email")
                    already_booked = user_email in slot.get("bookings", [])

                    if already_booked:
                        if st.button("❌",
                                     key=f"cancel_list_{slot.get('location')}_{slot.get('date')}_{slot.get('time_label')}",
                                     help="Cancel booking"):
                            slot["bookings"].remove(user_email)
                            slot["booked"] -= 1
                            storage.write("feeding", data)
                            st.rerun()
                    elif booked < total:
                        if st.button("✅",
                                     key=f"book_list_{slot.get('location')}_{slot.get('date')}_{slot.get('time_label')}",
                                     help="Book slot"):
                            if "bookings" not in slot:
                                slot["bookings"] = []
                            slot["bookings"].append(user_email)
                            slot["booked"] += 1
                            storage.write("feeding", data)
                            st.rerun()

                    if st.button("👁️",
                                 key=f"view_list_{slot.get('location')}_{slot.get('date')}_{slot.get('time_label')}",
                                 help="View details"):
                        st.session_state.selected_slot = slot
                        st.session_state.show_slot_modal = True
                        st.rerun()
    else:
        st.info("No feeding slots match the selected filters")


def render_timeline_view(data):
    """Render interactive timeline/Gantt chart view"""
    st.markdown("### 📊 Timeline View")

    if not data:
        st.info("No feeding slots to display")
        return

    viz = load_plotly()
    px = viz['px']

    # Prepare data for timeline
    timeline_data = []
    for slot in data:
        if slot.get('date') and slot.get('time'):
            date_str = slot['date']
            time_range = slot['time'].split(' - ')

            if len(time_range) == 2:
                start_time = time_range[0].strip()
                end_time = time_range[1].strip()

                # Create datetime objects
                start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")

                booked = slot.get('booked', 0)
                total = slot.get('slots', 1)

                if booked == 0:
                    status = "Available 🟢"
                elif booked < total:
                    status = "Partial 🟡"
                else:
                    status = "Full 🔴"

                timeline_data.append({
                    "Location": slot.get('location', 'Unknown'),
                    "Start": start_dt,
                    "End": end_dt,
                    "Status": status,
                    "Capacity": f"{booked}/{total}",
                    "Time": slot.get('time_label', 'N/A')
                })

    if timeline_data:
        df = pd.DataFrame(timeline_data)

        fig = px.timeline(
            df,
            x_start="Start",
            x_end="End",
            y="Location",
            color="Status",
            hover_data=["Capacity", "Time"],
            title="Feeding Schedule Timeline",
            color_discrete_map={
                "Available 🟢": "#10b981",
                "Partial 🟡": "#f59e0b",
                "Full 🔴": "#ef4444"
            }
        )

        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            height=max(400, len(df['Location'].unique()) * 40),
            showlegend=True,
            xaxis_title="Time",
            yaxis_title="Location"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid timeline data available")


def render_stats_dashboard(data):
    """Render statistics and analytics dashboard"""
    st.markdown("### 📈 Statistics & Analytics")

    # Overall stats
    col1, col2, col3, col4, col5 = st.columns(5)

    total_slots = sum(slot.get('slots', 0) for slot in data)
    total_booked = sum(slot.get('booked', 0) for slot in data)
    total_available = total_slots - total_booked
    total_locations = len(set(slot.get('location') for slot in data))
    user_email = st.session_state.user.get("email")
    my_bookings = sum(1 for slot in data if user_email in slot.get("bookings", []))

    with col1:
        st.metric("Total Slots", total_slots)
    with col2:
        st.metric("Booked", total_booked, delta=f"{(total_booked / total_slots * 100) if total_slots > 0 else 0:.1f}%")
    with col3:
        st.metric("Available", total_available)
    with col4:
        st.metric("Locations", total_locations)
    with col5:
        st.metric("My Bookings", my_bookings)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        # Bookings by location
        location_stats = {}
        for slot in data:
            loc = slot.get('location', 'Unknown')
            if loc not in location_stats:
                location_stats[loc] = {'booked': 0, 'total': 0}
            location_stats[loc]['booked'] += slot.get('booked', 0)
            location_stats[loc]['total'] += slot.get('slots', 0)

        if location_stats:
            viz = load_plotly()
            px = viz['px']

            chart_data = pd.DataFrame([
                {'Location': loc, 'Booked': stats['booked'], 'Available': stats['total'] - stats['booked']}
                for loc, stats in location_stats.items()
            ])

            fig = px.bar(
                chart_data,
                x='Location',
                y=['Booked', 'Available'],
                title='Bookings by Location',
                barmode='stack',
                color_discrete_map={'Booked': '#3b82f6', 'Available': '#10b981'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Bookings by time slot
        time_stats = {}
        for slot in data:
            time_label = slot.get('time_label', 'Unknown')
            if time_label not in time_stats:
                time_stats[time_label] = 0
            time_stats[time_label] += slot.get('booked', 0)

        if time_stats:
            chart_data = pd.DataFrame(list(time_stats.items()), columns=['Time Slot', 'Bookings'])
            chart_data = chart_data.sort_values('Bookings', ascending=False)

            fig = px.pie(
                chart_data,
                values='Bookings',
                names='Time Slot',
                title='Bookings by Time Slot',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)


def render():
    """Main render function for feeding schedule"""
    if not has_role('volunteer', 'admin'):
        st.error("⛔ Access Denied: Only volunteers and admins can access this page")
        return

    user_role = st.session_state.user.get("role")
    page_header("🍖", "Professional Feeding Schedule",
                "Interactive calendar-based volunteer coordination", user_role)

    # Initialize session state
    if 'week_offset' not in st.session_state:
        st.session_state.week_offset = 0
    if 'show_slot_modal' not in st.session_state:
        st.session_state.show_slot_modal = False
    if 'show_add_modal' not in st.session_state:
        st.session_state.show_add_modal = False

    # Load data
    data = storage.read("feeding", [])

    # Normalize data structure
    for slot in data:
        slot.setdefault("slots", 1)
        slot.setdefault("booked", 0)
        slot.setdefault("bookings", [])

    # Get unique locations
    locations = sorted(list(set(slot.get('location', 'Unknown') for slot in data)))

    # KPI Dashboard
    st.markdown("### 📊 Overview")
    col1, col2, col3, col4 = st.columns(4)

    total_slots_count = len(data)
    available_count = sum(1 for d in data if d['booked'] < d['slots'])
    full_count = sum(1 for d in data if d['booked'] >= d['slots'])
    user_email = st.session_state.user.get("email")
    my_bookings = sum(1 for d in data if user_email in d.get("bookings", []))

    with col1:
        kpi_card("Total Slots", total_slots_count, "All feeding programs", "📅", "primary")
    with col2:
        kpi_card("Available", available_count, "Open for volunteers", "🟢", "success")
    with col3:
        kpi_card("Fully Booked", full_count, "At capacity", "🔴", "danger")
    with col4:
        kpi_card("My Bookings", my_bookings, "Your commitments", "👤", "info")

    st.markdown("---")

    # Main view selector
    view_tab = st.radio(
        "Select View",
        ["📅 Calendar View", "📋 List View", "📊 Timeline View", "📈 Analytics"],
        horizontal=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Show modals if active
    if st.session_state.get('show_slot_modal') and st.session_state.get('selected_slot'):
        render_slot_detail_modal(st.session_state.selected_slot)
        return

    if st.session_state.get('show_add_modal'):
        render_add_slot_modal(
            st.session_state.get('new_slot_date'),
            st.session_state.get('new_slot_time')
        )
        return

    # Render selected view
    if view_tab == "📅 Calendar View":
        # Calculate week dates
        week_offset = st.session_state.week_offset
        base_date = datetime.now() + timedelta(weeks=week_offset)
        week_dates = get_week_dates(base_date)

        # Render calendar header with navigation
        render_calendar_header(week_dates, week_offset)

        st.markdown("---")

        # Render calendar grid
        render_calendar_grid(week_dates, data, locations)

    elif view_tab == "📋 List View":
        render_list_view(data, locations)

    elif view_tab == "📊 Timeline View":
        render_timeline_view(data)

    elif view_tab == "📈 Analytics":
        render_stats_dashboard(data)

    # Quick actions footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if has_role("admin"):
            if st.button("➕ Quick Add Slot", use_container_width=True):
                st.session_state.new_slot_date = datetime.now().strftime("%Y-%m-%d")
                st.session_state.new_slot_time = "Morning"
                st.session_state.show_add_modal = True
                st.rerun()

    with col2:
        # Export calendar
        if data and st.button("📥 Export Schedule", use_container_width=True):
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                file_name=f"feeding_schedule_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()


# Run the render function when imported
if __name__ == "__main__":
    render()