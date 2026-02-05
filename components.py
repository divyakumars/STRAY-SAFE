# components.py - Shared UI Components

import streamlit as st
import datetime as dt
import base64
from utils import storage


# ==================== ROLE & ACCESS CONTROL ====================
def has_role(*roles):
    """Check if current user has any of the specified roles"""
    if not st.session_state.get("user"):
        return False

    user_role = st.session_state.user.get("role", "user")
    return user_role in roles


def can_access_feature(feature_name):
    """Check if user can access a specific feature"""
    if not st.session_state.get("user"):
        return False

    user_role = st.session_state.user.get("role", "user")

    # Public pages - accessible to all authenticated users
    public_pages = [
        "Dashboard",
        "AI Disease Detection",
        "Hotspot Mapping",
        "Emergency SOS",
        "Awareness Hub",
        "Community Feed",
        "Adoption Portal",
        "Donations",
        "Contacts",
        "Messages",
        "Profile"
    ]

    # Admin-only pages
    admin_pages = [
        "Admin Panel",
        "Impact Analytics"
    ]

    # Vet-only pages
    vet_pages = [
        "Vet Desk",
        "Case Management"
    ]

    # Volunteer-only pages
    volunteer_pages = [
        "Volunteer Desk",
        "Feeding Schedule"
    ]

    # Admin, vet, and volunteer shared pages
    admin_vet_volunteer_pages = [
        "Vaccination Tracker"
    ]

    if feature_name in public_pages:
        return True

    if feature_name in admin_pages:
        return user_role == "admin"

    if feature_name in vet_pages:
        return user_role in ["vet", "admin"]

    if feature_name in volunteer_pages:
        return user_role in ["volunteer", "admin"]

    if feature_name in admin_vet_volunteer_pages:
        return user_role in ["admin", "vet", "volunteer"]

    # Default: allow if logged in
    return True


def role_badge(role: str):
    """Generate styled HTML badge for user role (compatible with page_header)."""
    if not role:
        return ""

    role = role.lower().strip()

    # Define colors and icons for each role
    styles = {
        "admin": {"bg": "#dc2626", "icon": "🛠️"},
        "vet": {"bg": "#3b82f6", "icon": "🩺"},
        "volunteer": {"bg": "#10b981", "icon": "💚"},
        "user": {"bg": "#6b7280", "icon": "👤"},
    }

    style = styles.get(role, styles["user"])
    bg_color = style["bg"]
    icon = style["icon"]

    # Return clean HTML badge
    return f"""
    <div style="
        display:inline-block;
        background:{bg_color};
        color:white;
        padding:4px 12px;
        border-radius:12px;
        font-weight:600;
        font-size:14px;
        margin-top:6px;">
        {icon} {role.title()}
    </div>
    """



