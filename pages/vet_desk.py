# pages/vet_desk.py

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage
from components import page_header, kpi_card, has_role


def render():
    """Professional veterinarian dashboard and workflow management"""
    if not has_role('vet', 'admin'):
        st.error("⛔ Access Denied: Only veterinarians and administrators can access this page")
        return

    user_role = st.session_state.user.get("role")
    user_name = st.session_state.user.get("name", "Unknown Vet")

    page_header("🩺", "Veterinary Desk",
                "Your personal medical consultation and case management workspace", user_role)

    # Load all necessary data
    cases = storage.read("cases", [])
    prescriptions = storage.read("prescriptions", [])
    sos = storage.read("sos", [])

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
        case.setdefault("vet_notes", "")
        case.setdefault("treatment_plan", "")
        case.setdefault("assigned_vet", "")
        case.setdefault("follow_up_date", "")
        case.setdefault("medications", [])

    # Calculate personal metrics
    my_cases = [c for c in cases if c.get('assigned_vet') == user_name]
    pending_cases = [c for c in my_cases if c['status'] == 'pending']
    in_treatment = [c for c in my_cases if c['status'] == 'in_treatment']
    resolved = [c for c in my_cases if c['status'] == 'resolved']
    critical_cases = [c for c in my_cases if c.get('severity') == 'critical']

    # Display personalized KPI dashboard
    st.markdown(f"### 📊 {user_name}'s Caseload Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card("My Total Cases", len(my_cases), "All assigned to me", "📋", "primary")
    with col2:
        kpi_card("Pending", len(pending_cases), "Awaiting review", "⏳", "warning")
    with col3:
        kpi_card("In Treatment", len(in_treatment), "Active treatment", "💊", "info")
    with col4:
        kpi_card("Critical", len(critical_cases), "Urgent attention needed", "🚨", "danger")

    # Main workspace tabs
    tabs = st.tabs([
        "📋 My Active Cases",
        "🆕 Unassigned Cases",
        "💊 Prescriptions",
        "🚨 Emergency Queue",
        "📊 My Statistics"
    ])

    # TAB 1: My Active Cases
    with tabs[0]:
        render_my_cases(my_cases, cases, user_name)

    # TAB 2: Unassigned Cases
    with tabs[1]:
        render_unassigned_cases(cases, user_name)

    # TAB 3: Prescriptions
    with tabs[2]:
        render_prescriptions(prescriptions, user_name)

    # TAB 4: Emergency Queue
    with tabs[3]:
        render_emergency_queue(sos, user_name)

    # TAB 5: Statistics
    with tabs[4]:
        render_vet_statistics(my_cases, prescriptions, user_name)


def render_my_cases(my_cases, all_cases, user_name):
    """Display veterinarian's assigned cases"""
    st.markdown("### 📋 My Assigned Cases")

    if not my_cases:
        st.info("You have no assigned cases yet. Check the 'Unassigned Cases' tab to pick up new cases.")
        return

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["all", "pending", "in_treatment", "resolved"],
            key="my_cases_status"
        )

    with col2:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["all", "critical", "high", "medium", "low"],
            key="my_cases_severity"
        )

    with col3:
        sort_option = st.selectbox(
            "Sort By",
            ["Recent First", "Severity (High to Low)", "Status"],
            key="my_cases_sort"
        )

    # Apply filters
    filtered = my_cases.copy()

    if status_filter != "all":
        filtered = [c for c in filtered if c['status'] == status_filter]

    if severity_filter != "all":
        filtered = [c for c in filtered if c.get('severity', 'medium').lower() == severity_filter]

    # Apply sorting
    if sort_option == "Recent First":
        filtered = sorted(filtered, key=lambda x: x.get('time', ''), reverse=True)
    elif sort_option == "Severity (High to Low)":
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        filtered = sorted(filtered, key=lambda x: severity_order.get(x.get('severity', 'medium').lower(), 2))
    else:
        status_order = {"pending": 0, "in_treatment": 1, "resolved": 2}
        filtered = sorted(filtered, key=lambda x: status_order.get(x['status'], 0))

    st.markdown(f"**Displaying {len(filtered)} of {len(my_cases)} cases**")

    # Display cases
    for case in filtered:
        render_case_consultation(case, all_cases, user_name)


