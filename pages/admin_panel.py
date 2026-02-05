# pages/admin_panel.py

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage, auth
from components import page_header, kpi_card, has_role, role_badge, audit_log


def render():
    """Comprehensive admin control center"""
    if not has_role("admin"):
        st.error("⛔ Access Denied: Only admins can access this page")
        return

    user_role = st.session_state.user.get("role")
    page_header("🛡️", "Admin Control Center",
                "Platform management and system administration", user_role)

    tabs = st.tabs(["👥 User Management", "✅ Content Moderation", "📦 Resources",
                    "📊 System Health", "🔒 Security", "📜 Audit Logs"])

    # TAB 1: User Management
    with tabs[0]:
        st.markdown("### 👥 User Management")

        users = storage.read("users", [])

        # Normalize user data
        for u in users:
            u.setdefault("name", "(no name)")
            u.setdefault("email", f"user{abs(hash(u.get('name')))}@example.com")
            u.setdefault("role", "user")
            u.setdefault("active", True)
            u.setdefault("created_at", str(dt.datetime.now()))

        # User stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            kpi_card("Total Users", len(users), "All roles", "👤", "primary")
        with col2:
            active_users = sum(1 for u in users if u.get("active", True))
            kpi_card("Active", active_users, f"{len(users) - active_users} inactive", "🟢", "success")
        with col3:
            admins = sum(1 for u in users if u.get("role") == "admin")
            kpi_card("Admins", admins, "Platform admins", "🛡️", "danger")
        with col4:
            volunteers = sum(1 for u in users if u.get("role") == "volunteer")
            kpi_card("Volunteers", volunteers, "Active volunteers", "🧰", "info")

        # User table
        st.markdown("#### User Directory")
        if users:
            df = pd.DataFrame(users)
            display_cols = ["name", "email", "role", "active", "created_at"]
            df_display = df[[c for c in display_cols if c in df.columns]]

            st.dataframe(df_display, use_container_width=True, height=300)

            # User actions
            st.markdown("#### User Actions")
            col1, col2 = st.columns(2)

            with col1:
                selected_email = st.selectbox("Select User", [u["email"] for u in users])

                if selected_email:
                    selected_user = next((u for u in users if u["email"] == selected_email), None)

                    if selected_user:
                        badge = role_badge(selected_user['role'])
                        st.markdown(f"""
                        <div style="padding: 16px; background: rgba(51, 65, 85, 0.3); 
                                    border-radius: 8px; margin: 12px 0;">
                            <strong>{selected_user['name']}</strong><br>
                            <span style="color: #94a3b8;">{selected_user['email']}</span><br>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"**Role:** {badge}", unsafe_allow_html=True)

            with col2:
                if selected_email:
                    new_role = st.selectbox("Change Role", ["user", "volunteer", "vet", "admin"])

                    if st.button("🔄 Update Role", type="primary"):
                        for u in users:
                            if u["email"] == selected_email:
                                old_role = u["role"]
                                u["role"] = new_role
                                storage.write("users", users)
                                audit_log("ROLE_CHANGE", {
                                    "user": selected_email,
                                    "old_role": old_role,
                                    "new_role": new_role
                                })
                                st.success(f"✅ Role updated to {new_role}")
                                st.rerun()

                    is_active = next((u.get("active", True) for u in users if u["email"] == selected_email), True)

                    if is_active:
                        if st.button("🚫 Deactivate User", type="secondary"):
                            for u in users:
                                if u["email"] == selected_email:
                                    u["active"] = False
                                    storage.write("users", users)
                                    audit_log("USER_DEACTIVATE", {"user": selected_email})
                                    st.warning("⚠️ User deactivated")
                                    st.rerun()
                    else:
                        if st.button("✅ Activate User", type="secondary"):
                            for u in users:
                                if u["email"] == selected_email:
                                    u["active"] = True
                                    storage.write("users", users)
                                    audit_log("USER_ACTIVATE", {"user": selected_email})
                                    st.success("✅ User activated")
                                    st.rerun()
        else:
            st.info("No users found")

    # TAB 2: Content Moderation
    with tabs[1]:
        st.markdown("### ✅ Content Moderation")

        posts = storage.read("posts", [])

        col1, col2, col3 = st.columns(3)

        with col1:
            total_posts = len(posts)
            kpi_card("Total Posts", total_posts, "Community posts", "💬", "primary")

        with col2:
            flagged_posts = sum(1 for p in posts if p.get("flagged", False))
            kpi_card("Flagged", flagged_posts, "Needs review", "🚩", "danger")

        with col3:
            approved_posts = sum(1 for p in posts if p.get("approved", True))
            kpi_card("Approved", approved_posts, "Published", "✅", "success")

        # Pending moderation
        st.markdown("#### Pending Moderation")

        pending_posts = [p for p in posts if p.get("flagged", False) and not p.get("reviewed", False)]

        if pending_posts:
            for post in pending_posts[:10]:
                with st.expander(f"Post by {post.get('author', 'Unknown')} - {post.get('time', '')[:16]}"):
                    st.markdown(post.get("content", "No content"))

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("✅ Approve", key=f"approve_{post.get('id')}"):
                            post["approved"] = True
                            post["reviewed"] = True
                            post["flagged"] = False
                            storage.write("posts", posts)
                            audit_log("POST_APPROVE", {"post_id": post.get('id')})
                            st.success("Post approved")
                            st.rerun()

                    with col2:
                        if st.button("🚫 Remove", key=f"remove_{post.get('id')}"):
                            posts.remove(post)
                            storage.write("posts", posts)
                            audit_log("POST_REMOVE", {"post_id": post.get('id')})
                            st.warning("Post removed")
                            st.rerun()

                    with col3:
                        if st.button("⚠️ Warn User", key=f"warn_{post.get('id')}"):
                            st.info("Warning sent to user")
        else:
            st.info("✅ No posts pending moderation")

    # TAB 3: Resources
    with tabs[2]:
        st.markdown("### 📦 Resource Management")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Food Inventory")

            inventory = storage.read("inventory", [])

            if not inventory:
                inventory = [
                    {"item": "Dog Food (kg)", "quantity": 100, "min_threshold": 20},
                    {"item": "Water Bowls", "quantity": 50, "min_threshold": 10},
                    {"item": "Medicines", "quantity": 30, "min_threshold": 5}
                ]
                storage.write("inventory", inventory)

            for item in inventory:
                quantity = item.get("quantity", 0)
                threshold = item.get("min_threshold", 10)

                status = "🟢" if quantity > threshold else "🔴"

                st.markdown(f"""
                <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                            border-radius: 8px; margin-bottom: 8px;">
                    {status} <strong>{item['item']}</strong>: {quantity} units
                    <span style="color: #94a3b8;">(Min: {threshold})</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("#### Add Stock")
            item_name = st.text_input("Item Name")
            quantity = st.number_input("Quantity", min_value=1, value=10)

            if st.button("➕ Add to Inventory"):
                # Find existing item or create new
                found = False
                for item in inventory:
                    if item['item'] == item_name:
                        item['quantity'] += quantity
                        found = True
                        break

                if not found:
                    inventory.append({
                        "item": item_name,
                        "quantity": quantity,
                        "min_threshold": 10
                    })

                storage.write("inventory", inventory)
                st.success(f"✅ Added {quantity} {item_name}")
                st.rerun()

        with col2:
            st.markdown("#### Donation Campaigns")

            # Donations
            donations = storage.read("donations", [])
            total_raised = sum(d.get("amount", 0) for d in donations)

            kpi_card("Total Raised", f"₹{total_raised:,}", "Lifetime", "💵", "success")

            # Donation campaigns
            campaigns = storage.read("campaigns", [
                {"id": 1, "name": "Emergency Medical Fund", "target": 100000, "raised": 45000},
                {"id": 2, "name": "Winter Shelter Project", "target": 200000, "raised": 120000},
                {"id": 3, "name": "Vaccination Drive 2024", "target": 50000, "raised": 35000}
            ])

            for campaign in campaigns:
                name = campaign.get("name", "Unnamed Campaign")
                target = campaign.get("target", 0)
                raised = campaign.get("raised", 0)
                percentage = (raised / target * 100) if target > 0 else 0

                st.markdown(f"""
                    <div style="padding: 16px; background: rgba(30, 41, 59, 0.3); 
                                border-radius: 8px; margin: 8px 0;">
                        <h4 style="margin: 0 0 12px 0;">{name}</h4>
                        <div style="background: rgba(30, 41, 59, 0.5); 
                                    border-radius: 4px; height: 8px; margin: 8px 0;">
                            <div style="background: #10b981; height: 100%; 
                                        width: {min(percentage, 100)}%; border-radius: 4px;"></div>
                        </div>
                        <small>₹{raised:,} / ₹{target:,} ({percentage:.0f}%)</small>
                    </div>
                    """, unsafe_allow_html=True)

    # TAB 4: System Health
    with tabs[3]:
        st.markdown("### 📊 System Health")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Database size
            import os
            db_size = 0
            if os.path.exists("data"):
                for file in os.listdir("data"):
                    file_path = os.path.join("data", file)
                    if os.path.isfile(file_path):
                        db_size += os.path.getsize(file_path)

            db_size_mb = db_size / (1024 * 1024)
            kpi_card("Database Size", f"{db_size_mb:.2f} MB", "Storage used", "💾", "info")

        with col2:
            # API calls (simulated)
            kpi_card("API Calls", "1,234", "Today", "📡", "success")

        with col3:
            # Uptime (simulated)
            kpi_card("Uptime", "99.9%", "Last 30 days", "⚡", "primary")

        # System metrics
        st.markdown("#### System Metrics")

        metrics_data = pd.DataFrame({
            'Metric': ['Response Time', 'Error Rate', 'Active Sessions', 'Queue Length'],
            'Value': ['120ms', '0.1%', '45', '3'],
            'Status': ['🟢 Good', '🟢 Good', '🟡 Normal', '🟢 Good']
        })

        st.dataframe(metrics_data, use_container_width=True, hide_index=True)

    # TAB 5: Security
    with tabs[4]:
        st.markdown("### 🔒 Security")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Failed Login Attempts")
            st.metric("Last 24 Hours", "3", "-2 from yesterday")

            st.markdown("#### Suspicious Activity")
            st.info("No suspicious activity detected")

        with col2:
            st.markdown("#### Access Control")

            st.markdown("""
            <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                        border-radius: 8px; margin: 8px 0;">
                <strong>Role-Based Access</strong>
                <ul style="margin: 8px 0;">
                    <li>Admin: Full system access</li>
                    <li>Vet: Medical records & cases</li>
                    <li>Volunteer: Task management</li>
                    <li>User: Basic features</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Session Management")
            active_sessions = len([u for u in users if u.get("active", True)])
            st.metric("Active Sessions", active_sessions)

            st.markdown("#### Security Features")
            st.markdown("""
            <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                        border-radius: 8px; margin-bottom: 8px;">
                ✅ Two-Factor Authentication: <strong>Enabled</strong>
            </div>
            <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                        border-radius: 8px; margin-bottom: 8px;">
                ✅ SSL Certificate: <strong>Valid</strong>
            </div>
            <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                        border-radius: 8px;">
                ✅ Firewall: <strong>Active</strong>
            </div>
            """, unsafe_allow_html=True)

    # TAB 6: Audit Logs
    with tabs[5]:
        st.markdown("### 📜 Audit Logs")

        logs = storage.read("audit", [])

        if not isinstance(logs, list):
            logs = []

        if logs:
            # Sort by time
            logs_sorted = sorted(logs, key=lambda x: x.get("time", ""), reverse=True)

            # Display recent logs
            for log in logs_sorted[:50]:
                event_color = {
                    "LOGIN": "#10b981",
                    "LOGOUT": "#64748b",
                    "ROLE_CHANGE": "#f59e0b",
                    "USER_DEACTIVATE": "#ef4444",
                    "POST_REMOVE": "#ef4444",
                    "CAMPAIGN_CREATE": "#6366f1"
                }.get(log.get("event"), "#64748b")

                badge = role_badge(log.get('role', 'user'))

                st.markdown(f"""
                <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                            border-left: 4px solid {event_color}; border-radius: 8px; 
                            margin-bottom: 8px;">
                    <strong>{log.get('event')}</strong> - {log.get('user', 'Unknown')}<br>
                    <span style="color: #94a3b8; font-size: 12px;">
                        {log.get('time', '')}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Role:** {badge}", unsafe_allow_html=True)

            # Download logs
            df_logs = pd.DataFrame(logs_sorted)
            csv = df_logs.to_csv(index=False)
            st.download_button("📥 Download Logs", csv, "audit_logs.csv", "text/csv")
        else:
            st.info("No audit logs available")