# ==================== UI COMPONENTS ====================
def kpi_card(title, value, subtitle="", icon="", color="primary"):
    """Render KPI card component"""
    color_schemes = {
        "primary": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
        "success": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        "warning": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
        "danger": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
        "info": "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
    }

    gradient = color_schemes.get(color, color_schemes["primary"])

    st.markdown(f"""
    <div style="background: {gradient}; padding: 24px; border-radius: 12px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.3); min-height: 140px;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <div style="font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.9); 
                        text-transform: uppercase; letter-spacing: 0.5px;">
                {title}
            </div>
            {f'<div style="font-size: 28px;">{icon}</div>' if icon else ''}
        </div>
        <div style="font-size: 36px; font-weight: 800; color: white; margin: 12px 0;">
            {value}
        </div>
        {f'<div style="font-size: 12px; color: rgba(255,255,255,0.8);">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def page_header(icon, title, subtitle="", role=None):
    """Enhanced page header with role display"""  # ensure local import works

    role_html = f'<div style="margin-top: 8px;">{role_badge(role)}</div>' if role else ''

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    padding: 32px; border-radius: 16px; margin-bottom: 32px;
                    border: 1px solid #475569;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="font-size: 48px;">{icon}</div>
                <div>
                    <h1 style="margin: 0; font-size: 36px; font-weight: 800;">{title}</h1>
                    {f'<p style="color: #94a3b8; font-size: 16px; margin: 8px 0 0 0;">{subtitle}</p>' if subtitle else ''}
                    {role_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section_header(icon, title, subtitle=""):
    """Section header component"""
    st.markdown(f"""
    <div style="margin: 24px 0 16px 0;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <span style="font-size: 32px;">{icon}</span>
            <h2 style="margin: 0; font-size: 28px; font-weight: 800;">{title}</h2>
        </div>
        {f'<p style="color: #94a3b8; font-size: 15px; margin-left: 44px;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


# ==================== FILE ENCODING ====================
def encode_file(file_bytes):
    """Encode file to base64"""
    if not file_bytes:
        return None
    return base64.b64encode(file_bytes).decode('utf-8')


def decode_file(encoded_str):
    """Decode base64 file"""
    if not encoded_str:
        return None
    return base64.b64decode(encoded_str)


# ==================== NOTIFICATIONS ====================
def create_notification(notif_type, message, priority="medium"):
    """Create system notification"""
    notif = storage.read("notifications", [])
    if not isinstance(notif, list):
        notif = []

    notif.append({
        "id": f"NOTIF-{int(dt.datetime.now().timestamp())}",
        "type": notif_type,
        "message": message,
        "time": str(dt.datetime.now()),
        "read": False,
        "priority": priority,
        "user": st.session_state.user.get("email") if st.session_state.get("user") else "system"
    })

    storage.write("notifications", notif)


# ==================== AUDIT LOGGING ====================
def audit_log(event, meta=None):
    """Enhanced audit logging"""
    logs = storage.read("audit", [])
    if not isinstance(logs, list):
        logs = []

    logs.append({
        "time": dt.datetime.now().isoformat(),
        "event": event,
        "user": (st.session_state.user or {}).get("email"),
        "role": (st.session_state.user or {}).get("role"),
        "meta": meta or {}
    })

    storage.write("audit", logs)


# ==================== SESSION STATE ====================
def init_session_state():
    """Initialize session state with stability checks"""
    ss = st.session_state

    # Core state
    if "user" not in ss:
        ss.user = None
    if "nav" not in ss:
        ss.nav = "Dashboard"
    if "search_q" not in ss:
        ss.search_q = ""
    if "show_notifications" not in ss:
        ss.show_notifications = False
    if "active_chat" not in ss:
        ss.active_chat = None
    if "theme" not in ss:
        ss.theme = "dark"
    if "map_theme" not in ss:
        ss.map_theme = "dark"

    # Offline status
    if "is_online" not in ss:
        from utils.offline import is_online
        ss.is_online = is_online()
    if "last_sync" not in ss:
        ss.last_sync = None
    if "was_offline" not in ss:
        ss.was_offline = False

    # Mobile detection
    if "is_mobile_device" not in ss:
        from utils.mobile import is_mobile
        ss.is_mobile_device = is_mobile()


# ==================== NAVIGATION ====================
def topbar():
    """Enhanced topbar with search and notifications"""
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=10000, key="auto_refresh")
    except:
        pass

    with st.container():
        col1, col2, col3 = st.columns([2, 3, 2])

        with col1:
            st.markdown("""
            <div style="padding: 16px 0;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 800; 
                           background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    🐾 RescuePaws AI
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 12px; color: #64748b; font-weight: 600;">
                    AI-Powered Street Dog Welfare Platform
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            q = st.text_input(
                "Search",
                st.session_state.search_q,
                label_visibility="collapsed",
                placeholder="🔍 Search cases, volunteers, posts, SOS..."
            )
            st.session_state.search_q = q.strip()

        with col3:
            cA, cB = st.columns([1, 1])
            with cA:
                notif = storage.read("notifications", [])
                unread = sum(1 for n in notif if not n.get("read"))
                if st.button(f"🔔 {unread}", use_container_width=True, key="notif_btn"):
                    st.session_state.show_notifications = not st.session_state.show_notifications

            with cB:
                if st.button("🚨 SOS", use_container_width=True, key="quick_sos"):
                    import time
                    sos = storage.read("sos", [])
                    sid = f"SOS-{int(time.time())}"
                    sos.append({
                        "id": sid,
                        "risk": 90,
                        "status": "active",
                        "time": str(dt.datetime.now()),
                        "place": "Quick SOS",
                        "severity": "Critical",
                        "created_by": st.session_state.user.get("name")
                    })
                    storage.write("sos", sos)
                    create_notification("emergency", f"Quick SOS: {sid}", "high")
                    st.success("🚨 SOS Activated!")
                    st.rerun()

    # Show notifications panel
    if st.session_state.show_notifications:
        notif = storage.read("notifications", [])
        with st.expander("🔔 Notifications", expanded=True):
            if notif:
                for n in sorted(notif, key=lambda x: x.get("time", ""), reverse=True)[:10]:
                    icon_map = {"emergency": "🚨", "info": "ℹ️", "success": "✅", "warning": "⚠️"}
                    icon = icon_map.get(n.get("type"), "📣")

                    st.markdown(f"""
                    <div style="padding: 10px; background: rgba(51, 65, 85, 0.3); 
                                border-radius: 8px; margin-bottom: 8px;">
                        {icon} <strong>{n.get('message', '')}</strong><br>
                        <span style="font-size: 11px; color: #94a3b8;">
                            {n.get('time', '')[:16]}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No notifications")


'''def enhanced_sidebar():
    """Enhanced sidebar with role-based navigation"""
    user = st.session_state.user

    # User profile section at top
    st.sidebar.markdown("### 👤 Profile")

    # User profile with picture
    profile_pic = user.get("profile_picture")

    if profile_pic:
        # Decode and display
        try:
            pic_bytes = decode_file(profile_pic)
            st.sidebar.image(pic_bytes, use_column_width=True)
        except:
            # Fallback to avatar
            st.sidebar.markdown(f"""
            <div style="width: 100%; text-align: center; padding: 20px;">
                <div style="width: 120px; height: 120px; border-radius: 50%; margin: 0 auto;
                            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                            display: flex; align-items: center; justify-content: center;
                            font-size: 48px; font-weight: 800; color: white;">
                    {user['name'][0].upper()}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Default avatar
        st.sidebar.markdown(f"""
        <div style="width: 100%; text-align: center; padding: 20px;">
            <div style="width: 120px; height: 120px; border-radius: 50%; margin: 0 auto;
                        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                        display: flex; align-items: center; justify-content: center;
                        font-size: 48px; font-weight: 800; color: white;">
                {user['name'][0].upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # User info card
    st.sidebar.markdown(f"""
    <div style="padding: 16px; background: rgba(51, 65, 85, 0.5); 
                border-radius: 12px; margin-bottom: 20px; text-align: center;">
        <div style="font-weight: 700; font-size: 18px; color: #e8eaf6; margin-bottom: 8px;">
            {user['name']}
        </div>
        <div style="margin-bottom: 8px;">
            {role_badge(user['role'])}
        </div>
        <div style="font-size: 11px; color: #94a3b8; word-break: break-all;">
            {user['email']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # Navigation section
    st.sidebar.markdown("### 🧭 Navigation")

    # Define pages by role
    common_pages = [
        ("Dashboard", "📊"),
        ("AI Disease Detection", "🧪"),
        ("Hotspot Mapping", "🗺️"),
        ("Emergency SOS", "🚨"),
        ("Awareness Hub", "🎓"),
        ("Community Feed", "💬"),
        ("Adoption Portal", "🐕"),
        ("Donations", "💰"),
        ("Contacts", "📞"),
        ("Messages", "✉️"),
        ("Profile", "👤")
    ]

    admin_pages = [
        ("Case Management", "📂"),
        ("Vaccination Tracker", "💉"),
        ("Feeding Schedule", "🍲"),
        ("Impact Analytics", "📈"),
        ("Admin Panel", "🛡️")
    ]

    vet_pages = [
        ("Case Management", "📂"),
        ("Vet Desk", "🩺"),
        ("Vaccination Tracker", "💉")
    ]

    volunteer_pages = [
        ("Volunteer Desk", "🧰"),
        ("Feeding Schedule", "🍲"),
        ("Vaccination Tracker", "💉")
    ]

    # Build page list
    pages = common_pages.copy()

    if has_role("admin"):
        pages.extend([p for p in admin_pages if p not in pages])

    if has_role("vet"):
        pages.extend([p for p in vet_pages if p not in pages])

    if has_role("volunteer"):
        pages.extend([p for p in volunteer_pages if p not in pages])

    # Render navigation buttons
    current_nav = st.session_state.nav

    for page_name, icon in pages:
        is_active = current_nav == page_name
        button_type = "primary" if is_active else "secondary"

        if st.sidebar.button(
                f"{icon} {page_name}",
                key=f"nav_{page_name}",
                use_container_width=True,
                type=button_type
        ):
            if can_access_feature(page_name):
                st.session_state.nav = page_name
                st.rerun()
            else:
                st.sidebar.error("⛔ Access Denied")

    st.sidebar.markdown("---")

    # Quick stats (only for admin/vet)
    if has_role("admin", "vet"):
        st.sidebar.markdown("### 📊 Quick Stats")
        sos = storage.read("sos", [])
        active_sos = sum(1 for s in sos if s.get("status") == "active")

        cases = storage.read("cases", [])
        total_cases = len(cases)

        st.sidebar.metric("Active SOS", active_sos, "🚨")
        st.sidebar.metric("Total Cases", total_cases, "📂")
        st.sidebar.markdown("---")

    # Map theme selector
    st.sidebar.markdown("### 🗺️ Map Theme")

    theme_options = {
        "dark": "🌙 Dark",
        "light": "☀️ Light",
        "satellite": "🛰️ Satellite",
        "street": "🗺️ Street"
    }

    selected_theme = st.sidebar.radio(
        "Theme",
        list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(st.session_state.map_theme),
        label_visibility="collapsed"
    )

    if selected_theme != st.session_state.map_theme:
        st.session_state.map_theme = selected_theme
        st.rerun()

    st.sidebar.markdown("---")

    # Logout button at bottom
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="primary"):
        audit_log("LOGOUT", {"email": user['email']})
        st.session_state.user = None
        st.session_state.nav = "Dashboard"
        st.rerun()
'''

def search_panel():
    """Global search panel"""
    q = st.session_state.search_q

    if not q:
        return

    st.markdown(f"### 🔍 Search Results for '{q}'")

    # Search across different data sources
    results = {
        "cases": [],
        "posts": [],
        "volunteers": [],
        "sos": []
    }

    # Search cases
    cases = storage.read("cases", [])
    for c in cases:
        if (q.lower() in c.get('id', '').lower() or
                q.lower() in c.get('disease', '').lower() or
                q.lower() in c.get('location', '').lower()):
            results["cases"].append(c)

    # Search posts
    posts = storage.read("posts", [])
    for p in posts:
        if (q.lower() in p.get('content', '').lower() or
                q.lower() in p.get('author', '').lower()):
            results["posts"].append(p)

    # Search SOS
    sos = storage.read("sos", [])
    for s in sos:
        if (q.lower() in s.get('id', '').lower() or
                q.lower() in s.get('place', '').lower()):
            results["sos"].append(s)

    # Display results
    total = sum(len(v) for v in results.values())

    if total == 0:
        st.info("No results found")
    else:
        st.success(f"Found {total} results")

        if results["cases"]:
            with st.expander(f"📂 Cases ({len(results['cases'])})"):
                for c in results["cases"][:5]:
                    st.markdown(f"**{c['id']}** - {c.get('disease', 'N/A')}")

        if results["posts"]:
            with st.expander(f"💬 Posts ({len(results['posts'])})"):
                for p in results["posts"][:5]:
                    st.markdown(f"**{p.get('author', 'N/A')}**: {p.get('content', '')[:100]}...")

        if results["sos"]:
            with st.expander(f"🚨 SOS ({len(results['sos'])})"):
                for s in results["sos"][:5]:
                    st.markdown(f"**{s['id']}** - {s.get('place', 'N/A')}")


# ==================== CSS LOADING ====================
def load_custom_css():
    """Load custom CSS styling"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }

    /* Only hide footer, keep menu and rerun button visible */
    footer {visibility: hidden;}

    /* Hide default sidebar header/nav */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Background */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(99, 102, 241, 0.3);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #475569;
        border-radius: 8px;
        color: #e8eaf6;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid #334155;
    }

    /* Clean sidebar content */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 800;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(51, 65, 85, 0.5);
        border-radius: 8px;
        color: #e8eaf6;
        font-weight: 600;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1e293b;
    }

    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }
    </style>
    """, unsafe_allow_html=True)

def enhanced_sidebar():
    """Enhanced sidebar with modern profile card, centered role badge, dynamic colors, and status dot"""
    user = st.session_state.user

    # ---- Sidebar CSS ----
    st.sidebar.markdown("""
    <style>
    .profile-card {
        position: relative;
        background: rgba(51, 65, 85, 0.45);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        transition: all 0.3s ease;
    }
    .profile-card:hover {
        background: rgba(71, 85, 105, 0.55);
        transform: scale(1.01);
    }

    /* Avatar + status positioning */
    .avatar-wrapper {
        position: relative;
        display: inline-block;
    }
    .profile-avatar, .profile-initial {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 3px solid rgba(102, 126, 234, 0.6);
        box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
        margin-bottom: 12px;
    }
    .profile-avatar {
        object-fit: cover;
    }
    .profile-initial {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        font-weight: 800;
        color: white;
        margin: 0 auto 12px auto;
    }

    /* Status dot */
    .status-dot {
        position: absolute;
        bottom: 10px;
        right: 10px;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid #1e293b;  /* border matches background */
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    .status-online {
        background: radial-gradient(circle, #10b981 30%, #34d399 70%);
        box-shadow: 0 0 10px rgba(16,185,129,0.6);
    }
    .status-offline {
        background: radial-gradient(circle, #ef4444 30%, #f87171 70%);
        box-shadow: 0 0 10px rgba(239,68,68,0.6);
    }

    .profile-name {
        font-size: 20px;
        font-weight: 700;
        color: #e8eaf6;
        margin-bottom: 6px;
        text-align: center;
    }

    .profile-role {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 12px;
        color: white;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }

    /* Role colors */
    .profile-role.user {
        background: linear-gradient(135deg, #10b981, #34d399);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }
    .profile-role.admin {
        background: linear-gradient(135deg, #f59e0b, #fbbf24);
        box-shadow: 0 0 10px rgba(251, 191, 36, 0.4);
    }
    .profile-role.vet {
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
    }
    .profile-role.volunteer {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

    # ---- Profile Section ----
    st.sidebar.markdown("### 👤 Profile")

    # Online status simulation
    is_online = True  # Later, you can toggle this from session data or backend

    profile_pic = user.get("profile_picture")
    profile_html = '<div class="profile-card"><div class="avatar-wrapper">'

    # Avatar or fallback
    if profile_pic:
        try:
            pic_bytes = decode_file(profile_pic)
            profile_html += f'<img src="data:image/png;base64,{profile_pic}" class="profile-avatar"/>'
        except Exception:
            profile_html += f'<div class="profile-initial">{user["name"][0].upper()}</div>'
    else:
        profile_html += f'<div class="profile-initial">{user["name"][0].upper()}</div>'

    # Add status dot overlay
    profile_html += f'<div class="status-dot {"status-online" if is_online else "status-offline"}"></div>'
    profile_html += '</div>'  # Close avatar-wrapper

    # Role color logic
    role_class = user['role'].lower().replace(" ", "_")

    # Add name + role
    profile_html += f"""
        <div class="profile-name">{user['name']}</div>
        <div class="profile-role {role_class}">{user['role'].upper()}</div>
    </div>
    """

    st.sidebar.markdown(profile_html, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # ---- Navigation ----
    st.sidebar.markdown("### 🧭 Navigation")

    common_pages = [
        ("Dashboard", "📊"),
        ("AI Disease Detection", "🧪"),
        ("Hotspot Mapping", "🗺️"),
        ("Emergency SOS", "🚨"),
        ("Awareness Hub", "🎓"),
        ("Community Feed", "💬"),
        ("Adoption Portal", "🐕"),
        ("Donations", "💰"),
        ("Contacts", "📞"),
        ("Messages", "✉️"),
        ("Profile", "👤")
    ]

    admin_pages = [
        ("Case Management", "📂"),
        ("Vaccination Tracker", "💉"),
        ("Feeding Schedule", "🍲"),
        ("Impact Analytics", "📈"),
        ("Admin Panel", "🛡️")
    ]

    vet_pages = [
        ("Case Management", "📂"),
        ("Vet Desk", "🩺"),
        ("Vaccination Tracker", "💉")
    ]

    volunteer_pages = [
        ("Volunteer Desk", "🧰"),
        ("Feeding Schedule", "🍲"),
        ("Vaccination Tracker", "💉")
    ]

    # Merge role pages
    pages = common_pages.copy()
    if has_role("admin"):
        pages.extend([p for p in admin_pages if p not in pages])
    if has_role("vet"):
        pages.extend([p for p in vet_pages if p not in pages])
    if has_role("volunteer"):
        pages.extend([p for p in volunteer_pages if p not in pages])

    current_nav = st.session_state.nav

    for page_name, icon in pages:
        is_active = current_nav == page_name
        button_type = "primary" if is_active else "secondary"

        if st.sidebar.button(
            f"{icon} {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type=button_type
        ):
            if can_access_feature(page_name):
                st.session_state.nav = page_name
                st.rerun()
            else:
                st.sidebar.error("⛔ Access Denied")

    st.sidebar.markdown("---")

    # ---- Quick Stats ----
    if has_role("admin", "vet"):
        st.sidebar.markdown("### 📊 Quick Stats")
        sos = storage.read("sos", [])
        active_sos = sum(1 for s in sos if s.get("status") == "active")
        cases = storage.read("cases", [])
        total_cases = len(cases)

        st.sidebar.metric("Active SOS", active_sos, "🚨")
        st.sidebar.metric("Total Cases", total_cases, "📂")
        st.sidebar.markdown("---")

    # ---- Map Theme Selector ----
    st.sidebar.markdown("### 🗺️ Map Theme")

    theme_options = {
        "dark": "🌙 Dark",
        "light": "☀️ Light",
        "satellite": "🛰️ Satellite",
        "street": "🗺️ Street"
    }

    selected_theme = st.sidebar.radio(
        "Theme",
        list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(st.session_state.map_theme),
        label_visibility="collapsed"
    )

    if selected_theme != st.session_state.map_theme:
        st.session_state.map_theme = selected_theme
        st.rerun()

    st.sidebar.markdown("---")

    # ---- Logout ----
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="primary"):
        audit_log("LOGOUT", {"email": user['email']})
        st.session_state.user = None
        st.session_state.nav = "Dashboard"
        st.rerun()


def generate_qr_code(data, filename="qr_code.png"):
    """Generate QR code"""
    import qrcode
    import io
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()

def status_badge(status):
    """Generate status badge HTML"""
    status_map = {
        "active": ("badge-active", "🟢"),
        "pending": ("badge-pending", "🟡"),
        "critical": ("badge-critical", "🔴"),
        "resolved": ("badge-active", "✅"),
        "dispatched": ("badge-pending", "🚀")
    }
    badge_class, icon = status_map.get(status.lower(), ("badge-pending", "⚪"))
    return f'<span class="status-badge {badge_class}">{icon} {status}</span>'