def render_case_consultation(case, all_cases, user_name):
    """Professional case consultation card"""

    # Normalize severity to lowercase for consistent handling
    case_severity = case.get('severity', 'medium').lower()

    # Status indicators
    status_emoji = {
        "pending": "🟡",
        "in_treatment": "🔵",
        "resolved": "🟢",
        "closed": "⚫"
    }

    severity_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }

    status_icon = status_emoji.get(case['status'], "⚪")
    severity_icon = severity_emoji.get(case_severity, "⚪")

    case_title = f"{status_icon} {case['id']} - {case['disease'].title()} {severity_icon}"

    with st.expander(case_title, expanded=(case['status'] == 'pending')):

        # Case information layout
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### 📄 Case Details")

            # Display case information
            info_col1, info_col2 = st.columns(2)

            with info_col1:
                st.markdown(f"**Disease:** {case['disease'].title()}")
                st.markdown(f"**AI Confidence:** {case.get('confidence', 0) * 100:.1f}%")
                st.markdown(f"**Severity:** {case_severity.title()}")
                st.markdown(f"**Status:** {case['status'].replace('_', ' ').title()}")

            with info_col2:
                st.markdown(f"**Location:** {case.get('location', 'Not specified')}")
                st.markdown(f"**Detected:** {case.get('time', 'Unknown')[:16]}")
                st.markdown(f"**Analyzed By:** {case.get('analyzed_by', 'AI System')}")

                if case.get('follow_up_date'):
                    st.markdown(f"**Follow-up:** {case['follow_up_date']}")

            st.markdown("---")

            # Medical documentation
            st.markdown("#### 🩺 Medical Documentation")

            if case.get('vet_notes'):
                st.markdown("**Clinical Notes:**")
                st.text_area(
                    "Clinical Notes",
                    value=case['vet_notes'],
                    height=120,
                    disabled=True,
                    key=f"view_notes_{case['id']}",
                    label_visibility="collapsed"
                )
            else:
                st.info("No clinical notes recorded")

            if case.get('treatment_plan'):
                st.markdown("**Treatment Plan:**")
                st.text_area(
                    "Treatment Plan",
                    value=case['treatment_plan'],
                    height=120,
                    disabled=True,
                    key=f"view_treatment_{case['id']}",
                    label_visibility="collapsed"
                )

            # Medications
            if case.get('medications') and len(case['medications']) > 0:
                st.markdown("**Prescribed Medications:**")
                for idx, med in enumerate(case['medications'], 1):
                    st.markdown(f"{idx}. {med}")

        with col2:
            st.markdown("#### ⚡ Actions")

            # Consultation actions based on status
            if case['status'] == 'pending':
                if st.button("📝 Start Consultation", key=f"consult_{case['id']}", use_container_width=True,
                             type="primary"):
                    st.session_state.consulting_case = case['id']
                    st.rerun()

            if case['status'] == 'in_treatment':
                if st.button("📝 Update Treatment", key=f"update_{case['id']}", use_container_width=True,
                             type="primary"):
                    st.session_state.updating_treatment = case['id']
                    st.rerun()

                if st.button("💊 Add Prescription", key=f"prescribe_{case['id']}", use_container_width=True):
                    st.session_state.create_prescription_for = case['id']
                    st.rerun()

            if case['status'] != 'resolved':
                if st.button("✅ Mark as Resolved", key=f"resolve_{case['id']}", use_container_width=True):
                    case['status'] = 'resolved'
                    case['last_updated'] = str(dt.datetime.now())
                    storage.write("cases", all_cases)
                    st.success("✅ Case marked as resolved!")
                    st.rerun()

            st.markdown("---")

            # Case metadata
            st.markdown("#### 📊 Case Info")

            try:
                case_date = dt.datetime.fromisoformat(case['time'][:19])
                days_open = (dt.datetime.now() - case_date).days
                st.metric("Days Open", days_open)
            except:
                st.metric("Days Open", "N/A")

            if case_severity == 'critical':
                st.error("⚠️ CRITICAL PRIORITY")
            elif case_severity == 'high':
                st.warning("⚡ HIGH PRIORITY")

        # Consultation interface
        if st.session_state.get('consulting_case') == case['id']:
            render_consultation_form(case, all_cases, user_name)

        if st.session_state.get('updating_treatment') == case['id']:
            render_treatment_update_form(case, all_cases, user_name)


