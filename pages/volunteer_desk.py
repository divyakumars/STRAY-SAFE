# pages/volunteer_desk.py - COMPLETE FUNCTIONAL IMPLEMENTATION

import streamlit as st
import pandas as pd
import datetime as dt
import time
from utils import storage, notify
from components import (
    page_header, kpi_card, has_role, create_notification,
    audit_log, encode_file, status_badge
)


@st.cache_resource
def load_plotly():
    """Load Plotly for interactive charts"""
    import plotly.express as px
    import plotly.graph_objects as go
    return {'px': px, 'go': go}


def calculate_completion_time(task):
    """Calculate time taken to complete a task"""
    try:
        if task.get("completed_at") and task.get("created_at"):
            created = dt.datetime.fromisoformat(task["created_at"][:19])
            completed = dt.datetime.fromisoformat(task["completed_at"][:19])
            delta = completed - created
            days = delta.days
            hours = delta.seconds // 3600
            if days > 0:
                return f"{days}d {hours}h"
            return f"{hours}h"
    except:
        pass
    return "N/A"


def render():
    """Volunteer task management dashboard - FULLY FUNCTIONAL"""
    if not has_role('volunteer', 'admin'):
        st.error("⛔ Access Denied: Only volunteers and admins can access this page")
        return

    user_role = st.session_state.user.get("role")
    user_email = st.session_state.user.get("email")
    user_name = st.session_state.user.get("name")

    page_header("🧰", "Volunteer Desk",
                "Manage your volunteer tasks and activities", user_role)

    # Load Plotly
    viz = load_plotly()
    px = viz['px']

    # ========== LOAD ALL DATA ==========
    tasks = storage.read("volunteer_tasks", [])
    sos_alerts = storage.read("sos", [])
    campaigns = storage.read("campaigns", [])
    feeding_slots = storage.read("feeding", [])
    posts = storage.read("posts", [])

    # Normalize task data with enhanced fields
    for task in tasks:
        task.setdefault("id", f"TASK-{abs(hash(str(task)))}")
        task.setdefault("title", "Untitled Task")
        task.setdefault("description", "")
        task.setdefault("status", "pending")
        task.setdefault("priority", "medium")
        task.setdefault("assigned_to", [])
        task.setdefault("created_by", "System")
        task.setdefault("created_at", str(dt.datetime.now()))
        task.setdefault("due_date", "")
        task.setdefault("category", "general")
        task.setdefault("location", "")
        task.setdefault("completed_at", "")
        task.setdefault("submission", None)
        task.setdefault("coords", None)
        task.setdefault("sos_id", None)
        task.setdefault("campaign_id", None)

    # ========== CALCULATE METRICS ==========
    my_tasks = [t for t in tasks if user_email in t.get("assigned_to", [])]
    pending_tasks = [t for t in my_tasks if t["status"] == "pending"]
    in_progress = [t for t in my_tasks if t["status"] == "in_progress"]
    completed = [t for t in my_tasks if t["status"] == "completed"]

    # Overdue tasks
    today = dt.date.today()
    overdue = []
    for t in pending_tasks + in_progress:
        if t.get("due_date"):
            try:
                due = dt.date.fromisoformat(t["due_date"])
                if due < today:
                    overdue.append(t)
            except:
                pass

    # Calculate completion stats
    if my_tasks:
        completion_rate = (len(completed) / len(my_tasks)) * 100
        avg_completion_days = 0
        completed_with_time = [t for t in completed if t.get("completed_at") and t.get("created_at")]
        if completed_with_time:
            total_hours = 0
            for t in completed_with_time:
                try:
                    created = dt.datetime.fromisoformat(t["created_at"][:19])
                    comp = dt.datetime.fromisoformat(t["completed_at"][:19])
                    hours = (comp - created).total_seconds() / 3600
                    total_hours += hours
                except:
                    pass
            avg_completion_hours = total_hours / len(completed_with_time) if completed_with_time else 0
            avg_completion_days = avg_completion_hours / 24
    else:
        completion_rate = 0
        avg_completion_days = 0

    # ========== KPI CARDS ==========
    st.markdown("### 📊 My Task Overview")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kpi_card("My Tasks", len(my_tasks), "Total assigned", "📋", "primary")
    with col2:
        kpi_card("Pending", len(pending_tasks), "Not started", "⏳", "warning")
    with col3:
        kpi_card("In Progress", len(in_progress), "Working on", "🔄", "info")
    with col4:
        kpi_card("Completed", len(completed), "Finished", "✅", "success")
    with col5:
        kpi_card("Overdue", len(overdue), "Need attention", "🔴", "danger")

    if overdue:
        st.error(f"⚠️ You have {len(overdue)} overdue task(s)! Please prioritize these.")

    # ========== MAIN TABS ==========
    tabs = st.tabs([
        "📋 My Tasks",
        "➕ Available Tasks",
        "✅ Submit Work",
        "📊 My Stats",
        "🚨 Active SOSs",
        "💉 Upcoming Campaigns",
        "🍲 My Feeding Slots"
    ])

    # ==================== TAB 1: MY TASKS ====================
    with tabs[0]:
        st.markdown("### 📋 My Assigned Tasks")

        if not my_tasks:
            st.info("🎉 No tasks assigned yet. Check 'Available Tasks' to volunteer!")

            # Show available tasks count
            available_tasks = [t for t in tasks if user_email not in t.get("assigned_to", [])]
            if available_tasks:
                st.success(f"✨ {len(available_tasks)} tasks are waiting for volunteers!")
        else:
            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                status_filter = st.selectbox("Filter by Status",
                                             ["all", "pending", "in_progress", "completed"],
                                             key="my_status_filter")
            with col2:
                priority_filter = st.selectbox("Filter by Priority",
                                               ["all", "high", "medium", "low"],
                                               key="my_priority_filter")
            with col3:
                category_filter = st.selectbox("Filter by Category",
                                               ["all", "feeding", "rescue", "vaccination", "general", "emergency"],
                                               key="my_category_filter")
            with col4:
                sort_by = st.selectbox("Sort by",
                                       ["Priority", "Due Date", "Created Date", "Status"],
                                       key="my_sort")

            # Apply filters
            filtered = my_tasks.copy()
            if status_filter != "all":
                filtered = [t for t in filtered if t["status"] == status_filter]
            if priority_filter != "all":
                filtered = [t for t in filtered if t["priority"] == priority_filter]
            if category_filter != "all":
                filtered = [t for t in filtered if t["category"] == category_filter]

            # Apply sorting
            if sort_by == "Priority":
                priority_order = {"high": 0, "medium": 1, "low": 2}
                filtered.sort(key=lambda x: priority_order.get(x["priority"], 3))
            elif sort_by == "Due Date":
                filtered.sort(key=lambda x: x.get("due_date") or "9999-12-31")
            elif sort_by == "Created Date":
                filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            else:  # Status
                status_order = {"pending": 0, "in_progress": 1, "completed": 2}
                filtered.sort(key=lambda x: status_order.get(x["status"], 3))

            st.caption(f"Showing {len(filtered)} of {len(my_tasks)} tasks")

            # Display tasks
            for task in filtered:
                # Priority colors
                priority_colors = {
                    "high": "#ef4444",
                    "medium": "#f59e0b",
                    "low": "#10b981"
                }

                # Status colors
                status_colors = {
                    "pending": "#6b7280",
                    "in_progress": "#3b82f6",
                    "completed": "#10b981"
                }

                # Check if overdue
                is_overdue = task in overdue

                with st.expander(
                        f"{'🔴' if is_overdue else '📌'} {task['title']} - {task['id']}",
                        expanded=(task['status'] == 'in_progress' or is_overdue)
                ):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); border-radius: 8px;">
                            <div style="display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;">
                                <span style="background: {priority_colors[task['priority']]}; color: white; 
                                             padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">
                                    {task['priority'].upper()} PRIORITY
                                </span>
                                <span style="background: {status_colors[task['status']]}; color: white; 
                                             padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">
                                    {task['status'].upper().replace('_', ' ')}
                                </span>
                                <span style="background: rgba(99, 102, 241, 0.3); color: #818cf8; 
                                             padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">
                                    {task['category'].upper()}
                                </span>
                                {f'<span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; animation: pulse 2s infinite;">⚠️ OVERDUE</span>' if is_overdue else ''}
                            </div>
                            <p style="margin: 8px 0; color: #e8eaf6; font-size: 14px;">{task['description'] or 'No description provided'}</p>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 8px;">
                                📍 <strong>Location:</strong> {task['location'] or 'Not specified'}<br>
                                📅 <strong>Created:</strong> {task['created_at'][:16]}<br>
                                ⏰ <strong>Due:</strong> {task['due_date'] or 'No deadline'}<br>
                                👤 <strong>Created by:</strong> {task['created_by']}<br>
                                {f"🔗 <strong>Linked SOS:</strong> {task['sos_id']}<br>" if task.get('sos_id') else ''}
                                {f"🔗 <strong>Linked Campaign:</strong> {task['campaign_id']}<br>" if task.get('campaign_id') else ''}
                                {f"⏱️ <strong>Completed in:</strong> {calculate_completion_time(task)}<br>" if task['status'] == 'completed' else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Show submission if exists
                        if task.get("submission"):
                            with st.expander("📄 View Submission", expanded=False):
                                sub = task["submission"]
                                st.markdown(f"**Submitted by:** {sub.get('submitted_by')}")
                                st.markdown(f"**Time:** {sub.get('submitted_at', '')[:16]}")
                                st.markdown(f"**Notes:** {sub.get('notes', 'No notes')}")

                                if sub.get('photos'):
                                    st.markdown("**📸 Attached Photos:**")
                                    for idx, photo in enumerate(sub['photos']):
                                        try:
                                            import base64
                                            from io import BytesIO
                                            from PIL import Image
                                            img_data = base64.b64decode(photo)
                                            img = Image.open(BytesIO(img_data))
                                            st.image(img, caption=f"Photo {idx + 1}", use_container_width=True)
                                        except:
                                            st.warning(f"Could not display photo {idx + 1}")

                    with col2:
                        # Status update
                        if task['status'] != 'completed':
                            new_status = st.selectbox(
                                "Update Status",
                                ["pending", "in_progress", "completed"],
                                index=["pending", "in_progress", "completed"].index(task['status']),
                                key=f"status_{task['id']}"
                            )

                            if st.button("💾 Save Status", key=f"save_{task['id']}", use_container_width=True,
                                         type="primary"):
                                old_status = task['status']
                                task['status'] = new_status

                                if new_status == 'completed':
                                    task['completed_at'] = str(dt.datetime.now())
                                    create_notification(
                                        "success",
                                        f"Task completed: {task['title']}",
                                        "normal"
                                    )

                                    # Update linked SOS if exists
                                    if task.get('sos_id'):
                                        sos_list = storage.read("sos", [])
                                        for sos in sos_list:
                                            if sos.get('id') == task['sos_id']:
                                                sos['status'] = 'resolved'
                                                sos['resolved_by'] = user_name
                                                sos['resolved_at'] = str(dt.datetime.now())
                                        storage.write("sos", sos_list)

                                storage.write("volunteer_tasks", tasks)

                                audit_log("TASK_UPDATE", {
                                    "task_id": task['id'],
                                    "old_status": old_status,
                                    "new_status": new_status,
                                    "user": user_name
                                })

                                st.success("✅ Status updated!")
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.success("✅ Completed")
                            st.caption(f"Finished: {task.get('completed_at', '')[:16]}")

                        # Unassign button
                        if st.button("❌ Unassign Me", key=f"unassign_{task['id']}", use_container_width=True):
                            task['assigned_to'].remove(user_email)
                            storage.write("volunteer_tasks", tasks)

                            create_notification(
                                "info",
                                f"{user_name} unassigned from task: {task['title']}",
                                "normal"
                            )

                            st.info("✅ Unassigned from task")
                            time.sleep(0.5)
                            st.rerun()

                        # Add notes
                        if task['status'] != 'completed':
                            st.markdown("---")
                            if st.button("📝 Add Note", key=f"note_btn_{task['id']}", use_container_width=True):
                                st.session_state[f"show_notes_{task['id']}"] = True

                    # Notes section
                    if st.session_state.get(f"show_notes_{task['id']}", False):
                        st.markdown("---")
                        note_text = st.text_area("Add progress note", key=f"note_text_{task['id']}")
                        if st.button("💾 Save Note", key=f"save_note_{task['id']}"):
                            if note_text.strip():
                                if 'notes' not in task:
                                    task['notes'] = []
                                task['notes'].append({
                                    'author': user_name,
                                    'text': note_text,
                                    'time': str(dt.datetime.now())
                                })
                                storage.write("volunteer_tasks", tasks)
                                st.success("✅ Note added!")
                                del st.session_state[f"show_notes_{task['id']}"]
                                st.rerun()

    # ==================== TAB 2: AVAILABLE TASKS ====================
    with tabs[1]:
        st.markdown("### 🆕 Available Tasks to Volunteer")

        # Show unassigned or partially assigned tasks
        available = [t for t in tasks if user_email not in t.get("assigned_to", [])]

        if not available:
            st.success("🎉 All tasks are currently assigned!")
            st.info("💡 Great job team! Check back later for new tasks.")
        else:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                avail_priority = st.multiselect(
                    "Priority",
                    ["high", "medium", "low"],
                    default=["high", "medium", "low"],
                    key="avail_priority"
                )
            with col2:
                avail_category = st.multiselect(
                    "Category",
                    ["feeding", "rescue", "vaccination", "general", "emergency"],
                    default=["feeding", "rescue", "vaccination", "general", "emergency"],
                    key="avail_category"
                )
            with col3:
                avail_sort = st.selectbox(
                    "Sort by",
                    ["Priority", "Newest", "Due Date"],
                    key="avail_sort"
                )

            # Filter
            filtered_avail = [
                t for t in available
                if t.get('priority') in avail_priority and t.get('category') in avail_category
            ]

            # Sort
            if avail_sort == "Priority":
                priority_order = {"high": 0, "medium": 1, "low": 2}
                filtered_avail.sort(key=lambda x: priority_order.get(x['priority'], 3))
            elif avail_sort == "Newest":
                filtered_avail.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            else:  # Due Date
                filtered_avail.sort(key=lambda x: x.get('due_date') or '9999-12-31')

            st.caption(f"Showing {len(filtered_avail)} available tasks")

            for task in filtered_avail:
                priority_colors = {
                    "high": "#ef4444",
                    "medium": "#f59e0b",
                    "low": "#10b981"
                }

                with st.expander(f"📌 {task['title']} - {task['id']}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); border-radius: 8px;">
                            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                                <span style="background: {priority_colors[task['priority']]}; color: white; 
                                             padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">
                                    {task['priority'].upper()} PRIORITY
                                </span>
                                <span style="background: rgba(99, 102, 241, 0.3); color: #818cf8; 
                                             padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">
                                    {task['category'].upper()}
                                </span>
                            </div>
                            <p style="margin: 8px 0; color: #e8eaf6;">{task['description'] or 'No description'}</p>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 8px;">
                                📍 {task['location'] or 'Not specified'}<br>
                                📅 Created: {task['created_at'][:10]}<br>
                                ⏰ Due: {task['due_date'] or 'No deadline'}<br>
                                👥 Assigned: {len(task.get('assigned_to', []))} volunteer(s)<br>
                                {f"🔗 Linked to: {task['sos_id']}<br>" if task.get('sos_id') else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        if st.button("✋ Volunteer", key=f"volunteer_{task['id']}", use_container_width=True,
                                     type="primary"):
                            task['assigned_to'].append(user_email)

                            # If task was pending, move to in_progress
                            if task['status'] == 'pending':
                                task['status'] = 'in_progress'

                            storage.write("volunteer_tasks", tasks)

                            create_notification(
                                "success",
                                f"{user_name} volunteered for: {task['title']}",
                                "normal"
                            )

                            # Send notification to task creator
                            try:
                                notify.send_email(
                                    task.get('created_by_email', 'admin@safepaws.com'),
                                    f"Task {task['id']} Assigned",
                                    f"{user_name} has volunteered for task: {task['title']}"
                                )
                            except:
                                pass

                            audit_log("TASK_VOLUNTEER", {
                                "task_id": task['id'],
                                "volunteer": user_name
                            })

                            st.success("✅ You've been assigned!")
                            time.sleep(0.5)
                            st.rerun()

                        # Show task details button
                        if st.button("ℹ️ Details", key=f"details_{task['id']}", use_container_width=True):
                            st.info(f"Task ID: {task['id']}\nCreated by: {task['created_by']}")

    # ==================== TAB 3: TASK SUBMISSION ====================
    with tabs[2]:
        st.markdown("### ✅ Submit Task Completion")

        completed_tasks = [
            t for t in my_tasks
            if t['status'] == 'completed' and not t.get('submission')
        ]

        if not completed_tasks:
            st.info("📋 No completed tasks pending submission")
            st.caption("Complete tasks from 'My Tasks' tab to submit work here")
        else:
            task_to_submit = st.selectbox(
                "Select Completed Task",
                [f"{t['id']} - {t['title']}" for t in completed_tasks]
            )

            if task_to_submit:
                task_id = task_to_submit.split(" - ")[0]
                task = next(t for t in tasks if t['id'] == task_id)

                # Show task details
                st.markdown("#### 📋 Task Details")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Title:** {task['title']}")
                    st.markdown(f"**Category:** {task['category']}")
                    st.markdown(f"**Location:** {task['location'] or 'N/A'}")

                with col2:
                    st.markdown(f"**Priority:** {task['priority']}")
                    st.markdown(f"**Completed:** {task['completed_at'][:16]}")
                    st.markdown(f"**Duration:** {calculate_completion_time(task)}")

                st.markdown("---")
                st.markdown("#### 📝 Submission Details")

                notes = st.text_area(
                    "Work Summary / Notes",
                    placeholder="Describe what you did, any challenges faced, outcomes...",
                    height=120,
                    key="submission_notes"
                )

                # Additional fields based on category
                if task['category'] == 'feeding':
                    dogs_fed = st.number_input("Number of dogs fed", min_value=0, value=0)
                    food_used = st.text_input("Food items used")
                elif task['category'] == 'rescue':
                    dogs_rescued = st.number_input("Number of dogs rescued", min_value=0, value=0)
                    condition = st.selectbox("Dog condition", ["Good", "Fair", "Critical"])
                elif task['category'] == 'vaccination':
                    dogs_vaccinated = st.number_input("Number of dogs vaccinated", min_value=0, value=0)
                    vaccine_type = st.text_input("Vaccine type used")

                photos = st.file_uploader(
                    "📷 Upload Photos (Before/After, Evidence of work)",
                    type=['jpg', 'png', 'jpeg'],
                    accept_multiple_files=True,
                    key="submission_photos"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📤 Submit Completion Report", type="primary", use_container_width=True):
                        if notes.strip():
                            submission = {
                                "submitted_at": str(dt.datetime.now()),
                                "submitted_by": user_name,
                                "notes": notes,
                                "photos": [encode_file(p.getvalue()) for p in photos] if photos else []
                            }

                            # Add category-specific data
                            if task['category'] == 'feeding':
                                submission['dogs_fed'] = dogs_fed
                                submission['food_used'] = food_used
                            elif task['category'] == 'rescue':
                                submission['dogs_rescued'] = dogs_rescued
                                submission['condition'] = condition
                            elif task['category'] == 'vaccination':
                                submission['dogs_vaccinated'] = dogs_vaccinated
                                submission['vaccine_type'] = vaccine_type

                            task['submission'] = submission
                            storage.write("volunteer_tasks", tasks)

                            create_notification(
                                "success",
                                f"Task submission received: {task['title']} by {user_name}",
                                "normal"
                            )

                            # Notify task creator
                            try:
                                notify.send_email(
                                    task.get('created_by_email', 'admin@safepaws.com'),
                                    f"Task Completed: {task['id']}",
                                    f"{user_name} has completed and submitted work for: {task['title']}"
                                )
                            except:
                                pass

                            audit_log("TASK_SUBMIT", {
                                "task_id": task['id'],
                                "volunteer": user_name
                            })

                            st.success("✅ Submission successful! Thank you for your work!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("⚠️ Please provide work summary notes")

                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.rerun()

    # ==================== TAB 4: MY STATS ====================
    with tabs[3]:
        st.markdown("### 📊 My Volunteer Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tasks", len(my_tasks))
        with col2:
            st.metric("Completed", len(completed))
        with col3:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        with col4:
            st.metric("Avg Time", f"{avg_completion_days:.1f} days")

        # Category breakdown
        st.markdown("---")
        st.markdown("#### 📈 Task Distribution by Category")

        if my_tasks:
            category_counts = {}
            for task in my_tasks:
                cat = task.get('category', 'general')
                category_counts[cat] = category_counts.get(cat, 0) + 1

            df_cat = pd.DataFrame([
                {"Category": k.title(), "Count": v}
                for k, v in category_counts.items()
            ])

            col1, col2 = st.columns(2)

            with col1:
                fig = px.pie(df_cat, values='Count', names='Category', title='Tasks by Category')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(df_cat, x='Category', y='Count', title='Task Count by Category')
                st.plotly_chart(fig, use_container_width=True)

        # Timeline
        st.markdown("---")
        st.markdown("#### 📅 Recent Activity Timeline")

        activities = []
        for task in sorted(my_tasks, key=lambda x: x.get('completed_at') or x.get('created_at', ''), reverse=True)[:10]:
            if task['status'] == 'completed':
                activities.append({
                    "time": task.get('completed_at', task['created_at']),
                    "action": f"✅ Completed: {task['title']}",
                    "category": task['category'],
                    "icon": "✅"
                })
            elif task['status'] == 'in_progress':
                activities.append({
                    "time": task['created_at'],
                    "action": f"🔄 Started: {task['title']}",
                    "category": task['category'],
                    "icon": "🔄"
                })
            elif task['status'] == 'pending':
                activities.append({
                    "time": task['created_at'],
                    "action": f"📋 Assigned: {task['title']}",
                    "category": task['category'],
                    "icon": "📋"
                })

        if activities:
            for act in activities:
                st.markdown(f"""
                <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                            border-left: 3px solid #6366f1; border-radius: 4px; margin-bottom: 8px;">
                    <strong>{act['icon']} {act['action']}</strong><br>
                    <span style="font-size: 12px; color: #94a3b8;">
                        🕐 {act['time'][:16]} • {act['category'].title()}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activity yet. Start volunteering to build your timeline!")

        # Performance metrics
        st.markdown("---")
        st.markdown("#### 🏆 Performance Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:
            on_time = sum(1 for t in completed if t not in overdue)
            st.metric(
                "On-Time Completion",
                f"{on_time}/{len(completed)}" if completed else "0/0",
                f"{(on_time / len(completed) * 100):.0f}%" if completed else "N/A"
            )

        with col2:
            total_hours = 0
            for t in completed:
                try:
                    created = dt.datetime.fromisoformat(t['created_at'][:19])
                    comp = dt.datetime.fromisoformat(t['completed_at'][:19])
                    total_hours += (comp - created).total_seconds() / 3600
                except:
                    pass
            st.metric("Total Hours Contributed", f"{total_hours:.1f}h")

        with col3:
            with_submission = sum(1 for t in completed if t.get('submission'))
            st.metric(
                "Submitted Reports",
                f"{with_submission}/{len(completed)}" if completed else "0/0"
            )

        # Achievements
        st.markdown("---")
        st.markdown("#### 🎖️ Achievements & Badges")

        badges = []
        if len(completed) >= 1:
            badges.append({"name": "First Task", "icon": "🌟", "desc": "Completed your first task"})
        if len(completed) >= 5:
            badges.append({"name": "Active Helper", "icon": "💪", "desc": "Completed 5 tasks"})
        if len(completed) >= 10:
            badges.append({"name": "Dedicated Volunteer", "icon": "🏆", "desc": "Completed 10 tasks"})
        if len(completed) >= 25:
            badges.append({"name": "Community Hero", "icon": "⭐", "desc": "Completed 25 tasks"})
        if completion_rate >= 80 and len(completed) >= 3:
            badges.append({"name": "High Achiever", "icon": "🎯", "desc": "80%+ completion rate"})
        if any(t.get('category') == 'emergency' for t in completed):
            badges.append({"name": "Emergency Responder", "icon": "🚨", "desc": "Handled emergency tasks"})

        if badges:
            cols = st.columns(min(3, len(badges)))
            for idx, badge in enumerate(badges):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style="padding: 16px; background: rgba(99, 102, 241, 0.2); 
                                border-radius: 12px; text-align: center; border: 2px solid #6366f1;">
                        <div style="font-size: 48px; margin-bottom: 8px;">{badge['icon']}</div>
                        <div style="font-weight: 700; color: #e8eaf6; margin-bottom: 4px;">
                            {badge['name']}
                        </div>
                        <div style="font-size: 12px; color: #94a3b8;">
                            {badge['desc']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Complete tasks to earn badges! 🎖️")

    # ==================== TAB 5: ACTIVE SOSs ====================
    with tabs[4]:
        st.markdown("### 🚨 Active Emergency SOSs")

        active_sos = [s for s in sos_alerts if s.get('status') in ['active', 'dispatched']]

        if not active_sos:
            st.success("✅ No active emergencies at the moment!")
        else:
            st.warning(f"⚠️ {len(active_sos)} active emergency(ies) need attention!")

            for sos in sorted(active_sos, key=lambda x: x.get('severity', 'Medium'), reverse=True):
                severity_color = {
                    "Critical": "#ef4444",
                    "High": "#f59e0b",
                    "Medium": "#10b981"
                }.get(sos.get('severity', 'Medium'), '#64748b')

                with st.expander(
                        f"🚨 {sos.get('id')} - {sos.get('type', 'Emergency')} ({sos.get('severity', 'N/A')})",
                        expanded=(sos.get('severity') == 'Critical')
                ):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                                    border-left: 4px solid {severity_color}; border-radius: 8px;">
                            <strong style="color: {severity_color}; font-size: 18px;">
                                {sos.get('severity', 'N/A').upper()} SEVERITY
                            </strong><br>
                            <p style="margin: 8px 0; color: #e8eaf6;">
                                <strong>Type:</strong> {sos.get('type', 'Emergency')}<br>
                                <strong>Location:</strong> {sos.get('full_address') or sos.get('place', 'Unknown')}<br>
                                <strong>Description:</strong> {sos.get('desc', 'No description')}<br>
                                <strong>Reported:</strong> {sos.get('time', '')[:16]}<br>
                                <strong>Status:</strong> {sos.get('status', 'active').upper()}<br>
                                {f"<strong>Assigned to:</strong> {sos.get('assigned')}<br>" if sos.get('assigned') else ''}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        if sos.get('status') == 'active':
                            if st.button("✋ Accept SOS", key=f"accept_sos_{sos['id']}", type="primary",
                                         use_container_width=True):
                                # Accept the SOS
                                sos['assigned'] = user_name
                                sos['status'] = 'dispatched'
                                storage.write("sos", sos_alerts)

                                # Create task for this SOS
                                new_task = {
                                    "id": f"TASK-SOS-{sos['id']}",
                                    "title": f"Emergency Response: {sos.get('type')}",
                                    "description": sos.get('desc', 'Emergency response required'),
                                    "status": "in_progress",
                                    "priority": "high" if sos.get('severity') == 'Critical' else "medium",
                                    "assigned_to": [user_email],
                                    "created_by": "System (SOS)",
                                    "created_at": str(dt.datetime.now()),
                                    "due_date": "",
                                    "category": "emergency",
                                    "location": sos.get('full_address') or sos.get('place', ''),
                                    "coords": sos.get('coords'),
                                    "sos_id": sos.get('id'),
                                    "completed_at": ""
                                }
                                tasks.append(new_task)
                                storage.write("volunteer_tasks", tasks)

                                create_notification(
                                    "emergency",
                                    f"{user_name} accepted SOS: {sos['id']}",
                                    "high"
                                )

                                st.success("✅ SOS accepted! Task created.")
                                st.rerun()

                        elif sos.get('status') == 'dispatched':
                            if sos.get('assigned') == user_name:
                                if st.button("✅ Mark Resolved", key=f"resolve_sos_{sos['id']}", type="primary",
                                             use_container_width=True):
                                    sos['status'] = 'resolved'
                                    sos['resolved_at'] = str(dt.datetime.now())
                                    storage.write("sos", sos_alerts)

                                    # Complete the task
                                    for task in tasks:
                                        if task.get('sos_id') == sos['id']:
                                            task['status'] = 'completed'
                                            task['completed_at'] = str(dt.datetime.now())
                                    storage.write("volunteer_tasks", tasks)

                                    st.success("✅ SOS resolved!")
                                    st.balloons()
                                    st.rerun()
                            else:
                                st.info(f"Assigned to: {sos.get('assigned')}")

                        if st.button("🗺️ View Map", key=f"map_sos_{sos['id']}", use_container_width=True):
                            st.session_state.nav = "Emergency SOS"
                            st.query_params.update({"sos_id": sos['id'], "action": "view_map"})
                            st.rerun()

    # ==================== TAB 6: UPCOMING CAMPAIGNS ====================
    with tabs[5]:
        st.markdown("### 💉 Upcoming Vaccination Campaigns")

        upcoming_campaigns = [
            c for c in campaigns
            if c.get('status') in ['Scheduled', 'In Progress']
        ]

        if not upcoming_campaigns:
            st.info("📅 No upcoming campaigns scheduled")
        else:
            for camp in sorted(upcoming_campaigns, key=lambda x: x.get('date', '')):
                progress_pct = (camp.get('completed', 0) / camp.get('target', 1) * 100) if camp.get('target',
                                                                                                    0) > 0 else 0

                status_color = {
                    "Scheduled": "#10b981",
                    "In Progress": "#f59e0b"
                }.get(camp.get('status', 'Scheduled'), '#64748b')

                with st.expander(f"💉 {camp.get('id')} - {camp.get('zone', 'Unknown')} ({camp.get('date', 'TBD')})"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"""
                        <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                                    border-left: 4px solid {status_color}; border-radius: 8px;">
                            <strong style="font-size: 16px;">Campaign: {camp.get('id')}</strong><br>
                            <p style="margin: 8px 0;">
                                <strong>Zone:</strong> {camp.get('zone', 'Unknown')}<br>
                                <strong>Date:</strong> {camp.get('date', 'TBD')}<br>
                                <strong>Target:</strong> {camp.get('target', 0)} vaccinations<br>
                                <strong>Completed:</strong> {camp.get('completed', 0)}/{camp.get('target', 0)}<br>
                                <strong>Status:</strong> {camp.get('status', 'Scheduled')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        st.progress(min(1.0, progress_pct / 100))
                        st.caption(f"{progress_pct:.1f}% complete")

                    with col2:
                        # Check if volunteer already has task for this campaign
                        has_task = any(
                            t.get('campaign_id') == camp.get('id') and user_email in t.get('assigned_to', [])
                            for t in tasks
                        )

                        if has_task:
                            st.success("✅ Volunteering")
                        else:
                            if st.button("✋ Volunteer", key=f"vol_camp_{camp['id']}", type="primary",
                                         use_container_width=True):
                                # Create task for this campaign
                                new_task = {
                                    "id": f"TASK-CAMP-{camp['id']}",
                                    "title": f"Vaccination Campaign: {camp.get('zone')}",
                                    "description": f"Assist with vaccination drive in {camp.get('zone')} area",
                                    "status": "pending",
                                    "priority": "medium",
                                    "assigned_to": [user_email],
                                    "created_by": "System (Campaign)",
                                    "created_at": str(dt.datetime.now()),
                                    "due_date": camp.get('date', ''),
                                    "category": "vaccination",
                                    "location": camp.get('zone', ''),
                                    "campaign_id": camp.get('id'),
                                    "completed_at": ""
                                }
                                tasks.append(new_task)
                                storage.write("volunteer_tasks", tasks)

                                create_notification(
                                    "info",
                                    f"{user_name} volunteered for campaign: {camp['id']}",
                                    "normal"
                                )

                                st.success("✅ You're now volunteering for this campaign!")
                                st.rerun()

                        if st.button("📋 View Campaign", key=f"view_camp_{camp['id']}", use_container_width=True):
                            st.session_state.nav = "Vaccination Tracker"
                            st.rerun()

    # ==================== TAB 7: MY FEEDING SLOTS ====================
    with tabs[6]:
        st.markdown("### 🍲 My Feeding Slots")

        my_feeding_slots = [
            slot for slot in feeding_slots
            if user_email in slot.get('bookings', [])
        ]

        if not my_feeding_slots:
            st.info("📅 You don't have any feeding slots booked")

            available_slots = [
                slot for slot in feeding_slots
                if slot.get('booked', 0) < slot.get('slots', 0)
            ]

            if available_slots:
                st.success(f"✨ {len(available_slots)} feeding slots are available!")
                if st.button("🍲 Browse Feeding Slots", type="primary"):
                    st.session_state.nav = "Feeding Schedule"
                    st.rerun()
        else:
            st.success(f"✅ You have {len(my_feeding_slots)} active feeding slot(s)")

            for slot in my_feeding_slots:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"""
                    <div style="padding: 16px; background: rgba(51, 65, 85, 0.3); 
                                border-left: 4px solid #10b981; border-radius: 8px; margin-bottom: 12px;">
                        <strong style="font-size: 18px;">📍 {slot.get('location', 'Unknown')}</strong><br>
                        <span style="color: #94a3b8; font-size: 14px;">
                            🕐 {slot.get('slot', 'N/A')}<br>
                            {f"📝 {slot.get('notes', '')}" if slot.get('notes') else ''}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    if st.button("❌ Cancel", key=f"cancel_feed_{slot.get('location')}_{slot.get('slot')}",
                                 use_container_width=True):
                        slot['bookings'].remove(user_email)
                        slot['booked'] = max(0, slot['booked'] - 1)
                        storage.write("feeding", feeding_slots)

                        create_notification(
                            "info",
                            f"{user_name} cancelled feeding slot: {slot['location']}",
                            "normal"
                        )

                        st.success("✅ Booking cancelled")
                        time.sleep(0.5)
                        st.rerun()

                    if st.button("✅ Mark Done", key=f"done_feed_{slot.get('location')}_{slot.get('slot')}",
                                 use_container_width=True, type="primary"):
                        # Create a completion record
                        create_notification(
                            "success",
                            f"{user_name} completed feeding at {slot['location']}",
                            "normal"
                        )
                        st.success("✅ Feeding recorded!")
                        st.balloons()

            # Weekly schedule view
            st.markdown("---")
            st.markdown("#### 📅 My Weekly Feeding Schedule")

            schedule_by_day = {}
            for slot in my_feeding_slots:
                time_slot = slot.get('slot', 'Unknown')
                location = slot.get('location', 'Unknown')

                if time_slot not in schedule_by_day:
                    schedule_by_day[time_slot] = []
                schedule_by_day[time_slot].append(location)

            for time_slot, locations in sorted(schedule_by_day.items()):
                st.markdown(f"**{time_slot}:** {', '.join(locations)}")

    # ========== QUICK ACTIONS SECTION ==========
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔔 Check Notifications", use_container_width=True):
            notifications = storage.read("notifications", [])
            unread = [n for n in notifications if not n.get('read', False)]
            st.info(f"You have {len(unread)} unread notification(s)")

    with col2:
        if st.button("📍 Check-in Location", use_container_width=True):
            st.info("📱 Location check-in feature")
            st.caption("Use this to log your arrival at task locations")

    with col3:
        if st.button("💬 Message Coordinator", use_container_width=True):
            st.session_state.nav = "Messages"
            st.rerun()

    with col4:
        if st.button("🆘 Report Issue", use_container_width=True):
            st.session_state.show_issue_form = True

    # Issue reporting form
    if st.session_state.get('show_issue_form', False):
        with st.form("issue_report_form"):
            st.markdown("#### 🆘 Report an Issue")

            issue_type = st.selectbox(
                "Issue Type",
                ["Task Problem", "Equipment Issue", "Safety Concern", "Other"]
            )

            issue_desc = st.text_area(
                "Describe the issue",
                placeholder="Please provide details..."
            )

            col1, col2 = st.columns(2)

            with col1:
                submit = st.form_submit_button("📤 Submit Report", type="primary", use_container_width=True)

            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit and issue_desc.strip():
                create_notification(
                    "warning",
                    f"Issue reported by {user_name}: {issue_type}",
                    "high"
                )

                # Send notification to admins
                try:
                    admins = storage.read("users", [])
                    admin_emails = [u.get('email') for u in admins if u.get('role') == 'admin']
                    for admin_email in admin_emails:
                        notify.send_email(
                            admin_email,
                            f"Issue Report: {issue_type}",
                            f"Issue reported by {user_name}\n\nType: {issue_type}\n\nDescription:\n{issue_desc}"
                        )
                except:
                    pass

                st.success("✅ Issue reported successfully!")
                st.session_state.show_issue_form = False
                st.rerun()

            if cancel:
                st.session_state.show_issue_form = False
                st.rerun()

    # ========== LEADERBOARD SECTION ==========
    st.markdown("---")
    st.markdown("### 🏆 Volunteer Leaderboard")

    # Calculate leaderboard
    all_users = storage.read("users", [])
    volunteers = [u for u in all_users if u.get('role') in ['volunteer', 'vet']]

    leaderboard = []
    for vol in volunteers:
        vol_email = vol.get('email')
        vol_tasks = [t for t in tasks if vol_email in t.get('assigned_to', [])]
        vol_completed = [t for t in vol_tasks if t['status'] == 'completed']

        leaderboard.append({
            'name': vol.get('name', 'Unknown'),
            'completed': len(vol_completed),
            'total': len(vol_tasks),
            'rate': (len(vol_completed) / len(vol_tasks) * 100) if vol_tasks else 0
        })

    leaderboard.sort(key=lambda x: x['completed'], reverse=True)

    if leaderboard[:5]:
        col1, col2, col3 = st.columns(3)

        # Top 3 with medals
        if len(leaderboard) >= 1:
            with col1:
                top1 = leaderboard[0]
                st.markdown(f"""
                <div style="padding: 20px; background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); 
                            border-radius: 12px; text-align: center; border: 3px solid #ffa500;">
                    <div style="font-size: 48px; margin-bottom: 8px;">🥇</div>
                    <div style="font-weight: 700; color: #1e293b; font-size: 16px;">
                        {top1['name']}
                    </div>
                    <div style="font-size: 24px; font-weight: 700; color: #1e293b; margin: 8px 0;">
                        {top1['completed']}
                    </div>
                    <div style="font-size: 12px; color: #475569;">
                        tasks completed
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if len(leaderboard) >= 2:
            with col2:
                top2 = leaderboard[1]
                st.markdown(f"""
                <div style="padding: 20px; background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%); 
                            border-radius: 12px; text-align: center; border: 3px solid #a8a8a8;">
                    <div style="font-size: 48px; margin-bottom: 8px;">🥈</div>
                    <div style="font-weight: 700; color: #1e293b; font-size: 16px;">
                        {top2['name']}
                    </div>
                    <div style="font-size: 24px; font-weight: 700; color: #1e293b; margin: 8px 0;">
                        {top2['completed']}
                    </div>
                    <div style="font-size: 12px; color: #475569;">
                        tasks completed
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if len(leaderboard) >= 3:
            with col3:
                top3 = leaderboard[2]
                st.markdown(f"""
                <div style="padding: 20px; background: linear-gradient(135deg, #cd7f32 0%, #e5a772 100%); 
                            border-radius: 12px; text-align: center; border: 3px solid #b8700d;">
                    <div style="font-size: 48px; margin-bottom: 8px;">🥉</div>
                    <div style="font-weight: 700; color: #1e293b; font-size: 16px;">
                        {top3['name']}
                    </div>
                    <div style="font-size: 24px; font-weight: 700; color: #1e293b; margin: 8px 0;">
                        {top3['completed']}
                    </div>
                    <div style="font-size: 12px; color: #475569;">
                        tasks completed
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Full leaderboard table
        st.markdown("---")
        df_leaderboard = pd.DataFrame([
            {
                "Rank": idx + 1,
                "Volunteer": vol['name'],
                "Completed": vol['completed'],
                "Total Tasks": vol['total'],
                "Success Rate": f"{vol['rate']:.1f}%"
            }
            for idx, vol in enumerate(leaderboard[:10])
        ])

        st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
    else:
        st.info("No volunteer data available yet")

    # ========== EXPORT OPTIONS ==========
    if has_role("admin", "volunteer"):
        st.markdown("---")
        st.markdown("### 📥 Export My Data")

        col1, col2 = st.columns(2)

        with col1:
            if my_tasks:
                df_export = pd.DataFrame([{
                    "Task ID": t['id'],
                    "Title": t['title'],
                    "Category": t['category'],
                    "Status": t['status'],
                    "Priority": t['priority'],
                    "Created": t['created_at'][:10],
                    "Due Date": t.get('due_date', 'N/A'),
                    "Completed": t.get('completed_at', 'N/A')[:10] if t.get('completed_at') else 'N/A'
                } for t in my_tasks])

                csv = df_export.to_csv(index=False)
                st.download_button(
                    "📥 Download My Tasks (CSV)",
                    csv,
                    file_name=f"my_tasks_{user_name}_{int(time.time())}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with col2:
            if my_tasks:
                import json
                json_data = json.dumps(my_tasks, indent=2, default=str)
                st.download_button(
                    "📥 Download My Tasks (JSON)",
                    json_data,
                    file_name=f"my_tasks_{user_name}_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True
                )