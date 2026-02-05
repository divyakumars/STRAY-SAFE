# pages/case_management.py

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage
from components import page_header, kpi_card, has_role


def render():
    """Professional veterinary case management system"""
    if not has_role('vet', 'admin'):
        st.error("⛔ Access Denied: Only veterinarians and administrators can access case management")
        return

    user_role = st.session_state.user.get("role")
    user_name = st.session_state.user.get("name", "Unknown")

    page_header("📂", "Case Management System",
                "Complete medical records and case tracking", user_role)

    # Load data
    cases = storage.read("cases", [])

    # Normalize case data structure
    for case in cases:
        case.setdefault("id", f"CASE-{abs(hash(str(case)))}")
        case.setdefault("disease", "Unknown")
        case.setdefault("confidence", 0)
        case.setdefault("status", "pending")
        case.setdefault("severity", "medium")
        case.setdefault("location", "")
        case.setdefault("analyzed_by", "AI")
        case.setdefault("time", str(dt.datetime.now()))
        case.setdefault("assigned_vet", "")
        case.setdefault("treatment_plan", "")
        case.setdefault("outcome", "")
        case.setdefault("vet_notes", "")
        case.setdefault("follow_up_date", "")
        case.setdefault("medications", [])
        case.setdefault("vital_signs", {})

    # Calculate key metrics
    total_cases = len(cases)
    pending = sum(1 for c in cases if c['status'] == 'pending')
    in_treatment = sum(1 for c in cases if c['status'] == 'in_treatment')
    resolved = sum(1 for c in cases if c['status'] == 'resolved')
    critical = sum(1 for c in cases if c.get('severity') == 'critical')

    # Display KPI Dashboard
    st.markdown("### 📊 Case Overview Dashboard")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kpi_card("Total Cases", total_cases, "All registered cases", "📋", "primary")
    with col2:
        kpi_card("Pending Review", pending, "Awaiting assignment", "⏳", "warning")
    with col3:
        kpi_card("In Treatment", in_treatment, "Active cases", "💊", "info")
    with col4:
        kpi_card("Resolved", resolved, "Successfully treated", "✅", "success")
    with col5:
        kpi_card("Critical", critical, "High priority", "🚨", "danger")

    # Main navigation tabs
    tabs = st.tabs([
        "📋 Active Cases",
        "🔍 Case Search",
        "📊 Statistics",
        "📈 Disease Trends"
    ])

    # TAB 1: Active Cases Registry
    with tabs[0]:
        render_active_cases(cases)

    # TAB 2: Case Search
    with tabs[1]:
        render_case_search(cases)

    # TAB 3: Statistics
    with tabs[2]:
        render_statistics(cases)

    # TAB 4: Disease Trends
    with tabs[3]:
        render_disease_trends(cases)


def render_active_cases(cases):
    """Display and manage active cases"""
    st.markdown("### 📋 Active Case Registry")

    # Filter controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Status Filter",
            ["all", "pending", "in_treatment", "resolved", "closed"],
            key="status_filter"
        )

    with col2:
        severity_filter = st.selectbox(
            "Severity Filter",
            ["all", "critical", "high", "medium", "low"],
            key="severity_filter"
        )

    with col3:
        disease_options = ["all"] + sorted(list(set(c['disease'] for c in cases if c.get('disease'))))
        disease_filter = st.selectbox(
            "Disease Type",
            disease_options,
            key="disease_filter"
        )

    with col4:
        sort_option = st.selectbox(
            "Sort By",
            ["Recent First", "Severity (High to Low)", "Status"],
            key="sort_option"
        )

    # Apply filters
    filtered_cases = cases.copy()

    if status_filter != "all":
        filtered_cases = [c for c in filtered_cases if c['status'] == status_filter]

    if severity_filter != "all":
        filtered_cases = [c for c in filtered_cases if c.get('severity') == severity_filter]

    if disease_filter != "all":
        filtered_cases = [c for c in filtered_cases if c['disease'] == disease_filter]

    # Apply sorting
    if sort_option == "Recent First":
        filtered_cases = sorted(filtered_cases, key=lambda x: x.get('time', ''), reverse=True)
    elif sort_option == "Severity (High to Low)":
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        filtered_cases = sorted(filtered_cases, key=lambda x: severity_order.get(x.get('severity', 'medium'), 2))
    else:
        status_order = {"pending": 0, "in_treatment": 1, "resolved": 2, "closed": 3}
        filtered_cases = sorted(filtered_cases, key=lambda x: status_order.get(x['status'], 0))

    st.markdown(f"**Displaying {len(filtered_cases)} of {len(cases)} total cases**")

    if not filtered_cases:
        st.info("No cases match the current filters")
        return

    # Display cases
    for case in filtered_cases[:50]:  # Limit display to 50 cases for performance
        render_case_card(case, cases)