def render_consultation_form(case, all_cases, user_name):
    """Professional consultation and treatment planning form"""
    st.markdown("---")
    st.markdown("### 📝 Clinical Consultation")

    with st.form(key=f"consultation_form_{case['id']}"):

        st.markdown("#### Patient Assessment")

        # Clinical observations
        clinical_notes = st.text_area(
            "Clinical Observations & Symptoms",
            height=150,
            placeholder="Document patient history, physical examination findings, clinical signs, symptoms observed...",
            help="Record detailed clinical observations"
        )

        col1, col2 = st.columns(2)

        with col1:
            # Diagnosis confirmation
            confirmed_diagnosis = st.text_input(
                "Confirmed Diagnosis",
                value=case['disease'].title(),
                help="Confirm or modify the AI-detected diagnosis"
            )

            # Severity assessment
            # Normalize severity to lowercase for comparison
            current_severity = case.get('severity', 'medium').lower()
            severity_options = ["low", "medium", "high", "critical"]

            # Find index, default to medium if not found
            try:
                severity_index = severity_options.index(current_severity)
            except ValueError:
                severity_index = 1  # Default to 'medium'

            severity = st.selectbox(
                "Severity Level",
                severity_options,
                index=severity_index
            )

        with col2:
            # Prognosis
            prognosis = st.selectbox(
                "Prognosis",
                ["Excellent", "Good", "Fair", "Guarded", "Poor"],
                index=1
            )

            # Follow-up scheduling
            follow_up_date = st.date_input(
                "Schedule Follow-up",
                value=dt.date.today() + dt.timedelta(days=7)
            )

        st.markdown("#### Treatment Plan")

        # Treatment protocol
        treatment_plan = st.text_area(
            "Treatment Protocol",
            height=150,
            placeholder="Prescribed medications, dosages, procedures, care instructions, dietary recommendations...",
            help="Document comprehensive treatment plan"
        )

        # Initial medication
        medication = st.text_input(
            "Primary Medication (optional)",
            placeholder="e.g., Amoxicillin 250mg - 2x daily for 7 days"
        )

        # Special instructions
        special_instructions = st.text_area(
            "Special Instructions & Precautions",
            height=100,
            placeholder="Any special care instructions, warnings, monitoring requirements..."
        )

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("💾 Complete Consultation", type="primary", use_container_width=True)

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            # Update case with consultation details
            case['status'] = 'in_treatment'
            case['disease'] = confirmed_diagnosis
            case['severity'] = severity
            case['vet_notes'] = clinical_notes
            case['treatment_plan'] = treatment_plan
            case['follow_up_date'] = str(follow_up_date)
            case['last_updated'] = str(dt.datetime.now())
            case['prognosis'] = prognosis

            if special_instructions:
                case['vet_notes'] += f"\n\n**Special Instructions:**\n{special_instructions}"

            if medication:
                if 'medications' not in case:
                    case['medications'] = []
                case['medications'].append(medication)

            storage.write("cases", all_cases)
            st.session_state.consulting_case = None
            st.success("✅ Consultation completed successfully!")
            st.rerun()

        if cancel:
            st.session_state.consulting_case = None
            st.rerun()


