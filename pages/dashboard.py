# pages/dashboard.py

import streamlit as st
import pandas as pd
import altair as alt
import datetime as dt
from utils import storage, auth
from components import kpi_card, page_header, role_badge, has_role


def render():
    """Enhanced dashboard with role-specific views"""
    user_role = st.session_state.user.get("role")
    page_header("📊", "Dashboard", "Real-time platform overview", user_role)

    # Load data
    cases = storage.read("cases", [])
    sos = storage.read("sos", [])
    vacc = storage.read("vaccinations", [])
    donations = storage.read("donations", [])
    posts = storage.read("posts", [])
    users = storage.read("users", [])

    # Normalize data
    for c in cases:
        c.setdefault("disease", "Unknown")
        c.setdefault("severity", "Medium")
        c.setdefault("status", "open")

    for s in sos:
        s.setdefault("status", "active")
        s.setdefault("severity", "Medium")

    for v in vacc:
        v.setdefault("status", "pending")

    for d in donations:
        d.setdefault("amount", 0)

    # KPI Row
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        active_cases = sum(1 for c in cases if c.get("status") == "open")
        kpi_card("Active Cases", active_cases, f"{len(cases)} total", "🔬", "primary")

    with col2:
        active_sos = sum(1 for s in sos if s.get("status") == "active")
        kpi_card("Active SOS", active_sos, f"{len(sos)} all-time", "🚨", "danger")

    with col3:
        total_vaccinations = len(vacc)
        pending_vacc = sum(1 for v in vacc if v.get("status") == "pending")
        kpi_card("Vaccinations", total_vaccinations, f"{pending_vacc} pending", "💉", "success")

    with col4:
        total_donations = sum(d.get("amount", 0) for d in donations)
        kpi_card("Total Raised", f"₹{total_donations:,.0f}", f"{len(donations)} donors", "💰", "info")

    # Role-specific sections
    if has_role("admin"):
        st.markdown("### 🛡️ Admin Overview")

        colA, colB, colC = st.columns(3)

        with colA:
            kpi_card("Total Users", len(users), "Platform users", "👥", "primary")

        with colB:
            volunteers = sum(1 for u in users if u.get("role") == "volunteer")
            kpi_card("Volunteers", volunteers, "Active volunteers", "🧰", "info")

        with colC:
            vets = sum(1 for u in users if u.get("role") == "vet")
            kpi_card("Veterinarians", vets, "Medical staff", "🩺", "success")

    # Recent Activity
    st.markdown("### 📋 Recent Activity")

    # Create activity feed
    activities = []

    # Recent cases
    for c in sorted(cases, key=lambda x: x.get("time", ""), reverse=True)[:5]:
        activities.append({
            "type": "🔬 Case",
            "description": f"New case detected: {c.get('disease', 'Unknown')}",
            "time": c.get("time", ""),
            "severity": c.get("severity", "Medium")
        })

    # Recent SOS
    for s in sorted(sos, key=lambda x: x.get("time", ""), reverse=True)[:5]:
        activities.append({
            "type": "🚨 SOS",
            "description": f"Emergency at {s.get('place', 'Unknown location')}",
            "time": s.get("time", ""),
            "severity": s.get("severity", "High")
        })

    # Recent donations
    for d in sorted(donations, key=lambda x: x.get("time", ""), reverse=True)[:5]:
        activities.append({
            "type": "💰 Donation",
            "description": f"₹{d.get('amount', 0)} donated by {d.get('donor', 'Anonymous')}",
            "time": d.get("time", ""),
            "severity": "Low"
        })

    # Sort all activities by time
    activities.sort(key=lambda x: x["time"], reverse=True)

    # Display activities
    for act in activities[:10]:
        severity_color = {
            "Critical": "#ef4444",
            "High": "#f59e0b",
            "Medium": "#3b82f6",
            "Low": "#10b981"
        }.get(act["severity"], "#64748b")

        st.markdown(f"""
        <div style="padding: 16px; background: rgba(51, 65, 85, 0.3); 
                    border-left: 4px solid {severity_color}; border-radius: 8px; 
                    margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size: 16px;">{act['type']}</strong>
                    <p style="margin: 4px 0 0 0; color: #94a3b8;">{act['description']}</p>
                </div>
                <span style="color: #64748b; font-size: 12px;">🕐 {act['time'][:16]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Charts section
    st.markdown("### 📊 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        # Disease distribution
        st.markdown("#### Disease Distribution")
        if cases:
            disease_counts = {}
            for c in cases:
                disease = c.get("disease", "Unknown")
                disease_counts[disease] = disease_counts.get(disease, 0) + 1

            df_disease = pd.DataFrame({
                'Disease': list(disease_counts.keys()),
                'Count': list(disease_counts.values())
            })

            chart = alt.Chart(df_disease).mark_bar().encode(
                x=alt.X('Count:Q', title='Number of Cases'),
                y=alt.Y('Disease:N', sort='-x', title='Disease Type'),
                color=alt.Color('Count:Q', scale=alt.Scale(scheme='viridis'), legend=None),
                tooltip=['Disease', 'Count']
            ).properties(height=300)

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No case data available")

    with col2:
        # Donation trends
        st.markdown("#### Donation Trends")
        if donations:
            # Group donations by date
            donation_by_date = {}
            for d in donations:
                date_str = d.get("time", "")[:10]  # Get YYYY-MM-DD
                if date_str:
                    donation_by_date[date_str] = donation_by_date.get(date_str, 0) + d.get("amount", 0)

            df_donations = pd.DataFrame({
                'Date': list(donation_by_date.keys()),
                'Amount': list(donation_by_date.values())
            })

            df_donations = df_donations.sort_values('Date')

            chart = alt.Chart(df_donations).mark_line(point=True, color="#10b981").encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Amount:Q', title='Amount (₹)'),
                tooltip=['Date', 'Amount']
            ).properties(height=300)

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No donation data available")

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔬 New Case", use_container_width=True, type="primary"):
            st.session_state.nav = "AI Disease Detection"
            st.rerun()

    with col2:
        if st.button("🚨 Report SOS", use_container_width=True, type="secondary"):
            st.session_state.nav = "Emergency SOS"
            st.rerun()

    with col3:
        if st.button("💉 Schedule Vaccination", use_container_width=True, type="secondary"):
            st.session_state.nav = "Vaccination Tracker"
            st.rerun()

    with col4:
        if st.button("💰 Donate Now", use_container_width=True, type="secondary"):
            st.session_state.nav = "Donations"
            st.rerun()