# pages/impact_analytics.py

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage
from components import page_header, kpi_card, has_role


@st.cache_resource
def load_visualization_libs():
    """Load visualization libraries only when needed"""
    import plotly.express as px
    import plotly.graph_objects as go
    import altair as alt
    return {'px': px, 'go': go, 'alt': alt}


@st.cache_resource
def load_pdf_library():
    """Load PDF generation library"""
    try:
        from fpdf import FPDF
        return FPDF
    except:
        return None


def generate_report(report_type, format_type, report_data):
    """Generate comprehensive impact report"""
    if format_type == "PDF":
        FPDF = load_pdf_library()
        if not FPDF:
            return None, "PDF library not available. Install fpdf: pip install fpdf"

        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 15, f"SafePaws AI - {report_type}", ln=True, align='C')

        # Generated date
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"Generated: {report_data['generated_on']}", ln=True, align='C')
        pdf.ln(10)

        # Executive Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Executive Summary", ln=True)
        pdf.set_font("Arial", '', 11)

        summary_text = f"This report provides comprehensive analytics for SafePaws AI platform activities. "
        summary_text += f"The platform has processed {report_data['total_cases']} disease cases, "
        summary_text += f"responded to {report_data['total_sos']} emergency alerts, "
        summary_text += f"completed {report_data['completed_vaccinations']} vaccinations, "
        summary_text += f"and raised Rs.{report_data['total_donations']:,.0f} in donations."

        pdf.multi_cell(0, 6, summary_text)
        pdf.ln(8)

        # Key Metrics Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Key Performance Indicators", ln=True)
        pdf.set_font("Arial", '', 11)

        metrics = [
            ("Disease Cases",
             f"{report_data['total_cases']} total, {report_data['resolved_cases']} resolved ({report_data['case_resolution_rate']:.1f}%)"),
            ("Emergency Alerts",
             f"{report_data['total_sos']} total, {report_data['resolved_sos']} resolved ({report_data['sos_resolution_rate']:.1f}%)"),
            ("Vaccinations",
             f"{report_data['total_vaccinations']} campaigns, {report_data['completed_vaccinations']} completed"),
            ("Donations", f"Rs.{report_data['total_donations']:,.0f} from {report_data['total_donors']} unique donors"),
            ("Adoptions",
             f"{report_data['total_adoptions']} applications, {report_data['approved_adoptions']} approved"),
            ("Community", f"{report_data['total_posts']} posts, {report_data['total_users']} users"),
            ("Volunteers",
             f"{report_data['active_volunteers']} active, {report_data['total_volunteer_tasks']} tasks completed")
        ]

        for metric_name, metric_value in metrics:
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(60, 7, f"{metric_name}:", 0, 0)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 7, metric_value, 0, 1)

        pdf.ln(8)

        # Impact Analysis
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Impact Analysis", ln=True)
        pdf.set_font("Arial", '', 11)

        impact_text = f"Platform Efficiency: The case resolution rate of {report_data['case_resolution_rate']:.1f}% "
        impact_text += f"demonstrates effective treatment protocols. Emergency response achieved "
        impact_text += f"{report_data['sos_resolution_rate']:.1f}% resolution rate. "
        impact_text += f"Vaccination campaigns reached {report_data['completed_vaccinations']} animals. "
        impact_text += f"Community engagement shows {report_data['total_posts']} active discussions."

        pdf.multi_cell(0, 6, impact_text)

        return pdf.output(dest='S').encode('latin1'), None

    else:  # CSV
        df = pd.DataFrame([report_data])
        return df.to_csv(index=False), None