def render_treatment_update_form(case, all_cases, user_name):
    """Update treatment progress"""
    st.markdown("---")
    st.markdown("### 💊 Treatment Progress Update")

    with st.form(key=f"treatment_update_{case['id']}"):

        progress_notes = st.text_area(
            "Treatment Progress Notes",
            height=120,
            placeholder="Document treatment response, any changes in condition, complications, improvements..."
        )

        additional_medication = st.text_input(
            "Add Additional Medication",
            placeholder="e.g., Pain reliever - Carprofen 50mg - 1x daily"
        )

        col1, col2 = st.columns(2)

        with col1:
            # Normalize severity to lowercase
            current_severity = case.get('severity', 'medium').lower()
            severity_options = ["low", "medium", "high", "critical"]

            try:
                severity_index = severity_options.index(current_severity)
            except ValueError:
                severity_index = 1  # Default to 'medium'

            update_severity = st.selectbox(
                "Update Severity",
                severity_options,
                index=severity_index
            )

        with col2:
            update_status = st.selectbox(
                "Update Status",
                ["in_treatment", "resolved"],
                index=0 if case['status'] == 'in_treatment' else 1
            )

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("💾 Save Progress", type="primary", use_container_width=True)

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            if progress_notes:
                timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                case['vet_notes'] = f"{case.get('vet_notes', '')}\n\n[{timestamp}] Progress Update:\n{progress_notes}"

            if additional_medication:
                if 'medications' not in case:
                    case['medications'] = []
                case['medications'].append(additional_medication)

            case['severity'] = update_severity
            case['status'] = update_status
            case['last_updated'] = str(dt.datetime.now())

            storage.write("cases", all_cases)
            st.session_state.updating_treatment = None
            st.success("✅ Treatment progress updated!")
            st.rerun()

        if cancel:
            st.session_state.updating_treatment = None
            st.rerun()


def render_unassigned_cases(cases, user_name):
    """Display cases available for assignment"""
    st.markdown("### 🆕 Unassigned Cases - Pick Up New Cases")

    # Get unassigned cases
    unassigned = [c for c in cases if not c.get('assigned_vet') or c.get('assigned_vet') == '']

    if not unassigned:
        st.success("✅ No unassigned cases - all cases have been assigned!")
        return

    st.markdown(f"**{len(unassigned)} cases awaiting assignment**")

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    unassigned = sorted(unassigned, key=lambda x: severity_order.get(x.get('severity', 'medium'), 2))

    # Display unassigned cases
    for case in unassigned[:20]:  # Show first 20
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        severity_icon = severity_emoji.get(case.get('severity', 'medium'), "⚪")

        case_title = f"{severity_icon} {case['id']} - {case['disease'].title()}"

        with st.expander(case_title):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Disease:** {case['disease'].title()}")
                st.markdown(f"**AI Confidence:** {case.get('confidence', 0) * 100:.1f}%")
                st.markdown(f"**Severity:** {case.get('severity', 'medium').title()}")
                st.markdown(f"**Location:** {case.get('location', 'Not specified')}")
                st.markdown(f"**Detected:** {case.get('time', 'Unknown')[:16]}")

            with col2:
                if st.button("📋 Assign to Me", key=f"assign_{case['id']}", use_container_width=True, type="primary"):
                    case['assigned_vet'] = user_name
                    case['status'] = 'pending'
                    case['last_updated'] = str(dt.datetime.now())
                    storage.write("cases", cases)
                    st.success(f"✅ Case {case['id']} assigned to you!")
                    st.rerun()