def render_case_card(case, all_cases):
    """Render an individual case card with professional medical layout"""

    # Status and severity color coding
    status_colors = {
        "pending": "🟡",
        "in_treatment": "🔵",
        "resolved": "🟢",
        "closed": "⚫"
    }

    severity_colors = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }

    status_icon = status_colors.get(case['status'], "⚪")
    severity_icon = severity_colors.get(case.get('severity', 'medium'), "⚪")

    # Case header
    case_title = f"{status_icon} {case['id']} - {case['disease'].title()} {severity_icon}"

    with st.expander(case_title):

        # Two-column layout for case details
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### 📄 Case Information")

            # Basic information
            st.markdown(f"**Disease:** {case['disease'].title()}")
            st.markdown(f"**AI Confidence:** {case.get('confidence', 0) * 100:.1f}%")
            st.markdown(f"**Severity Level:** {case.get('severity', 'medium').title()}")
            st.markdown(f"**Status:** {case['status'].replace('_', ' ').title()}")
            st.markdown(f"**Location:** {case.get('location', 'Not specified')}")
            st.markdown(f"**Detected:** {case.get('time', 'Unknown')[:16]}")
            st.markdown(f"**Analyzed By:** {case.get('analyzed_by', 'AI System')}")

            if case.get('assigned_vet'):
                st.markdown(f"**Assigned Vet:** {case['assigned_vet']}")

            if case.get('follow_up_date'):
                st.markdown(f"**Follow-up Date:** {case['follow_up_date']}")

            st.markdown("---")

            # Medical notes section
            st.markdown("#### 🩺 Medical Assessment")

            if case.get('vet_notes'):
                st.text_area(
                    "Veterinary Notes",
                    value=case['vet_notes'],
                    height=100,
                    disabled=True,
                    key=f"notes_view_{case['id']}"
                )
            else:
                st.info("No veterinary notes recorded yet")

            # Treatment plan
            if case.get('treatment_plan'):
                st.markdown("**Treatment Plan:**")
                st.text_area(
                    "Treatment Details",
                    value=case['treatment_plan'],
                    height=100,
                    disabled=True,
                    key=f"treatment_view_{case['id']}"
                )

            # Medications
            if case.get('medications') and len(case['medications']) > 0:
                st.markdown("**Prescribed Medications:**")
                for idx, med in enumerate(case['medications'], 1):
                    st.markdown(f"{idx}. {med}")

            # Outcome
            if case.get('outcome'):
                st.markdown("**Treatment Outcome:**")
                st.text_area(
                    "Outcome",
                    value=case['outcome'],
                    height=80,
                    disabled=True,
                    key=f"outcome_view_{case['id']}"
                )

        with col2:
            st.markdown("#### ⚡ Quick Actions")

            # Action buttons
            if case['status'] == 'pending':
                if st.button("📝 Review Case", key=f"review_{case['id']}", use_container_width=True):
                    st.session_state.editing_case = case['id']
                    st.rerun()

            if case['status'] != 'resolved' and case['status'] != 'closed':
                if st.button("💊 Update Treatment", key=f"update_{case['id']}", use_container_width=True):
                    st.session_state.updating_case = case['id']
                    st.rerun()

            if case['status'] == 'in_treatment':
                if st.button("✅ Mark Resolved", key=f"resolve_{case['id']}", use_container_width=True):
                    case['status'] = 'resolved'
                    storage.write("cases", all_cases)
                    st.success("Case marked as resolved")
                    st.rerun()

            if has_role('admin'):
                if st.button("🗄️ Archive Case", key=f"archive_{case['id']}", use_container_width=True):
                    case['status'] = 'closed'
                    storage.write("cases", all_cases)
                    st.success("Case archived")
                    st.rerun()

            st.markdown("---")

            # Case metadata
            st.markdown("#### 📌 Case Metadata")

            days_open = "N/A"
            try:
                case_date = dt.datetime.fromisoformat(case['time'][:19])
                days_open = (dt.datetime.now() - case_date).days
                st.metric("Days Open", days_open)
            except:
                st.metric("Days Open", "N/A")

            # Priority indicator
            if case.get('severity') == 'critical':
                st.warning("⚠️ CRITICAL - Immediate attention required")
            elif case.get('severity') == 'high':
                st.info("⚡ HIGH priority case")

        # Editing interface
        if st.session_state.get('editing_case') == case['id']:
            render_case_editor(case, all_cases)

        if st.session_state.get('updating_case') == case['id']:
            render_treatment_updater(case, all_cases)


