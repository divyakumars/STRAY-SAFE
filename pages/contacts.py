# pages/contact.py

import streamlit as st
import pandas as pd
import datetime as dt
import time
from utils import storage
from components import page_header, role_badge, kpi_card


def render():
    """Complete contact management with requests and connections"""
    user_role = st.session_state.user.get("role")
    page_header("👥", "Contacts",
                "Manage your connections and permissions", user_role)

    me = st.session_state.user.get("name")
    users = storage.read("users", [])
    contacts_data = storage.read("contacts", [])

    # Helper function to get user profile picture
    def get_user_picture(username):
        """Get user's profile picture or return None"""
        user = next((u for u in users if u.get("name") == username), None)
        return user.get("profile_picture") if user else None

    # Render avatar as HTML string
    def render_avatar_html(username, size=40):
        """Render profile picture or default avatar as HTML string"""
        picture = get_user_picture(username)

        if picture:
            return f'<img src="data:image/png;base64,{picture}" style="width: {size}px; height: {size}px; border-radius: 50%; object-fit: cover; border: 2px solid #475569;"/>'
        else:
            return f'<div style="width: {size}px; height: {size}px; border-radius: 50%; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; font-size: {size // 2}px; border: 2px solid #475569;">{username[0].upper() if username else "?"}</div>'

    # Role badge helper
    def role_badge_html(role):
        """Generate role badge HTML"""
        role_map = {
            "admin": ("🛡️", "#ef4444", "Admin"),
            "vet": ("🩺", "#8b5cf6", "Veterinarian"),
            "volunteer": ("🤝", "#10b981", "Volunteer"),
            "user": ("👤", "#6366f1", "User")
        }
        emoji, color, label = role_map.get(role, ("👤", "#6366f1", "User"))
        return f'<span style="background: {color}22; color: {color}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; border: 1px solid {color}44;">{emoji} {label}</span>'

    # Statistics
    my_contacts = [c["contact"] for c in contacts_data
                   if c.get("user") == me and c.get("status") == "accepted"]
    incoming_requests = [c for c in contacts_data
                         if c.get("contact") == me and c.get("status") == "pending"]
    outgoing_requests = [c for c in contacts_data
                         if c.get("user") == me and c.get("status") == "pending"]
    blocks = storage.read("blocks", [])
    my_blocks = [b["blocked"] for b in blocks if b.get("user") == me]

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("My Contacts", len(my_contacts), "✅ Accepted")
    with col2:
        st.metric("Incoming", len(incoming_requests), "📥 Requests")
    with col3:
        st.metric("Outgoing", len(outgoing_requests), "📤 Pending")
    with col4:
        st.metric("Blocked", len(my_blocks), "🚫 Users")

    st.markdown("<hr style='border: 1px solid #475569; margin: 24px 0;'>", unsafe_allow_html=True)

    tabs = st.tabs(["👥 My Contacts", "📥 Requests", "🔍 Find People", "🚫 Blocked"])

    # TAB 1: My Contacts
    with tabs[0]:
        st.markdown("### ✅ Accepted Contacts")

        if my_contacts:
            for contact in my_contacts:
                # Find user
                user = next((u for u in users if u.get("name") == contact), None)
                role = user.get("role", "user") if user else "user"

                # Render contact card
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px; 
                            background: rgba(51, 65, 85, 0.3); border-radius: 12px; margin-bottom: 12px;">
                    {render_avatar_html(contact, 48)}
                    <div style="flex: 1;">
                        <div style="font-weight: 700; font-size: 16px; color: #e8eaf6;">
                            {contact}
                        </div>
                        <div style="margin-top: 4px;">
                            {role_badge_html(role)}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons
                col_msg, col_remove = st.columns([3, 1])

                with col_msg:
                    if st.button(f"💬 Message {contact}", key=f"msg_{contact}", use_container_width=True):
                        convs = storage.read("conversations", [])

                        existing_conv = next((c for c in convs
                                              if not c.get("is_group")
                                              and set(c.get("members", [])) == {me, contact}), None)

                        if not existing_conv:
                            new_conv = {
                                "id": f"C-{int(time.time())}",
                                "name": f"{me} & {contact}",
                                "is_group": False,
                                "members": [me, contact],
                                "created_at": str(dt.datetime.now())
                            }
                            convs.append(new_conv)
                            storage.write("conversations", convs)
                            st.session_state.active_chat = new_conv["id"]
                        else:
                            st.session_state.active_chat = existing_conv["id"]

                        st.session_state.nav = "Messages"
                        st.rerun()

                with col_remove:
                    if st.button("❌", key=f"remove_{contact}", help=f"Remove {contact}"):
                        contacts_data = [c for c in contacts_data
                                         if not ((c.get("user") == me and c.get("contact") == contact) or
                                                 (c.get("user") == contact and c.get("contact") == me))]
                        storage.write("contacts", contacts_data)
                        st.success(f"✅ {contact} removed!")
                        st.rerun()

        else:
            st.info("No contacts yet. Send requests to connect!")

    # TAB 2: Requests
    with tabs[1]:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📥 Incoming Requests")

            if incoming_requests:
                for req in incoming_requests:
                    # Render request card
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
                                padding: 12px; background: rgba(51, 65, 85, 0.3); border-radius: 12px;">
                        {render_avatar_html(req['user'], 40)}
                        <div style="flex: 1;">
                            <strong style="color: #e8eaf6;">{req['user']}</strong>
                            <div style="font-size: 12px; color: #94a3b8;">wants to connect</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Accept", key=f"acc_{req['user']}", use_container_width=True):
                            req["status"] = "accepted"

                            # Add reciprocal contact entry
                            if not any(c.get("user") == me and c.get("contact") == req['user']
                                       for c in contacts_data):
                                contacts_data.append({
                                    "user": me,
                                    "contact": req['user'],
                                    "status": "accepted",
                                    "created_at": str(dt.datetime.now())
                                })

                            storage.write("contacts", contacts_data)

                            # Create notification
                            from components import create_notification
                            create_notification("success",
                                                f"{me} accepted your contact request!",
                                                "normal")

                            st.success(f"✅ {req['user']} added to contacts!")
                            st.rerun()

                    with col_b:
                        if st.button("❌ Reject", key=f"rej_{req['user']}", use_container_width=True):
                            req["status"] = "rejected"
                            storage.write("contacts", contacts_data)
                            st.rerun()
            else:
                st.info("No incoming requests")

        with col2:
            st.markdown("### 📤 Outgoing Requests")

            if outgoing_requests:
                for req in outgoing_requests:
                    # Render outgoing request card
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
                                padding: 12px; background: rgba(51, 65, 85, 0.3); border-radius: 12px;">
                        {render_avatar_html(req['contact'], 40)}
                        <div style="flex: 1;">
                            <strong style="color: #e8eaf6;">{req['contact']}</strong>
                            <div style="font-size: 12px; color: #f59e0b;">Pending...</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"❌ Cancel request to {req['contact']}", key=f"cancel_{req['contact']}",
                                 use_container_width=True):
                        contacts_data.remove(req)
                        storage.write("contacts", contacts_data)
                        st.rerun()
            else:
                st.info("No outgoing requests")

    # TAB 3: Find People
    with tabs[2]:
        st.markdown("### 🔍 Find People")

        search = st.text_input("Search by name or email", key="contact_search",
                               placeholder="Enter name or email...")

        if search:
            results = [u for u in users
                       if search.lower() in u.get("name", "").lower()
                       or search.lower() in u.get("email", "").lower()]

            if results:
                st.markdown(f"**Found {len(results)} user(s)**")

                for user in results[:10]:
                    if user.get("name") != me:
                        # Render user search result
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 12px; padding: 12px;
                                    background: rgba(51, 65, 85, 0.3); border-radius: 12px; margin-bottom: 12px;">
                            {render_avatar_html(user.get('name', ''), 48)}
                            <div style="flex: 1;">
                                <div style="font-weight: 700; font-size: 16px; color: #e8eaf6;">
                                    {user['name']}
                                </div>
                                <div style="margin-top: 4px;">
                                    {role_badge_html(user.get('role', 'user'))}
                                </div>
                                <div style="font-size: 12px; color: #64748b; margin-top: 2px;">
                                    {user.get('email', '')}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Check if already sent
                        already_sent = any(c.get("user") == me and c.get("contact") == user["name"]
                                           for c in contacts_data)

                        if not already_sent:
                            if st.button(f"➕ Connect with {user['name']}", key=f"connect_{user['name']}",
                                         use_container_width=True):
                                contacts_data.append({
                                    "user": me,
                                    "contact": user["name"],
                                    "status": "pending",
                                    "created_at": str(dt.datetime.now())
                                })
                                storage.write("contacts", contacts_data)

                                # Create notification for the recipient
                                from components import create_notification
                                create_notification("info",
                                                    f"{me} sent you a contact request!",
                                                    "normal")

                                st.success(f"✅ Request sent to {user['name']}!")
                                st.rerun()
                        else:
                            st.info("⏳ Request already sent")
            else:
                st.warning("🔍 No users found")
        else:
            st.info("💡 Start typing to search for people")

    # TAB 4: Blocked Users
    with tabs[3]:
        st.markdown("### 🚫 Blocked Users")

        if my_blocks:
            for blocked in my_blocks:
                # Render blocked user card
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px;
                            background: rgba(239, 68, 68, 0.1); border-radius: 12px;
                            border: 1px solid #ef4444; margin-bottom: 12px;">
                    {render_avatar_html(blocked, 40)}
                    <div style="flex: 1;">
                        <strong style="color: #ef4444;">{blocked}</strong>
                        <div style="font-size: 12px; color: #94a3b8;">Blocked user</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🔓 Unblock {blocked}", key=f"unblock_{blocked}", use_container_width=True):
                    blocks = [b for b in blocks if not (b.get("user") == me and b.get("blocked") == blocked)]
                    storage.write("blocks", blocks)
                    st.success(f"✅ {blocked} unblocked!")
                    st.rerun()
        else:
            st.info("No blocked users")

    st.markdown("<hr style='border: 1px solid #475569; margin: 24px 0;'>", unsafe_allow_html=True)

    # Quick Actions Section
    st.markdown("### ⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresh Contacts", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("💬 Go to Messages", use_container_width=True):
            st.session_state.nav = "Messages"
            st.rerun()