def render_prescriptions(prescriptions, user_name):
    """Manage prescriptions"""
    st.markdown("### 💊 Prescription Management")

    # Check if creating new prescription
    if st.session_state.get('create_prescription_for'):
        case_id = st.session_state.create_prescription_for
        st.markdown(f"#### 📝 New Prescription for Case: {case_id}")

        with st.form("new_prescription_form"):
            col1, col2 = st.columns(2)

            with col1:
                medication = st.text_input("Medication Name *", placeholder="e.g., Amoxicillin")
                dosage = st.text_input("Dosage *", placeholder="e.g., 250mg")

            with col2:
                frequency = st.text_input("Frequency *", placeholder="e.g., 2x daily")
                duration = st.text_input("Duration *", placeholder="e.g., 7 days")

            instructions = st.text_area(
                "Administration Instructions",
                placeholder="Detailed instructions for medication administration..."
            )

            warnings = st.text_area(
                "Warnings & Contraindications",
                placeholder="Any warnings, side effects to monitor, contraindications..."
            )

            col1, col2 = st.columns(2)

            with col1:
                submit = st.form_submit_button("💾 Create Prescription", type="primary", use_container_width=True)

            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit and medication and dosage and frequency and duration:
                prescription = {
                    "id": f"RX-{int(dt.datetime.now().timestamp())}",
                    "case_id": case_id,
                    "prescribed_by": user_name,
                    "prescribed_at": str(dt.datetime.now()),
                    "medication": medication,
                    "dosage": dosage,
                    "frequency": frequency,
                    "duration": duration,
                    "instructions": instructions,
                    "warnings": warnings,
                    "status": "active"
                }

                prescriptions.append(prescription)
                storage.write("prescriptions", prescriptions)
                st.session_state.create_prescription_for = None
                st.success("✅ Prescription created successfully!")
                st.rerun()

            if cancel:
                st.session_state.create_prescription_for = None
                st.rerun()

    # Display existing prescriptions
    st.markdown("---")
    st.markdown("#### 📋 My Issued Prescriptions")

    my_prescriptions = [rx for rx in prescriptions if rx.get('prescribed_by') == user_name]

    if not my_prescriptions:
        st.info("No prescriptions issued yet")
        return

    # Filter prescriptions
    col1, col2 = st.columns(2)

    with col1:
        rx_filter = st.selectbox("Filter by Status", ["all", "active", "completed", "cancelled"])

    with col2:
        rx_sort = st.selectbox("Sort By", ["Recent First", "Case ID"])

    # Apply filters
    filtered_rx = my_prescriptions.copy()

    if rx_filter != "all":
        filtered_rx = [rx for rx in filtered_rx if rx.get('status') == rx_filter]

    # Sort
    if rx_sort == "Recent First":
        filtered_rx = sorted(filtered_rx, key=lambda x: x.get('prescribed_at', ''), reverse=True)
    else:
        filtered_rx = sorted(filtered_rx, key=lambda x: x.get('case_id', ''))

    st.markdown(f"**Showing {len(filtered_rx)} prescriptions**")

    # Display prescriptions
    for rx in filtered_rx:
        status_icon = "✅" if rx.get('status') == 'completed' else "❌" if rx.get('status') == 'cancelled' else "💊"

        with st.expander(f"{status_icon} {rx['id']} - {rx.get('medication', 'N/A')}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Case ID:** {rx.get('case_id', 'N/A')}")
                st.markdown(f"**Medication:** {rx.get('medication', 'N/A')}")
                st.markdown(f"**Dosage:** {rx.get('dosage', 'N/A')}")
                st.markdown(f"**Frequency:** {rx.get('frequency', 'N/A')}")
                st.markdown(f"**Duration:** {rx.get('duration', 'N/A')}")
                st.markdown(f"**Prescribed:** {rx.get('prescribed_at', '')[:16]}")

                if rx.get('instructions'):
                    st.markdown(f"**Instructions:** {rx['instructions']}")

                if rx.get('warnings'):
                    st.warning(f"⚠️ {rx['warnings']}")

            with col2:
                st.markdown(f"**Status:** {rx.get('status', 'active').upper()}")

                if rx.get('status') == 'active':
                    if st.button("✅ Mark Complete", key=f"complete_{rx['id']}", use_container_width=True):
                        rx['status'] = 'completed'
                        rx['completed_at'] = str(dt.datetime.now())
                        storage.write("prescriptions", prescriptions)
                        st.success("Prescription marked as completed")
                        st.rerun()

                    if st.button("❌ Cancel Rx", key=f"cancel_{rx['id']}", use_container_width=True):
                        rx['status'] = 'cancelled'
                        rx['cancelled_at'] = str(dt.datetime.now())
                        storage.write("prescriptions", prescriptions)
                        st.warning("Prescription cancelled")
                        st.rerun()


