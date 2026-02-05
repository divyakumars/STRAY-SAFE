# -*- coding: utf-8 -*-
# pages/message.py

import streamlit as st
import pandas as pd
import datetime as dt
import time
import uuid
from utils import storage
from components import page_header, encode_file


def decode_file(data_str):
    """Decode base64 file"""
    import base64
    if not data_str:
        return None
    return base64.b64decode(data_str)


def render():
    """WhatsApp-style messaging with profile pictures and delete options"""
    user_role = st.session_state.user.get("role")
    page_header("✉️", "Messages", "Real-time communication", user_role)

    me = st.session_state.user.get("name")
    me_email = st.session_state.user.get("email")

    convs = storage.read("conversations", [])
    msgs = storage.read("messages", [])
    users = storage.read("users", [])
    contacts = storage.read("contacts", [])

    # Get my accepted contacts
    my_contacts = [c["contact"] for c in contacts
                   if c.get("user") == me and c.get("status") == "accepted"]

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
    def role_badge(role):
        """Generate role badge HTML"""
        role_map = {
            "admin": ("🛡️", "#ef4444", "Admin"),
            "vet": ("🩺", "#8b5cf6", "Vet"),
            "volunteer": ("🤝", "#10b981", "Volunteer"),
            "user": ("👤", "#6366f1", "User")
        }
        emoji, color, label = role_map.get(role, ("👤", "#6366f1", "User"))
        return f'<span style="background: {color}22; color: {color}; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 600; border: 1px solid {color}44;">{emoji} {label}</span>'

    # Statistics
    unread_count = sum(1 for msg in msgs
                       if me in msg.get("receipts", {}) and msg["receipts"][me] == "unread")
    total_convs = len([c for c in convs if me in c.get("members", [])])

    # KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Conversations", total_convs, "💬 Active")
    with col2:
        st.metric("Unread", unread_count, "📩 Messages")
    with col3:
        st.metric("Contacts", len(my_contacts), "👥 Connected")

    st.markdown("<hr style='border: 1px solid #475569; margin: 24px 0;'>", unsafe_allow_html=True)

    # Sidebar for chats
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 💬 Conversations")

        # New chat button
        if st.button("➕ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
            st.session_state.show_new_chat = not st.session_state.get("show_new_chat", False)

        # New chat form
        if st.session_state.get("show_new_chat", False):
            st.markdown("---")
            st.markdown("#### 👤 Start New Chat")

            if my_contacts:
                selected_contact = st.selectbox(
                    "Select contact",
                    options=my_contacts,
                    key="contact_selector"
                )

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("✅ Start", use_container_width=True, key="start_chat"):
                        existing_conv = next((c for c in convs
                                              if not c.get("is_group")
                                              and set(c.get("members", [])) == {me, selected_contact}), None)

                        if existing_conv:
                            st.session_state.active_chat = existing_conv["id"]
                        else:
                            new_conv = {
                                "id": f"C-{int(time.time())}",
                                "name": f"{me} & {selected_contact}",
                                "is_group": False,
                                "members": [me, selected_contact],
                                "created_at": str(dt.datetime.now())
                            }
                            convs.append(new_conv)
                            storage.write("conversations", convs)
                            st.session_state.active_chat = new_conv["id"]

                        st.session_state.show_new_chat = False
                        st.rerun()

                with col_b:
                    if st.button("❌ Cancel", use_container_width=True, key="cancel_new_chat"):
                        st.session_state.show_new_chat = False
                        st.rerun()
            else:
                st.info("Add contacts first to start chatting!")

        st.markdown("---")

        # List conversations
        my_convs = [c for c in convs if me in c.get("members", [])]

        if my_convs:
            for conv in sorted(my_convs, key=lambda x: x.get("created_at", ""), reverse=True):
                other_members = [m for m in conv.get("members", []) if m != me]
                other_member = other_members[0] if other_members else "Unknown"

                # Get last message
                conv_msgs = [m for m in msgs if m.get("convo_id") == conv["id"]]
                last_msg = conv_msgs[-1] if conv_msgs else None
                last_text = (last_msg.get("text", "")[:30] + "...") if last_msg and last_msg.get(
                    "text") else "No messages"

                # Count unread
                unread_in_conv = sum(1 for m in conv_msgs
                                     if me in m.get("receipts", {}) and m["receipts"][me] == "unread")

                # Highlight active chat
                is_active = st.session_state.get("active_chat") == conv["id"]
                bg_color = "rgba(99, 102, 241, 0.2)" if is_active else "rgba(51, 65, 85, 0.3)"

                # Render conversation card
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 10px;
                            background: {bg_color}; border-radius: 12px; margin-bottom: 8px;
                            border: {'2px solid #6366f1' if is_active else '1px solid #475569'};
                            cursor: pointer;">
                    {render_avatar_html(other_member, 40)}
                    <div style="flex: 1;">
                        <div style="font-weight: 700; color: #e8eaf6; font-size: 14px;">
                            {other_member}
                        </div>
                        <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">
                            {last_text}
                        </div>
                    </div>
                    {f'<div style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 50%; font-size: 10px; font-weight: 700;">{unread_in_conv}</div>' if unread_in_conv > 0 else ''}
                </div>
                """, unsafe_allow_html=True)

                col_open, col_del = st.columns([3, 1])

                with col_open:
                    if st.button("💬 Open", key=f"open_conv_{conv['id']}", use_container_width=True):
                        st.session_state.active_chat = conv["id"]

                        # Mark messages as read
                        for msg in conv_msgs:
                            if me in msg.get("receipts", {}) and msg["receipts"][me] == "unread":
                                msg["receipts"][me] = "read"
                        storage.write("messages", msgs)
                        st.rerun()

                with col_del:
                    if st.button("🗑️", key=f"del_conv_{conv['id']}", help="Delete this conversation"):
                        # Delete conversation and all its messages
                        if st.session_state.get("confirm_delete_conv") == conv["id"]:
                            # Actually delete
                            convs.remove(conv)
                            storage.write("conversations", convs)

                            # Delete all messages in this conversation
                            msgs = [m for m in msgs if m.get("convo_id") != conv["id"]]
                            storage.write("messages", msgs)

                            if st.session_state.get("active_chat") == conv["id"]:
                                st.session_state.active_chat = None

                            st.session_state.confirm_delete_conv = None
                            st.success("✅ Conversation deleted!")
                            st.rerun()
                        else:
                            # Ask for confirmation
                            st.session_state.confirm_delete_conv = conv["id"]
                            st.rerun()

                # Show confirmation warning
                if st.session_state.get("confirm_delete_conv") == conv["id"]:
                    st.warning("⚠️ Click 🗑️ again to confirm deletion")
                    if st.button("❌ Cancel", key=f"cancel_del_conv_{conv['id']}"):
                        st.session_state.confirm_delete_conv = None
                        st.rerun()

        else:
            st.info("No conversations yet. Start a new chat!")

    with col2:
        # Chat window
        active_chat_id = st.session_state.get("active_chat")

        if not active_chat_id:
            st.markdown("### 👋 Welcome to Messages!")
            st.info("Select a conversation from the left or start a new chat to begin messaging.")

        else:
            conv = next((c for c in convs if c["id"] == active_chat_id), None)

            if not conv:
                st.error("❌ Conversation not found")
                st.session_state.active_chat = None
                st.rerun()

            else:
                # Get other member
                other_members = [m for m in conv.get("members", []) if m != me]
                other_member = other_members[0] if other_members else "Unknown"

                # Find other member's user info
                other_user = next((u for u in users if u.get("name") == other_member), None)
                other_role = other_user.get("role", "user") if other_user else "user"

                # Chat header with delete conversation button
                col_header, col_delete_chat = st.columns([5, 1])

                with col_header:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 12px; padding: 16px;
                                background: rgba(51, 65, 85, 0.5); border-radius: 12px;
                                border: 1px solid #475569;">
                        {render_avatar_html(other_member, 50)}
                        <div style="flex: 1;">
                            <div style="font-weight: 700; font-size: 18px; color: #e8eaf6;">
                                {other_member}
                            </div>
                            <div style="margin-top: 4px;">
                                {role_badge(other_role)}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_delete_chat:
                    if st.button("🗑️ Delete Chat", key="delete_entire_chat", help="Delete this entire conversation",
                                 type="secondary"):
                        if st.session_state.get("confirm_delete_entire_chat"):
                            # Delete conversation and all messages
                            convs = [c for c in convs if c["id"] != conv["id"]]
                            storage.write("conversations", convs)

                            msgs = [m for m in msgs if m.get("convo_id") != conv["id"]]
                            storage.write("messages", msgs)

                            st.session_state.active_chat = None
                            st.session_state.confirm_delete_entire_chat = False
                            st.success("✅ Conversation deleted!")
                            st.rerun()
                        else:
                            st.session_state.confirm_delete_entire_chat = True
                            st.rerun()

                if st.session_state.get("confirm_delete_entire_chat"):
                    st.warning("⚠️ Are you sure? This will delete the entire conversation and all messages!")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Yes, Delete", key="confirm_yes_chat", type="primary", use_container_width=True):
                            convs = [c for c in convs if c["id"] != conv["id"]]
                            storage.write("conversations", convs)

                            msgs = [m for m in msgs if m.get("convo_id") != conv["id"]]
                            storage.write("messages", msgs)

                            st.session_state.active_chat = None
                            st.session_state.confirm_delete_entire_chat = False
                            st.success("✅ Conversation deleted!")
                            st.rerun()
                    with col_no:
                        if st.button("❌ Cancel", key="confirm_no_chat", use_container_width=True):
                            st.session_state.confirm_delete_entire_chat = False
                            st.rerun()

                # Get messages for this conversation
                conv_msgs = [m for m in msgs if m.get("convo_id") == conv["id"]]
                conv_msgs.sort(key=lambda x: x.get("time", ""))

                # Messages display area
                st.markdown("---")
                st.markdown("### 💬 Messages")

                if not conv_msgs:
                    st.info("🎉 No messages yet. Start the conversation below!")

                else:
                    # Message selection mode toggle
                    col_mode, col_actions = st.columns([3, 1])

                    with col_mode:
                        selection_mode = st.toggle("🔘 Selection Mode", key="selection_mode",
                                                   help="Enable to select and delete messages")

                    with col_actions:
                        if selection_mode and st.session_state.get("msg_selection", []):
                            if st.button("🗑️ Delete", key="delete_selected_msgs", type="primary",
                                         use_container_width=True):
                                if st.session_state.get("confirm_delete_messages"):
                                    # Delete selected messages
                                    selected_ids = st.session_state.get("msg_selection", [])
                                    msgs = [m for m in msgs if m.get("id") not in selected_ids]
                                    storage.write("messages", msgs)

                                    st.session_state.msg_selection = []
                                    st.session_state.confirm_delete_messages = False
                                    st.success(f"✅ Deleted {len(selected_ids)} message(s)!")
                                    st.rerun()
                                else:
                                    st.session_state.confirm_delete_messages = True
                                    st.rerun()

                    # Confirmation for message deletion
                    if st.session_state.get("confirm_delete_messages"):
                        st.warning(f"⚠️ Delete {len(st.session_state.get('msg_selection', []))} selected message(s)?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Yes", key="confirm_yes_msgs", type="primary", use_container_width=True):
                                selected_ids = st.session_state.get("msg_selection", [])
                                msgs = [m for m in msgs if m.get("id") not in selected_ids]
                                storage.write("messages", msgs)

                                st.session_state.msg_selection = []
                                st.session_state.confirm_delete_messages = False
                                st.success(f"✅ Deleted {len(selected_ids)} message(s)!")
                                st.rerun()
                        with col_no:
                            if st.button("❌ Cancel", key="confirm_no_msgs", use_container_width=True):
                                st.session_state.confirm_delete_messages = False
                                st.rerun()

                    # Initialize message selection list
                    if "msg_selection" not in st.session_state:
                        st.session_state.msg_selection = []

                    # Display messages
                    st.markdown("---")

                    for idx, msg in enumerate(conv_msgs):
                        sender = msg.get("sender")
                        is_me = sender == me
                        align = "flex-end" if is_me else "flex-start"
                        bg_color = "#6366f1" if is_me else "#334155"
                        text_align = "right" if is_me else "left"
                        msg_id = msg.get("id")

                        # Format timestamp
                        msg_time = msg.get("time", "")
                        try:
                            msg_time_formatted = dt.datetime.fromisoformat(msg_time).strftime("%I:%M %p")
                        except:
                            msg_time_formatted = msg_time

                        # Selection checkbox (only show for my messages in selection mode)
                        if selection_mode and is_me:
                            is_selected = msg_id in st.session_state.msg_selection

                            if st.checkbox(f"Select", value=is_selected, key=f"cb_{msg_id}",
                                           label_visibility="collapsed"):
                                if msg_id not in st.session_state.msg_selection:
                                    st.session_state.msg_selection.append(msg_id)
                            else:
                                if msg_id in st.session_state.msg_selection:
                                    st.session_state.msg_selection.remove(msg_id)

                            # Highlight selected messages
                            border_style = "3px solid #ef4444" if is_selected else "none"
                        else:
                            border_style = "none"

                        # Message bubble
                        st.markdown(f"""
                        <div style="display: flex; justify-content: {align}; margin-bottom: 16px;">
                            <div style="max-width: 70%; background: {bg_color}; padding: 12px 16px;
                                        border-radius: 16px; text-align: {text_align}; border: {border_style};">
                                <div style="font-weight: 600; font-size: 12px; color: rgba(255,255,255,0.7); margin-bottom: 4px;">
                                    {sender}
                                </div>
                                <div style="color: white; font-size: 14px; word-wrap: break-word;">
                                    {msg.get('text', '')}
                                </div>
                                <div style="font-size: 10px; color: rgba(255,255,255,0.5); margin-top: 4px;">
                                    {msg_time_formatted}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Handle attachments
                        if msg.get("attachment"):
                            att = msg["attachment"]
                            att_type = att.get("type", "")
                            att_name = att.get("name", "file")

                            if att_type.startswith("image/"):
                                try:
                                    img_data = decode_file(att["data"])
                                    st.image(img_data, width=200)
                                except:
                                    st.write(f"🖼️ {att_name}")
                            else:
                                try:
                                    file_data = decode_file(att["data"])
                                    st.download_button(
                                        label=f"📎 {att_name}",
                                        data=file_data,
                                        file_name=att_name,
                                        mime=att_type or "application/octet-stream",
                                        key=f"file_{msg_id}_{att_name}"
                                    )
                                except:
                                    st.write(f"📎 {att_name}")

                st.markdown("---")

                # Message composer
                st.markdown("### ✏️ Send Message")

                with st.form("send_message_form", clear_on_submit=True):
                    message_text = st.text_area(
                        "Type your message",
                        placeholder=f"Type a message to {other_member}...",
                        height=100,
                        key="message_text_input"
                    )

                    attachment_file = st.file_uploader(
                        "Attach file (optional)",
                        type=["jpg", "jpeg", "png", "pdf", "doc", "docx"],
                        key="message_attachment"
                    )

                    send_button = st.form_submit_button("📤 Send Message", type="primary", use_container_width=True)

                    if send_button and (message_text.strip() or attachment_file):
                        new_msg = {
                            "id": f"M-{int(time.time())}-{uuid.uuid4().hex[:6]}",
                            "convo_id": conv["id"],
                            "sender": me,
                            "text": message_text.strip() if message_text else "",
                            "time": str(dt.datetime.now()),
                            "receipts": {}
                        }

                        if attachment_file:
                            new_msg["attachment"] = {
                                "name": attachment_file.name,
                                "type": attachment_file.type,
                                "data": encode_file(attachment_file.getvalue())
                            }

                        # Set receipts for other members
                        for member in other_members:
                            new_msg["receipts"][member] = "unread"

                        msgs.append(new_msg)
                        storage.write("messages", msgs)

                        # Create notification
                        from components import create_notification
                        for member in other_members:
                            create_notification("message",
                                                f"💬 New message from {me}",
                                                "normal")

                        st.success("✅ Message sent!")
                        st.rerun()

    st.markdown("<hr style='border: 1px solid #475569; margin: 24px 0;'>", unsafe_allow_html=True)

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Messages", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("👥 Go to Contacts", use_container_width=True):
            st.session_state.nav = "Contacts"
            st.rerun()

    with col3:
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.show_new_chat = True
            st.rerun()