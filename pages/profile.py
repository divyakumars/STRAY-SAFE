# pages/profile.py

import streamlit as st
import pandas as pd
import datetime as dt
from utils import storage, auth
from components import page_header, kpi_card, role_badge, encode_file, decode_file


def render():
    """User profile management"""
    user_role = st.session_state.user.get("role")
    me = st.session_state.user

    page_header("👤", "My Profile",
                "Manage your account and view your activity", user_role)

    users = storage.read("users", [])
    cases = storage.read("cases", [])
    donations = storage.read("donations", [])
    posts = storage.read("posts", [])
    sos = storage.read("sos", [])

    # Find current user in database
    current_user = next((u for u in users if u.get("email") == me.get("email")), None)

    if not current_user:
        st.error("❌ User not found in database")
        return

    # Tabs
    tabs = st.tabs(["👤 Profile Info", "📊 My Activity", "⚙️ Settings", "🔒 Security"])

    # TAB 1: Profile Info
    with tabs[0]:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📸 Profile Picture")

            # Display current profile picture
            if current_user.get("profile_picture"):
                try:
                    import base64
                    from io import BytesIO
                    from PIL import Image

                    image_data = base64.b64decode(current_user["profile_picture"])
                    image = Image.open(BytesIO(image_data))

                    st.image(image, width=200)
                except:
                    # Fallback to initials
                    st.markdown(f"""
                    <div style="width: 200px; height: 200px; border-radius: 50%; 
                                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                                display: flex; align-items: center; justify-content: center;
                                font-size: 80px; font-weight: 800; color: white; margin: 0 auto;">
                        {current_user.get('name', 'U')[0].upper()}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Default avatar with initials
                st.markdown(f"""
                <div style="width: 200px; height: 200px; border-radius: 50%; 
                            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                            display: flex; align-items: center; justify-content: center;
                            font-size: 80px; font-weight: 800; color: white; margin: 0 auto;">
                    {current_user.get('name', 'U')[0].upper()}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Upload new picture
            new_picture = st.file_uploader("Update Profile Picture",
                                           type=["jpg", "jpeg", "png"],
                                           key="profile_pic_upload")

            if new_picture:
                if st.button("💾 Save Picture", use_container_width=True):
                    current_user["profile_picture"] = encode_file(new_picture.getvalue())
                    storage.write("users", users)

                    # Update session
                    st.session_state.user["profile_picture"] = current_user["profile_picture"]

                    st.success("✅ Profile picture updated!")
                    st.rerun()

        with col2:
            st.markdown("### 📝 Personal Information")

            # Editable fields
            with st.form("profile_form"):
                name = st.text_input("Full Name", value=current_user.get("name", ""))
                email = st.text_input("Email", value=current_user.get("email", ""), disabled=True)
                phone = st.text_input("Phone", value=current_user.get("phone", ""))

                # Bio
                bio = st.text_area("Bio",
                                   value=current_user.get("bio", ""),
                                   placeholder="Tell us about yourself...",
                                   height=100)

                # Location
                location = st.text_input("Location", value=current_user.get("location", ""))

                # Social links
                st.markdown("#### 🔗 Social Links")
                col_a, col_b = st.columns(2)

                with col_a:
                    twitter = st.text_input("Twitter",
                                            value=current_user.get("social", {}).get("twitter", ""),
                                            placeholder="@username")

                with col_b:
                    linkedin = st.text_input("LinkedIn",
                                             value=current_user.get("social", {}).get("linkedin", ""),
                                             placeholder="profile-url")

                # Submit button
                submitted = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")

                if submitted:
                    # Update user data
                    current_user["name"] = name
                    current_user["phone"] = phone
                    current_user["bio"] = bio
                    current_user["location"] = location
                    current_user["social"] = {
                        "twitter": twitter,
                        "linkedin": linkedin
                    }

                    storage.write("users", users)

                    # Update session
                    st.session_state.user.update({
                        "name": name,
                        "phone": phone,
                        "bio": bio,
                        "location": location
                    })

                    st.success("✅ Profile updated successfully!")
                    st.rerun()

            # Account info (read-only)
            st.markdown("---")
            st.markdown("### ℹ️ Account Information")

            # Get role badge HTML separately to avoid escaping
            user_role_html = role_badge(current_user.get("role", "user"))

            info_data = {
                "Role": user_role_html,
                "Member Since": current_user.get("created_at", "Unknown")[:10],
                "Account Status": "🟢 Active" if current_user.get("active", True) else "🔴 Inactive",
                "Email Verified": "✅ Verified" if current_user.get("email_verified", False) else "⚠️ Not Verified"
            }

            for label, value in info_data.items():
                st.markdown(f"""
                <div style="padding: 12px; background: rgba(51, 65, 85, 0.3); 
                            border-radius: 8px; margin-bottom: 8px; 
                            display: flex; justify-content: space-between; align-items: center;">
                    <strong>{label}:</strong>
                    <span>{value}</span>
                </div>
                """, unsafe_allow_html=True)

    # TAB 2: My Activity
    with tabs[1]:
        st.markdown("### 📊 Activity Overview")

        # Calculate user's contributions
        my_cases = [c for c in cases if c.get("analyzed_by") == me.get("name")]
        my_donations = [d for d in donations if d.get("donor") == me.get("name")]
        my_posts = [p for p in posts if p.get("author_email") == me.get("email")]
        my_sos = [s for s in sos if s.get("created_by") == me.get("name")]

        # Stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            kpi_card("Cases Analyzed", len(my_cases), "AI detections", "🔬", "primary")

        with col2:
            total_donated = sum(d.get("amount", 0) for d in my_donations)
            kpi_card("Donated", f"₹{total_donated:,}", f"{len(my_donations)} times", "💰", "success")

        with col3:
            total_likes = sum(p.get("likes", 0) for p in my_posts)
            kpi_card("Posts", len(my_posts), f"{total_likes} likes", "💬", "info")

        with col4:
            kpi_card("SOS Reports", len(my_sos), "Emergencies", "🚨", "danger")

        # Recent activity timeline
        st.markdown("### 📅 Recent Activity")

        # Combine all activities
        activities = []

        for case in my_cases[-10:]:
            activities.append({
                "icon": "🔬",
                "title": "Case Analysis",
                "description": f"Analyzed case {case.get('id')} - {case.get('disease', 'Unknown')}",
                "time": case.get("time", ""),
                "type": "case"
            })

        for donation in my_donations[-10:]:
            activities.append({
                "icon": "💰",
                "title": "Donation",
                "description": f"Donated ₹{donation.get('amount', 0)} to {donation.get('campaign_name', 'General Fund')}",
                "time": donation.get("time", ""),
                "type": "donation"
            })

        for post in my_posts[-10:]:
            activities.append({
                "icon": "💬",
                "title": "Community Post",
                "description": post.get("content", "")[:80] + ("..." if len(post.get("content", "")) > 80 else ""),
                "time": post.get("time", ""),
                "type": "post"
            })

        for sos_item in my_sos[-10:]:
            activities.append({
                "icon": "🚨",
                "title": "SOS Alert",
                "description": f"Reported emergency at {sos_item.get('place', 'Unknown')}",
                "time": sos_item.get("time", ""),
                "type": "sos"
            })

        # Sort by time
        activities.sort(key=lambda x: x["time"], reverse=True)

        # Display timeline
        for activity in activities[:20]:
            st.markdown(f"""
            <div style="padding: 16px; background: rgba(51, 65, 85, 0.3); 
                        border-radius: 8px; margin-bottom: 12px; 
                        border-left: 4px solid #6366f1;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <span style="font-size: 24px;">{activity['icon']}</span>
                    <div style="flex: 1;">
                        <strong style="font-size: 16px;">{activity['title']}</strong>
                        <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">
                            {activity['description']}
                        </div>
                    </div>
                    <span style="color: #64748b; font-size: 12px; white-space: nowrap;">
                        🕐 {activity['time'][:16]}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if not activities:
            st.info("No recent activity. Start contributing to see your impact!")

        # Impact summary
        st.markdown("---")
        st.markdown("### 🌟 Your Impact")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div style="padding: 20px; background: rgba(99, 102, 241, 0.1); 
                        border-radius: 12px; border: 1px solid #6366f1; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 12px;">🏆</div>
                <h3 style="margin: 0;">Contributor</h3>
                <p style="color: #94a3b8; margin-top: 8px;">
                    Active member helping street dogs
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            contribution_score = len(my_cases) * 10 + len(my_donations) * 5 + len(my_posts) * 2
            st.markdown(f"""
            <div style="padding: 20px; background: rgba(16, 185, 129, 0.1); 
                        border-radius: 12px; border: 1px solid #10b981; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 12px;">⭐</div>
                <h3 style="margin: 0;">{contribution_score}</h3>
                <p style="color: #94a3b8; margin-top: 8px;">
                    Contribution Points
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="padding: 20px; background: rgba(245, 158, 11, 0.1); 
                        border-radius: 12px; border: 1px solid #f59e0b; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 12px;">🎖️</div>
                <h3 style="margin: 0;">Level 5</h3>
                <p style="color: #94a3b8; margin-top: 8px;">
                    Dedicated Supporter
                </p>
            </div>
            """, unsafe_allow_html=True)

    # TAB 3: Settings
    with tabs[2]:
        st.markdown("### ⚙️ Preferences")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔔 Notifications")

            email_notif = st.checkbox("Email Notifications",
                                      value=current_user.get("settings", {}).get("email_notifications", True))

            sms_notif = st.checkbox("SMS Notifications",
                                    value=current_user.get("settings", {}).get("sms_notifications", False))

            push_notif = st.checkbox("Push Notifications",
                                     value=current_user.get("settings", {}).get("push_notifications", True))

            st.markdown("#### 📧 Email Frequency")
            email_freq = st.radio("How often?",
                                  ["Real-time", "Daily Digest", "Weekly Summary", "Never"],
                                  index=0)

        with col2:
            st.markdown("#### 🎨 Preferences")

            theme = st.selectbox("Theme",
                                 ["Dark", "Light", "Auto"],
                                 index=0)

            language = st.selectbox("Language",
                                    ["English", "Hindi", "Tamil", "Telugu"],
                                    index=0)

            timezone = st.selectbox("Timezone",
                                    ["Asia/Kolkata", "UTC", "America/New_York"],
                                    index=0)

        if st.button("💾 Save Preferences", type="primary", use_container_width=True):
            current_user["settings"] = {
                "email_notifications": email_notif,
                "sms_notifications": sms_notif,
                "push_notifications": push_notif,
                "email_frequency": email_freq,
                "theme": theme,
                "language": language,
                "timezone": timezone
            }

            storage.write("users", users)
            st.success("✅ Preferences saved!")
            st.rerun()

        # Privacy settings
        st.markdown("---")
        st.markdown("### 🔒 Privacy")

        profile_visibility = st.radio("Profile Visibility",
                                      ["Public", "Friends Only", "Private"],
                                      horizontal=True)

        show_email = st.checkbox("Show email on profile", value=False)
        show_phone = st.checkbox("Show phone on profile", value=False)

        if st.button("💾 Save Privacy Settings", use_container_width=True):
            current_user["privacy"] = {
                "profile_visibility": profile_visibility,
                "show_email": show_email,
                "show_phone": show_phone
            }
            storage.write("users", users)
            st.success("✅ Privacy settings updated!")

    # TAB 4: Security
    with tabs[3]:
        st.markdown("### 🔒 Security Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔑 Change Password")

            with st.form("change_password"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")

                if st.form_submit_button("🔐 Update Password", use_container_width=True):
                    # Verify current password
                    import hashlib
                    hashed_current = hashlib.sha256(current_password.encode()).hexdigest()

                    if hashed_current != current_user.get("password"):
                        st.error("❌ Current password is incorrect")
                    elif new_password != confirm_password:
                        st.error("❌ New passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        # Update password
                        current_user["password"] = hashlib.sha256(new_password.encode()).hexdigest()
                        storage.write("users", users)
                        st.success("✅ Password updated successfully!")

        with col2:
            st.markdown("#### 🛡️ Two-Factor Authentication")

            twofa_enabled = current_user.get("twofa_enabled", False)

            if not twofa_enabled:
                st.info("🔓 Two-factor authentication is currently disabled")

                if st.button("🔐 Enable 2FA", use_container_width=True, type="primary"):
                    current_user["twofa_enabled"] = True
                    storage.write("users", users)
                    st.success("✅ 2FA enabled! Check your email for setup instructions.")
                    st.rerun()
            else:
                st.success("✅ Two-factor authentication is enabled")

                if st.button("🔓 Disable 2FA", use_container_width=True):
                    current_user["twofa_enabled"] = False
                    storage.write("users", users)
                    st.warning("⚠️ 2FA disabled")
                    st.rerun()

        # Active sessions
        st.markdown("---")
        st.markdown("### 📱 Active Sessions")

        st.markdown("""
        <div style="padding: 16px; background: rgba(51, 65, 85, 0.3); 
                    border-radius: 8px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>🖥️ Windows - Chrome</strong><br>
                    <span style="color: #94a3b8; font-size: 12px;">
                        Chennai, India • Active now
                    </span>
                </div>
                <span style="color: #10b981;">🟢 Current</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Account deletion
        st.markdown("---")
        st.markdown("### ⚠️ Danger Zone")

        with st.expander("🗑️ Delete Account"):
            st.warning("⚠️ This action is permanent and cannot be undone!")

            confirm_delete = st.text_input("Type 'DELETE' to confirm")

            if st.button("🗑️ Delete My Account", type="secondary"):
                if confirm_delete == "DELETE":
                    # Remove user
                    users.remove(current_user)
                    storage.write("users", users)

                    # Logout
                    st.session_state.user = None
                    st.error("❌ Account deleted")
                    st.rerun()
                else:
                    st.error("❌ Please type 'DELETE' to confirm")