def render():
    """Comprehensive impact analytics dashboard connecting all platform features"""
    user_role = st.session_state.user.get("role")
    page_header("📊", "Impact Analytics",
                "Comprehensive data-driven insights across all platform activities", user_role)

    # Load all data sources
    cases = storage.read("cases", [])
    sos = storage.read("sos", [])
    campaigns = storage.read("campaigns", [])
    vaccinations = storage.read("vaccinations", [])
    donations = storage.read("donations", [])
    users = storage.read("users", [])
    posts = storage.read("posts", [])
    adoptions = storage.read("adoptions", [])
    tasks = storage.read("tasks", [])
    prescriptions = storage.read("prescriptions", [])

    # Normalize data structures
    for c in cases:
        c.setdefault("disease", "Unknown")
        c.setdefault("severity", "Medium")
        c.setdefault("status", "pending")
        c.setdefault("time", str(dt.datetime.now()))
        c.setdefault("location", "Unknown")

    for s in sos:
        s.setdefault("status", "pending")
        s.setdefault("time", str(dt.datetime.now()))
        s.setdefault("location", "Unknown")

    for v in vaccinations:
        v.setdefault("status", "pending")
        v.setdefault("time", str(dt.datetime.now()))

    for d in donations:
        d.setdefault("amount", 0)
        d.setdefault("donor", "Anonymous")
        d.setdefault("time", str(dt.datetime.now()))

    for a in adoptions:
        a.setdefault("status", "pending")
        a.setdefault("time", str(dt.datetime.now()))

    for t in tasks:
        t.setdefault("status", "pending")
        t.setdefault("time", str(dt.datetime.now()))

    # Calculate comprehensive metrics
    total_cases = len(cases)
    resolved_cases = sum(1 for c in cases if c.get("status") == "resolved")
    active_cases = sum(1 for c in cases if c.get("status") in ["pending", "in_treatment"])

    total_sos = len(sos)
    resolved_sos = sum(1 for s in sos if s.get("status") == "resolved")
    active_sos = sum(1 for s in sos if s.get("status") != "resolved")

    total_campaigns = len(campaigns)
    completed_vaccinations = sum(c.get("completed", 0) for c in campaigns)
    total_vaccination_target = sum(c.get("target", 0) for c in campaigns)

    total_donations = sum(d.get("amount", 0) for d in donations)
    total_donors = len(set(d.get("donor") for d in donations if d.get("donor") != "Anonymous"))

    total_adoptions = len(adoptions)
    approved_adoptions = sum(1 for a in adoptions if a.get("status") == "approved")

    total_posts = len(posts)
    total_users = len(users)
    active_volunteers = sum(1 for u in users if u.get("role") in ["volunteer", "admin"])

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")

    total_prescriptions = len(prescriptions)

    # Calculate rates
    case_resolution_rate = (resolved_cases / total_cases * 100) if total_cases > 0 else 0
    sos_resolution_rate = (resolved_sos / total_sos * 100) if total_sos > 0 else 0
    vaccination_completion_rate = (
                completed_vaccinations / total_vaccination_target * 100) if total_vaccination_target > 0 else 0
    adoption_approval_rate = (approved_adoptions / total_adoptions * 100) if total_adoptions > 0 else 0
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Overall Impact Summary
    st.markdown("### 🎯 Overall Platform Impact")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card("Disease Cases", total_cases,
                 f"{resolved_cases} resolved ({case_resolution_rate:.1f}%)",
                 "🔬", "primary")

    with col2:
        kpi_card("Emergency Alerts", total_sos,
                 f"{resolved_sos} resolved ({sos_resolution_rate:.1f}%)",
                 "🚨", "danger")

    with col3:
        kpi_card("Vaccinations", completed_vaccinations,
                 f"{vaccination_completion_rate:.1f}% of target",
                 "💉", "success")

    with col4:
        kpi_card("Funds Raised", f"₹{total_donations:,.0f}",
                 f"{total_donors} unique donors",
                 "💰", "info")

    # Second row of KPIs
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        kpi_card("Adoptions", total_adoptions,
                 f"{approved_adoptions} approved ({adoption_approval_rate:.1f}%)",
                 "🏠", "success")

    with col6:
        kpi_card("Community Posts", total_posts,
                 f"{total_users} total users",
                 "💬", "info")

    with col7:
        kpi_card("Volunteers", active_volunteers,
                 f"{completed_tasks}/{total_tasks} tasks done",
                 "🤝", "warning")

    with col8:
        kpi_card("Prescriptions", total_prescriptions,
                 f"Issued by vets",
                 "💊", "primary")

    st.markdown("---")

    # Tabs for detailed analytics
    tabs = st.tabs([
        "📈 Trends & Patterns",
        "🗺️ Geographic Distribution",
        "⚡ Performance Metrics",
        "💰 Financial Analytics",
        "👥 User Engagement",
        "📄 Reports"
    ])

    # Load visualization libraries
    viz_libs = load_visualization_libs()
    px = viz_libs['px']
    go = viz_libs['go']

    # TAB 1: Trends & Patterns
    with tabs[0]:
        st.markdown("### 📈 Activity Trends Over Time")

        col1, col2 = st.columns(2)

        with col1:
            # Cases over time
            if cases:
                case_dates = {}
                for c in cases:
                    date = c.get("time", "")[:10]
                    case_dates[date] = case_dates.get(date, 0) + 1

                df_cases = pd.DataFrame({
                    'Date': list(case_dates.keys()),
                    'Cases': list(case_dates.values())
                })
                df_cases = df_cases.sort_values('Date')

                fig = px.line(df_cases, x='Date', y='Cases',
                              title="Disease Cases Over Time",
                              markers=True,
                              template="plotly_dark")
                fig.update_traces(line_color='#6366f1', line_width=3)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No case data available for trend analysis")

        with col2:
            # SOS alerts over time
            if sos:
                sos_dates = {}
                for s in sos:
                    date = s.get("time", "")[:10]
                    sos_dates[date] = sos_dates.get(date, 0) + 1

                df_sos = pd.DataFrame({
                    'Date': list(sos_dates.keys()),
                    'Alerts': list(sos_dates.values())
                })
                df_sos = df_sos.sort_values('Date')

                fig = px.line(df_sos, x='Date', y='Alerts',
                              title="Emergency Alerts Over Time",
                              markers=True,
                              template="plotly_dark")
                fig.update_traces(line_color='#ef4444', line_width=3)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No SOS data available for trend analysis")

        # Disease distribution
        st.markdown("### 🦠 Disease Distribution")

        col1, col2 = st.columns(2)

        with col1:
            if cases:
                disease_counts = {}
                for c in cases:
                    disease = c.get("disease", "Unknown")
                    disease_counts[disease] = disease_counts.get(disease, 0) + 1

                df_diseases = pd.DataFrame({
                    'Disease': list(disease_counts.keys()),
                    'Count': list(disease_counts.values())
                })
                df_diseases = df_diseases.sort_values('Count', ascending=False)

                fig = px.bar(df_diseases, x='Disease', y='Count',
                             title="Cases by Disease Type",
                             template="plotly_dark",
                             color='Count',
                             color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No disease distribution data available")

        with col2:
            # Severity distribution
            if cases:
                severity_counts = {}
                for c in cases:
                    severity = c.get("severity", "Medium")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                fig = go.Figure(data=[go.Pie(
                    labels=list(severity_counts.keys()),
                    values=list(severity_counts.values()),
                    hole=.4,
                    marker_colors=['#ef4444', '#f59e0b', '#10b981']
                )])
                fig.update_layout(
                    title="Case Severity Distribution",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No severity data available")

        # Donation trends
        st.markdown("### 💰 Donation Trends")

        if donations:
            donation_dates = {}
            for d in donations:
                date = d.get("time", "")[:10]
                amount = d.get("amount", 0)
                donation_dates[date] = donation_dates.get(date, 0) + amount

            df_donations = pd.DataFrame({
                'Date': list(donation_dates.keys()),
                'Amount': list(donation_dates.values())
            })
            df_donations = df_donations.sort_values('Date')

            fig = px.area(df_donations, x='Date', y='Amount',
                          title="Cumulative Donations Over Time",
                          template="plotly_dark")
            fig.update_traces(line_color='#10b981', fillcolor='rgba(16, 185, 129, 0.3)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No donation data available")

    # TAB 2: Geographic Distribution
    with tabs[1]:
        st.markdown("### 🗺️ Geographic Hotspots")

        col1, col2 = st.columns(2)

        with col1:
            # Case locations
            if cases:
                case_locations = {}
                for c in cases:
                    location = c.get("location", "Unknown")
                    if location != "Unknown":
                        case_locations[location] = case_locations.get(location, 0) + 1

                if case_locations:
                    df_locations = pd.DataFrame({
                        'Location': list(case_locations.keys()),
                        'Cases': list(case_locations.values())
                    })
                    df_locations = df_locations.sort_values('Cases', ascending=False).head(10)

                    fig = px.bar(df_locations, x='Cases', y='Location',
                                 orientation='h',
                                 title="Top 10 Disease Hotspots",
                                 template="plotly_dark",
                                 color='Cases',
                                 color_continuous_scale='Reds')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No location data available for cases")
            else:
                st.info("No case location data available")

        with col2:
            # SOS locations
            if sos:
                sos_locations = {}
                for s in sos:
                    location = s.get("location", "Unknown")
                    if location != "Unknown":
                        sos_locations[location] = sos_locations.get(location, 0) + 1

                if sos_locations:
                    df_sos = pd.DataFrame({
                        'Location': list(sos_locations.keys()),
                        'Alerts': list(sos_locations.values())
                    })
                    df_sos = df_sos.sort_values('Alerts', ascending=False).head(10)

                    fig = px.bar(df_sos, x='Alerts', y='Location',
                                 orientation='h',
                                 title="Top 10 Emergency Hotspots",
                                 template="plotly_dark",
                                 color='Alerts',
                                 color_continuous_scale='Oranges')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No location data available for SOS alerts")
            else:
                st.info("No SOS location data available")

        # Campaign coverage
        st.markdown("### 💉 Vaccination Campaign Coverage")

        if campaigns:
            campaign_zones = {}
            for c in campaigns:
                zone = c.get("zone", "Unknown")
                completed = c.get("completed", 0)
                campaign_zones[zone] = campaign_zones.get(zone, 0) + completed

            df_campaigns = pd.DataFrame({
                'Zone': list(campaign_zones.keys()),
                'Vaccinations': list(campaign_zones.values())
            })
            df_campaigns = df_campaigns.sort_values('Vaccinations', ascending=False)

            fig = px.bar(df_campaigns, x='Zone', y='Vaccinations',
                         title="Vaccinations by Zone",
                         template="plotly_dark",
                         color='Vaccinations',
                         color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No vaccination campaign data available")

    # TAB 3: Performance Metrics
    with tabs[2]:
        st.markdown("### ⚡ System Performance Indicators")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🎯 Resolution Rates")

            st.metric("Case Resolution", f"{case_resolution_rate:.1f}%",
                      f"{resolved_cases}/{total_cases} cases")

            st.metric("SOS Response", f"{sos_resolution_rate:.1f}%",
                      f"{resolved_sos}/{total_sos} alerts")

            st.metric("Vaccination Completion", f"{vaccination_completion_rate:.1f}%",
                      f"{completed_vaccinations}/{total_vaccination_target}")

        with col2:
            st.markdown("#### 📊 Approval & Completion")

            st.metric("Adoption Approval", f"{adoption_approval_rate:.1f}%",
                      f"{approved_adoptions}/{total_adoptions} applications")

            st.metric("Task Completion", f"{task_completion_rate:.1f}%",
                      f"{completed_tasks}/{total_tasks} tasks")

            avg_donation = total_donations / len(donations) if donations else 0
            st.metric("Avg Donation", f"₹{avg_donation:,.0f}",
                      f"{len(donations)} donations")

        with col3:
            st.markdown("#### 👥 User Engagement")

            active_users = sum(1 for u in users if u.get("last_login", ""))
            st.metric("Active Users", f"{active_users}/{total_users}",
                      f"{(active_users / total_users * 100) if total_users > 0 else 0:.1f}% active")

            posts_per_user = total_posts / total_users if total_users > 0 else 0
            st.metric("Posts per User", f"{posts_per_user:.1f}",
                      f"{total_posts} total posts")

            st.metric("Volunteer Force", active_volunteers,
                      f"{(active_volunteers / total_users * 100) if total_users > 0 else 0:.1f}% of users")

        # Performance timeline
        st.markdown("### 📈 Performance Timeline")

        if cases and sos:
            # Combine resolution metrics over time
            resolution_timeline = {}

            for c in cases:
                if c.get("status") == "resolved":
                    date = c.get("time", "")[:10]
                    if date not in resolution_timeline:
                        resolution_timeline[date] = {"cases": 0, "sos": 0}
                    resolution_timeline[date]["cases"] += 1

            for s in sos:
                if s.get("status") == "resolved":
                    date = s.get("time", "")[:10]
                    if date not in resolution_timeline:
                        resolution_timeline[date] = {"cases": 0, "sos": 0}
                    resolution_timeline[date]["sos"] += 1

            if resolution_timeline:
                df_timeline = pd.DataFrame([
                    {
                        'Date': date,
                        'Cases Resolved': data['cases'],
                        'SOS Resolved': data['sos']
                    }
                    for date, data in resolution_timeline.items()
                ])
                df_timeline = df_timeline.sort_values('Date')

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_timeline['Date'], y=df_timeline['Cases Resolved'],
                    mode='lines+markers', name='Cases Resolved',
                    line=dict(color='#6366f1', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=df_timeline['Date'], y=df_timeline['SOS Resolved'],
                    mode='lines+markers', name='SOS Resolved',
                    line=dict(color='#ef4444', width=3)
                ))
                fig.update_layout(
                    title="Resolution Activity Over Time",
                    template="plotly_dark",
                    xaxis_title="Date",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig, use_container_width=True)

    # TAB 4: Financial Analytics
    with tabs[3]:
        st.markdown("### 💰 Financial Insights")

        col1, col2 = st.columns(2)

        with col1:
            # Donation distribution by campaign
            if donations:
                campaign_donations = {}
                for d in donations:
                    campaign = d.get("campaign_name", "General Fund")
                    amount = d.get("amount", 0)
                    campaign_donations[campaign] = campaign_donations.get(campaign, 0) + amount

                fig = go.Figure(data=[go.Pie(
                    labels=list(campaign_donations.keys()),
                    values=list(campaign_donations.values()),
                    hole=.4
                )])
                fig.update_layout(
                    title="Donations by Campaign",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No donation data available")

        with col2:
            # Top donors
            if donations:
                donor_amounts = {}
                for d in donations:
                    donor = d.get("donor", "Anonymous")
                    if donor != "Anonymous":
                        amount = d.get("amount", 0)
                        donor_amounts[donor] = donor_amounts.get(donor, 0) + amount

                if donor_amounts:
                    df_donors = pd.DataFrame({
                        'Donor': list(donor_amounts.keys()),
                        'Total': list(donor_amounts.values())
                    })
                    df_donors = df_donors.sort_values('Total', ascending=False).head(10)

                    fig = px.bar(df_donors, x='Total', y='Donor',
                                 orientation='h',
                                 title="Top 10 Donors",
                                 template="plotly_dark",
                                 color='Total',
                                 color_continuous_scale='Greens')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No donor data available")
            else:
                st.info("No donation data available")

        # Campaign progress
        st.markdown("### 🎯 Campaign Fundraising Progress")

        if campaigns:
            for camp in campaigns:
                if camp.get("status") == "active":
                    raised = camp.get("raised", 0)
                    target = camp.get("target", 10000)
                    percentage = (raised / target * 100) if target > 0 else 0

                    st.markdown(f"**{camp.get('name', 'Campaign')}**")
                    st.progress(min(percentage / 100, 1.0))
                    st.caption(f"₹{raised:,} / ₹{target:,} ({percentage:.1f}%)")
                    st.markdown("---")
        else:
            st.info("No active campaigns")

    # TAB 5: User Engagement
    with tabs[4]:
        st.markdown("### 👥 Community Engagement Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:
            # User role distribution
            if users:
                role_counts = {}
                for u in users:
                    role = u.get("role", "user")
                    role_counts[role] = role_counts.get(role, 0) + 1

                fig = go.Figure(data=[go.Pie(
                    labels=list(role_counts.keys()),
                    values=list(role_counts.values())
                )])
                fig.update_layout(
                    title="User Role Distribution",
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No user data available")

        with col2:
            # Post engagement
            if posts:
                total_likes = sum(p.get("likes", 0) for p in posts)
                total_comments = sum(len(p.get("comments", [])) for p in posts)

                fig = go.Figure(data=[
                    go.Bar(name='Posts', x=['Engagement'], y=[total_posts]),
                    go.Bar(name='Likes', x=['Engagement'], y=[total_likes]),
                    go.Bar(name='Comments', x=['Engagement'], y=[total_comments])
                ])
                fig.update_layout(
                    title="Community Engagement",
                    template="plotly_dark",
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No post data available")

        with col3:
            # Activity timeline
            st.markdown("#### 📅 Recent Activity")

            all_activities = []

            # Combine recent activities
            for c in cases[-5:]:
                all_activities.append({
                    'time': c.get('time', ''),
                    'type': 'Case',
                    'icon': '🔬'
                })

            for s in sos[-5:]:
                all_activities.append({
                    'time': s.get('time', ''),
                    'type': 'SOS',
                    'icon': '🚨'
                })

            for p in posts[-5:]:
                all_activities.append({
                    'time': p.get('time', ''),
                    'type': 'Post',
                    'icon': '💬'
                })

            all_activities.sort(key=lambda x: x['time'], reverse=True)

            for activity in all_activities[:10]:
                time_str = activity['time'][:19] if len(activity['time']) >= 19 else activity['time']
                st.markdown(f"{activity['icon']} **{activity['type']}** - {time_str}")

        # Volunteer leaderboard
        st.markdown("### 🏆 Volunteer Leaderboard")

        if tasks:
            volunteer_tasks = {}
            for t in tasks:
                if t.get("status") == "completed":
                    volunteer = t.get("assigned_to", "Unknown")
                    volunteer_tasks[volunteer] = volunteer_tasks.get(volunteer, 0) + 1

            if volunteer_tasks:
                df_volunteers = pd.DataFrame({
                    'Volunteer': list(volunteer_tasks.keys()),
                    'Tasks Completed': list(volunteer_tasks.values())
                })
                df_volunteers = df_volunteers.sort_values('Tasks Completed', ascending=False).head(10)

                fig = px.bar(df_volunteers, x='Volunteer', y='Tasks Completed',
                             title="Top 10 Volunteers by Tasks Completed",
                             template="plotly_dark",
                             color='Tasks Completed',
                             color_continuous_scale='Purples')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No completed volunteer tasks yet")
        else:
            st.info("No task data available")

    # TAB 6: Reports
    with tabs[5]:
        st.markdown("### 📄 Generate Comprehensive Reports")

        col1, col2 = st.columns([2, 1])

        with col1:
            report_type = st.selectbox(
                "Select Report Type",
                ["Monthly Summary", "Quarterly Review", "Annual Impact Report",
                 "Campaign Performance", "Volunteer Activity", "Financial Summary"]
            )

            format_type = st.radio(
                "Export Format",
                ["PDF", "CSV"],
                horizontal=True
            )

        with col2:
            st.markdown("#### Quick Stats")
            st.metric("Total Records",
                      sum([total_cases, total_sos, total_adoptions, total_posts]))
            st.metric("Date Range",
                      f"{len(set(c.get('time', '')[:10] for c in cases + sos))} days")

        if st.button("📥 Generate Report", type="primary", use_container_width=True):
            # Prepare report data
            report_data = {
                "title": f"SafePaws AI - {report_type}",
                "generated_on": str(dt.datetime.now()),
                "total_cases": total_cases,
                "resolved_cases": resolved_cases,
                "active_cases": active_cases,
                "case_resolution_rate": case_resolution_rate,
                "total_sos": total_sos,
                "resolved_sos": resolved_sos,
                "sos_resolution_rate": sos_resolution_rate,
                "total_vaccinations": total_campaigns,
                "completed_vaccinations": completed_vaccinations,
                "vaccination_completion_rate": vaccination_completion_rate,
                "total_donations": total_donations,
                "total_donors": total_donors,
                "total_adoptions": total_adoptions,
                "approved_adoptions": approved_adoptions,
                "adoption_approval_rate": adoption_approval_rate,
                "total_posts": total_posts,
                "total_users": total_users,
                "active_volunteers": active_volunteers,
                "total_volunteer_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "task_completion_rate": task_completion_rate,
                "total_prescriptions": total_prescriptions
            }

            report_data_bytes, error = generate_report(report_type, format_type, report_data)

            if error:
                st.error(f"❌ {error}")
            elif report_data_bytes:
                file_ext = "pdf" if format_type == "PDF" else "csv"
                file_name = f"SafePaws_Impact_Report_{dt.datetime.now().strftime('%Y%m%d')}.{file_ext}"

                st.download_button(
                    label=f"📥 Download {format_type} Report",
                    data=report_data_bytes,
                    file_name=file_name,
                    mime=f"application/{file_ext}",
                    use_container_width=True
                )
                st.success(f"✅ Report generated successfully!")
            else:
                st.error("❌ Failed to generate report")

        # Report preview
        st.markdown("### 📊 Report Preview")

        preview_data = {
            "Metric": [
                "Total Disease Cases",
                "Resolved Cases",
                "Emergency Alerts",
                "Vaccinations Completed",
                "Total Donations",
                "Unique Donors",
                "Adoption Applications",
                "Community Posts",
                "Active Volunteers"
            ],
            "Value": [
                total_cases,
                resolved_cases,
                total_sos,
                completed_vaccinations,
                f"₹{total_donations:,}",
                total_donors,
                total_adoptions,
                total_posts,
                active_volunteers
            ],
            "Status": [
                f"{case_resolution_rate:.1f}% resolved",
                f"{active_cases} active",
                f"{sos_resolution_rate:.1f}% resolved",
                f"{vaccination_completion_rate:.1f}% of target",
                f"Avg ₹{(total_donations / len(donations)) if donations else 0:,.0f}",
                f"{len(donations)} donations",
                f"{adoption_approval_rate:.1f}% approved",
                f"{(total_posts / total_users) if total_users > 0 else 0:.1f} per user",
                f"{task_completion_rate:.1f}% task completion"
            ]
        }

        df_preview = pd.DataFrame(preview_data)
        st.dataframe(df_preview, use_container_width=True, hide_index=True)

    # Footer with last update
    st.markdown("---")
    st.caption(f"📊 Dashboard last updated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
               f"Data sources: {len([cases, sos, campaigns, donations, posts, users, tasks])} modules connected")