def render_emergency_queue(sos_cases, user_name):
    """Display emergency SOS queue"""
    st.markdown("### 🚨 Emergency SOS Queue")

    # Workflow explanation
    with st.expander("ℹ️ How Emergency Response Works", expanded=False):
        st.markdown("""
        **Emergency Workflow:**

        1. **🆕 Active** - New emergency reported, waiting for response
        2. **🚀 Dispatched** - You accepted and are responding to the emergency
        3. **✅ Resolved** - Emergency handled and closed

        **Your Actions:**
        - Click **"Accept & Dispatch"** on unassigned emergencies to take responsibility
        - Click **"Mark as Resolved"** when you've successfully handled the emergency
        """)

    # Show both active (unassigned) and dispatched (assigned to me)
    active_emergencies = [s for s in sos_cases if s.get('status') == 'active']
    my_dispatched = [s for s in sos_cases if s.get('status') == 'dispatched' and s.get('assigned') == user_name]

    # Combine for display
    all_my_emergencies = active_emergencies + my_dispatched

    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🆕 Unassigned", len(active_emergencies), "Need response")
    with col2:
        st.metric("🚀 My Active", len(my_dispatched), "Assigned to me")
    with col3:
        critical_count = sum(1 for s in all_my_emergencies if s.get('severity', '').lower() == 'critical')
        st.metric("🔴 Critical", critical_count, "High priority")

    if not all_my_emergencies:
        st.success("✅ No active emergencies requiring your attention")
        st.info("💡 New emergencies will appear here automatically")
        return

    st.markdown("---")

    # Sort by severity and risk
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_my_emergencies = sorted(
        all_my_emergencies,
        key=lambda x: (severity_order.get(x.get('severity', 'Medium').lower(), 3), -x.get('risk', 0))
    )

    for sos in all_my_emergencies:
        risk_level = sos.get('risk', 0)
        # Normalize severity to lowercase
        severity = sos.get('severity', 'Medium').title()  # Capitalize for display
        severity_lower = severity.lower()
        status = sos.get('status', 'active')

        # Priority indicators
        if severity_lower == 'critical' or risk_level >= 70:
            priority_color = "🔴"
            priority_text = "CRITICAL"
        elif severity_lower == 'high' or risk_level >= 50:
            priority_color = "🟠"
            priority_text = "HIGH"
        else:
            priority_color = "🟡"
            priority_text = "MEDIUM"

        # Status indicator
        status_emoji = {
            'active': '🆕',
            'dispatched': '🚀'
        }
        status_icon = status_emoji.get(status, '⚪')

        expander_title = f"{status_icon} {priority_color} {sos['id']} - {severity} ({priority_text})"

        with st.expander(expander_title, expanded=(severity_lower == 'critical' or status == 'active')):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### 📍 Emergency Details")

                # Location information
                location_display = sos.get('full_address') or sos.get('place', 'Unknown')
                st.markdown(f"**Location:** {location_display}")
                st.markdown(f"**Severity:** {severity}")
                st.markdown(f"**Type:** {sos.get('type', 'Emergency')}")

                if risk_level > 0:
                    st.markdown(f"**Risk Score:** {risk_level}%")

                st.markdown(f"**Reported:** {sos.get('time', 'Unknown')[:16]}")
                st.markdown(f"**Reporter:** {sos.get('created_by', 'Anonymous')}")

                if sos.get('description'):
                    st.markdown(f"**Description:** {sos['description']}")

                # Show assignment info if dispatched
                if status == 'dispatched':
                    st.info(f"🚀 Assigned to you at {sos.get('dispatched_at', '')[:16]}")

                # Show coordinates if available
                if sos.get('coords'):
                    coords = sos['coords']
                    if isinstance(coords, (list, tuple)) and len(coords) == 2:
                        st.caption(f"📍 GPS: {coords[0]:.6f}, {coords[1]:.6f}")

            with col2:
                st.markdown("#### ⚡ Actions")

                if status == 'active':
                    # Unassigned emergency - vet can accept it
                    st.info("🆕 Unassigned - Available")

                    if st.button("✋ Accept & Dispatch", key=f"accept_{sos['id']}", use_container_width=True,
                                 type="primary"):
                        sos['status'] = 'dispatched'
                        sos['assigned'] = user_name
                        sos['dispatched_at'] = str(dt.datetime.now())
                        storage.write("sos", sos_cases)

                        # Create notification
                        from components import create_notification
                        create_notification("info", f"🚀 SOS {sos['id']} dispatched to {user_name}", "normal")

                        st.success(f"✅ Emergency {sos['id']} assigned to you!")
                        st.rerun()

                elif status == 'dispatched' and sos.get('assigned') == user_name:
                    # Already assigned to this vet - can mark as resolved
                    st.success("✅ Assigned to You")

                    if st.button("✅ Mark as Resolved", key=f"resolve_{sos['id']}", use_container_width=True,
                                 type="primary"):
                        sos['status'] = 'resolved'
                        sos['resolved_by'] = user_name
                        sos['resolved_at'] = str(dt.datetime.now())
                        storage.write("sos", sos_cases)

                        # Create notification
                        from components import create_notification
                        create_notification("success", f"✅ SOS {sos['id']} resolved by {user_name}", "normal")

                        st.success(f"✅ Emergency {sos['id']} marked as resolved!")
                        st.balloons()
                        st.rerun()

                st.markdown("---")

                # Quick info
                st.markdown("#### 📊 Status")
                days_open = 0
                try:
                    sos_date = dt.datetime.fromisoformat(sos['time'][:19])
                    days_open = (dt.datetime.now() - sos_date).days
                    hours_open = (dt.datetime.now() - sos_date).total_seconds() / 3600

                    if hours_open < 24:
                        st.metric("Time Open", f"{int(hours_open)}h")
                    else:
                        st.metric("Days Open", days_open)
                except:
                    st.metric("Time Open", "N/A")


