# main.py - Lightweight Router with Lazy Page Loading

import streamlit as st
import importlib
from utils import storage, auth
from utils.mobile import is_mobile, mobile_friendly_css, mobile_nav_menu
from utils.offline import offline_mode_banner, is_online, sync_offline_changes
from components import (
    topbar, enhanced_sidebar, search_panel,
    can_access_feature, init_session_state, load_custom_css,
    audit_log, role_badge, encode_file
)

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="STRAY SAFE – An Intelligent Platform for Urban Street Dog Health & Safety",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== BOOTSTRAP ====================
def bootstrap():
    """Centralized initialization - runs once per session"""
    # Initialize session state
    init_session_state()

    # Load CSS
    load_custom_css()

    # Mobile CSS
    if st.session_state.get("is_mobile_device", False):
        st.markdown(mobile_friendly_css(), unsafe_allow_html=True)


# ==================== LAZY PAGE REGISTRY ====================
PAGE_REGISTRY = {
    "Dashboard": "pages.dashboard",
    "AI Disease Detection": "pages.ai_detection",
    "Hotspot Mapping": "pages.hotspot_mapping",
    "Vaccination Tracker": "pages.vaccination_tracker",
    "Emergency SOS": "pages.emergency_sos",
    "Feeding Schedule": "pages.feeding_schedule",
    "Donations": "pages.donations",
    "Impact Analytics": "pages.impact_analytics",
    "Admin Panel": "pages.admin_panel",
    "Community Feed": "pages.community_feed",
    "Messages": "pages.messages",
    "Profile": "pages.profile",
    "Adoption Portal": "pages.adoption",
    "Awareness Hub": "pages.awareness_hub",
    "Contacts": "pages.contacts",
    "Volunteer Desk": "pages.volunteer_desk",
    "Vet Desk": "pages.vet_desk",
    "Case Management": "pages.case_management"
}


def load_page(page_name):
    """Lazy load page module only when needed"""
    module_path = PAGE_REGISTRY.get(page_name)

    if not module_path:
        st.error(f"⚠️ Page '{page_name}' not found in registry")
        return None

    try:
        # Import module dynamically
        module = importlib.import_module(module_path)
        return module
    except Exception as e:
        st.error(f"❌ Failed to load page: {e}")
        return None


# ==================== LOGIN VIEW ====================
def login_view():
    """Login and registration interface"""
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="font-size: 56px; font-weight: 800; margin-bottom: 12px;
                   background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🐾 Stray Safe 
        </h1>
        <p style="font-size: 18px; color: #94a3b8; font-weight: 600;">
            AI-Powered Street Dog Welfare Platform
        </p>
        <p style="font-size: 14px; color: #64748b; margin-top: 8px;">
            Saving lives with compassion, technology, and community action
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        # LOGIN TAB
        with tab1:
            st.markdown("### 🔐 Login to Your Account")

            with st.form("login_form", clear_on_submit=True):
                email_l = st.text_input("📧 Email Address", placeholder="your.email@example.com")
                pw_l = st.text_input("🔒 Password", type="password", placeholder="Enter password")

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    login_btn = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
                with col_b:
                    demo_btn = st.form_submit_button("🎭 Demo Login", use_container_width=True)

                if login_btn:
                    if not email_l or not pw_l:
                        st.error("❌ Please enter both email and password")
                    else:
                        ok, msg, user_data = auth.login(email_l, pw_l)
                        if ok:
                            st.session_state.user = user_data
                            audit_log("LOGIN", {"email": email_l, "role": user_data.get("role")})
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

                if demo_btn:
                    # Demo login as admin
                    demo_user = {
                        "email": "admin@safepaws.ai",
                        "name": "Demo Admin",
                        "role": "admin"
                    }
                    st.session_state.user = demo_user
                    audit_log("LOGIN", {"email": demo_user['email'], "role": "admin", "type": "demo"})
                    st.success("✅ Logged in as Demo Admin")
                    st.rerun()

        # REGISTRATION TAB
        with tab2:
            st.markdown("### 📝 Create New Account")

            with st.form("register_form", clear_on_submit=True):
                name = st.text_input("👤 Full Name", placeholder="John Doe")
                email_r = st.text_input("📧 Email Address", placeholder="john.doe@example.com")
                phone = st.text_input("📱 Phone Number (Optional)", placeholder="+91 98765 43210")

                role = st.selectbox("🎭 Role", ["user", "volunteer", "vet"],
                                    help="Select your role in the platform")

                pw1 = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters")
                pw2 = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password")

                profile_pic = st.file_uploader("📷 Profile Picture (Optional)", type=['jpg', 'png', 'jpeg'])

                agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")

                register_btn = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")

                if register_btn:
                    if not all([name, email_r, pw1, pw2]):
                        st.error("❌ Please fill all required fields")
                    elif pw1 != pw2:
                        st.error("❌ Passwords don't match")
                    elif len(pw1) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    elif not agree:
                        st.error("❌ Please agree to Terms of Service")
                    else:
                        # Encode profile picture if uploaded
                        profile_pic_encoded = None
                        if profile_pic:
                            profile_pic_encoded = encode_file(profile_pic.getvalue())

                        ok, msg = auth.register(
                            email_r, name, pw1,
                            role=role,
                            phone=phone,
                            profile_picture=profile_pic_encoded
                        )

                        if ok:
                            st.success(f"✅ {msg}")
                            audit_log("REGISTER", {"email": email_r, "role": role})
                            st.info("👉 Please login with your credentials")
                        else:
                            st.error(f"❌ {msg}")

    # Feature highlights
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    features = [
        ("🧪", "AI Detection", "98.7% accuracy"),
        ("🗺️", "Hotspot Maps", "Real-time tracking"),
        ("💉", "Vaccination", "Coordinated campaigns"),
        ("🚨", "Emergency SOS", "18 min response")
    ]

    for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: rgba(51, 65, 85, 0.3);
                        border-radius: 12px; border: 1px solid #475569;">
                <div style="font-size: 36px; margin-bottom: 8px;">{icon}</div>
                <div style="font-weight: 700; margin-bottom: 4px;">{title}</div>
                <div style="font-size: 12px; color: #94a3b8;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ==================== ROUTER ====================
def router():
    """Main application router with lazy loading"""
    # Run bootstrap
    bootstrap()

    # Check authentication
    if not st.session_state.user:
        # Hide sidebar on login page
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)
        login_view()
        return

    # Offline mode banner
    is_offline = offline_mode_banner()

    # Sync when coming back online
    if not is_offline and st.session_state.get("was_offline", False):
        if not st.session_state.get("sync_attempted", False):
            sync_offline_changes()
            st.session_state.sync_attempted = True
            st.session_state.was_offline = False
    elif is_offline:
        st.session_state.was_offline = True
        st.session_state.sync_attempted = False

    # Show topbar
    topbar()

    # Navigation (mobile vs desktop)
    if st.session_state.get("is_mobile_device", False):
        mobile_nav_menu()
    else:
        enhanced_sidebar()

    # Show search panel if active
    search_panel()

    # Get current navigation
    nav = st.session_state.nav

    # Check page access
    if not can_access_feature(nav):
        st.error("⛔ Access Denied: You don't have permission to access this page")
        return

    # Lazy load and render page
    page_module = load_page(nav)

    if page_module and hasattr(page_module, 'render'):
        page_module.render()
    else:
        st.warning(f"⚠️ Page '{nav}' is under construction")
        st.info("This feature will be available soon!")


# ==================== RUN APP ====================
if __name__ == "__main__":
    router()