def render_case_editor(case, all_cases):
    """Professional case review and editing interface"""
    st.markdown("---")
    st.markdown("### 📝 Case Review & Update")

    with st.form(key=f"edit_form_{case['id']}"):
        col1, col2 = st.columns(2)

        with col1:
            new_status = st.selectbox(
                "Case Status",
                ["pending", "in_treatment", "resolved", "closed"],
                index=["pending", "in_treatment", "resolved", "closed"].index(case['status'])
            )

            new_severity = st.selectbox(
                "Severity Level",
                ["low", "medium", "high", "critical"],
                index=["low", "medium", "high", "critical"].index(case.get('severity', 'medium'))
            )

            assigned_vet = st.text_input(
                "Assign to Veterinarian",
                value=case.get('assigned_vet', st.session_state.user.get('name', ''))
            )

        with col2:
            follow_up = st.date_input(
                "Follow-up Date",
                value=dt.date.today() + dt.timedelta(days=7)
            )

        vet_notes = st.text_area(
            "Veterinary Assessment Notes",
            value=case.get('vet_notes', ''),
            height=150,
            help="Record clinical observations, diagnosis, and recommendations"
        )

        treatment_plan = st.text_area(
            "Treatment Plan",
            value=case.get('treatment_plan', ''),
            height=150,
            help="Detailed treatment protocol and procedures"
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save Updates", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            case['status'] = new_status
            case['severity'] = new_severity
            case['assigned_vet'] = assigned_vet
            case['vet_notes'] = vet_notes
            case['treatment_plan'] = treatment_plan
            case['follow_up_date'] = str(follow_up)
            case['last_updated'] = str(dt.datetime.now())

            storage.write("cases", all_cases)
            st.session_state.editing_case = None
            st.success("✅ Case updated successfully")
            st.rerun()

        if cancel:
            st.session_state.editing_case = None
            st.rerun()


def render_treatment_updater(case, all_cases):
    """Update treatment progress and medications"""
    st.markdown("---")
    st.markdown("### 💊 Treatment Progress Update")

    with st.form(key=f"treatment_form_{case['id']}"):

        treatment_notes = st.text_area(
            "Treatment Progress Notes",
            height=100,
            help="Record treatment administration and patient response"
        )

        medication = st.text_input(
            "Add Medication",
            help="Enter medication name, dosage, and frequency"
        )

        outcome_update = st.text_area(
            "Current Outcome/Response",
            value=case.get('outcome', ''),
            height=100,
            help="Patient's response to treatment"
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Update Treatment", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            if treatment_notes:
                current_notes = case.get('vet_notes', '')
                case['vet_notes'] = f"{current_notes}\n\n[{dt.datetime.now():%Y-%m-%d %H:%M}] {treatment_notes}"

            if medication:
                if 'medications' not in case:
                    case['medications'] = []
                case['medications'].append(medication)

            if outcome_update:
                case['outcome'] = outcome_update

            case['last_updated'] = str(dt.datetime.now())

            storage.write("cases", all_cases)
            st.session_state.updating_case = None
            st.success("✅ Treatment record updated")
            st.rerun()

        if cancel:
            st.session_state.updating_case = None
            st.rerun()


def render_case_search(cases):
    """Advanced case search functionality"""
    st.markdown("### 🔍 Case Search")

    search_query = st.text_input(
        "Search cases",
        placeholder="Enter case ID, disease, location, or veterinarian name...",
        key="case_search"
    )

    if search_query and len(search_query) >= 2:
        query_lower = search_query.lower()

        results = [
            c for c in cases
            if query_lower in c['id'].lower()
               or query_lower in c.get('disease', '').lower()
               or query_lower in c.get('location', '').lower()
               or query_lower in c.get('assigned_vet', '').lower()
               or query_lower in c.get('vet_notes', '').lower()
        ]

        st.markdown(f"**Found {len(results)} matching cases**")

        if results:
            for case in results[:20]:  # Limit to 20 results
                render_case_card(case, cases)
        else:
            st.info("No cases found matching your search criteria")
    else:
        st.info("Enter at least 2 characters to search")


def render_statistics(cases):
    """Display case statistics and analytics"""
    st.markdown("### 📊 Case Statistics & Analytics")

    if not cases:
        st.info("No case data available for analysis")
        return

    # Disease distribution
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🦠 Disease Distribution")

        disease_counts = {}
        for c in cases:
            disease = c.get('disease', 'Unknown')
            disease_counts[disease] = disease_counts.get(disease, 0) + 1

        if disease_counts:
            disease_df = pd.DataFrame([
                {
                    "Disease": disease,
                    "Cases": count,
                    "Percentage": f"{count / len(cases) * 100:.1f}%"
                }
                for disease, count in sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)
            ])

            st.dataframe(
                disease_df,
                use_container_width=True,
                hide_index=True
            )

    with col2:
        st.markdown("#### 📍 Location Distribution")

        location_counts = {}
        for c in cases:
            loc = c.get('location', 'Unknown')
            if loc and loc != 'Unknown':
                location_counts[loc] = location_counts.get(loc, 0) + 1

        if location_counts:
            location_df = pd.DataFrame([
                {"Location": loc, "Cases": count}
                for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ])

            st.dataframe(
                location_df,
                use_container_width=True,
                hide_index=True
            )

    # Status breakdown
    st.markdown("---")
    st.markdown("#### 📋 Case Status Breakdown")

    col1, col2, col3, col4 = st.columns(4)

    status_counts = {
        'pending': sum(1 for c in cases if c['status'] == 'pending'),
        'in_treatment': sum(1 for c in cases if c['status'] == 'in_treatment'),
        'resolved': sum(1 for c in cases if c['status'] == 'resolved'),
        'closed': sum(1 for c in cases if c['status'] == 'closed')
    }

    with col1:
        st.metric("Pending", status_counts['pending'])
    with col2:
        st.metric("In Treatment", status_counts['in_treatment'])
    with col3:
        st.metric("Resolved", status_counts['resolved'])
    with col4:
        st.metric("Closed", status_counts['closed'])

    # Severity breakdown
    st.markdown("#### ⚠️ Severity Distribution")

    col1, col2, col3, col4 = st.columns(4)

    severity_counts = {
        'critical': sum(1 for c in cases if c.get('severity') == 'critical'),
        'high': sum(1 for c in cases if c.get('severity') == 'high'),
        'medium': sum(1 for c in cases if c.get('severity') == 'medium'),
        'low': sum(1 for c in cases if c.get('severity') == 'low')
    }

    with col1:
        st.metric("Critical", severity_counts['critical'], delta="Urgent")
    with col2:
        st.metric("High", severity_counts['high'])
    with col3:
        st.metric("Medium", severity_counts['medium'])
    with col4:
        st.metric("Low", severity_counts['low'])


def render_disease_trends(cases):
    """Display disease trends and patterns"""
    st.markdown("### 📈 Disease Trends & Patterns")

    if not cases:
        st.info("No case data available for trend analysis")
        return

    # Time-based analysis
    st.markdown("#### 📅 Recent Activity Summary")

    now = dt.datetime.now()

    # Calculate date ranges
    today_cases = []
    week_cases = []
    month_cases = []

    for case in cases:
        try:
            case_date = dt.datetime.fromisoformat(case.get('time', '')[:19])
            days_ago = (now - case_date).days

            if days_ago == 0:
                today_cases.append(case)
            if days_ago <= 7:
                week_cases.append(case)
            if days_ago <= 30:
                month_cases.append(case)
        except:
            continue

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Today", len(today_cases))
    with col2:
        st.metric("This Week", len(week_cases))
    with col3:
        st.metric("This Month", len(month_cases))

    st.markdown("---")

    # Top diseases this month
    if month_cases:
        st.markdown("#### 🔥 Top Diseases This Month")

        disease_counts = {}
        for case in month_cases:
            disease = case.get('disease', 'Unknown')
            disease_counts[disease] = disease_counts.get(disease, 0) + 1

        top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        for idx, (disease, count) in enumerate(top_diseases, 1):
            st.markdown(f"{idx}. **{disease.title()}**: {count} cases")

    st.markdown("---")

    # Critical cases requiring attention
    critical_cases = [c for c in cases if c.get('severity') == 'critical' and c['status'] != 'resolved']

    if critical_cases:
        st.warning(f"⚠️ **{len(critical_cases)} Critical Cases Requiring Immediate Attention**")

        for case in critical_cases[:5]:
            st.markdown(f"- {case['id']}: {case['disease'].title()} ({case.get('location', 'Unknown location')})")

    # Performance metrics
    st.markdown("---")
    st.markdown("#### 📊 System Performance Metrics")

    resolved_cases = [c for c in cases if c['status'] == 'resolved']

    if len(cases) > 0:
        resolution_rate = (len(resolved_cases) / len(cases)) * 100
        st.metric("Case Resolution Rate", f"{resolution_rate:.1f}%")

    # Average AI confidence
    avg_confidence = sum(c.get('confidence', 0) for c in cases) / len(cases) if cases else 0
    st.metric("Average AI Detection Confidence", f"{avg_confidence * 100:.1f}%")