def render_vet_statistics(my_cases, prescriptions, user_name):
    """Display veterinarian performance statistics"""
    st.markdown(f"### 📊 {user_name}'s Performance Statistics")

    if not my_cases and not prescriptions:
        st.info("No activity data available yet")
        return

    # Calculate statistics
    col1, col2, col3, col4 = st.columns(4)

    total_cases = len(my_cases)
    resolved_cases = len([c for c in my_cases if c['status'] == 'resolved'])
    in_treatment_cases = len([c for c in my_cases if c['status'] == 'in_treatment'])
    total_prescriptions = len([rx for rx in prescriptions if rx.get('prescribed_by') == user_name])

    with col1:
        st.metric("Total Cases Handled", total_cases)

    with col2:
        st.metric("Successfully Resolved", resolved_cases)

    with col3:
        st.metric("Currently Treating", in_treatment_cases)

    with col4:
        st.metric("Prescriptions Issued", total_prescriptions)

    # Resolution rate
    if total_cases > 0:
        resolution_rate = (resolved_cases / total_cases) * 100
        st.markdown("---")
        st.markdown("#### 📈 Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Case Resolution Rate", f"{resolution_rate:.1f}%")

        with col2:
            avg_prescriptions = total_prescriptions / total_cases if total_cases > 0 else 0
            st.metric("Avg Prescriptions per Case", f"{avg_prescriptions:.1f}")

    # Disease distribution
    st.markdown("---")
    st.markdown("#### 🦠 Cases by Disease Type")

    disease_counts = {}
    for case in my_cases:
        disease = case.get('disease', 'Unknown')
        disease_counts[disease] = disease_counts.get(disease, 0) + 1

    if disease_counts:
        disease_df = pd.DataFrame([
            {"Disease": disease, "Cases": count, "Percentage": f"{count / total_cases * 100:.1f}%"}
            for disease, count in sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)
        ])

        st.dataframe(disease_df, use_container_width=True, hide_index=True)

    # Recent activity
    st.markdown("---")
    st.markdown("#### 🕐 Recent Activity")

    recent_cases = sorted(my_cases, key=lambda x: x.get('last_updated', x.get('time', '')), reverse=True)[:5]

    if recent_cases:
        for case in recent_cases:
            status_emoji = {"pending": "🟡", "in_treatment": "🔵", "resolved": "🟢"}
            st.markdown(
                f"{status_emoji.get(case['status'], '⚪')} **{case['id']}** - {case['disease'].title()} ({case['status'].replace('_', ' ').title()})")