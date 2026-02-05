# utils/mobile.py - COMPLETE FILE (NEW)

"""
Mobile optimization utilities for SafePaws AI
"""

import streamlit as st


def is_mobile():
    """Detect if user is on mobile device"""
    # Check user agent (requires streamlit-js-eval)
    try:
        from streamlit_js_eval import get_user_agent
        user_agent = get_user_agent()
        if user_agent:
            mobile_keywords = ['Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone']
            return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        pass

    # Fallback: check viewport width
    try:
        from streamlit_js_eval import get_window_size
        size = get_window_size()
        if size and size.get('width', 1920) < 768:
            return True
    except:
        pass

    return False


def mobile_friendly_css():
    """Mobile-responsive CSS overrides"""
    return """
    <style>
    /* Mobile-first responsive design */
    @media only screen and (max-width: 768px) {
        /* Adjust main content padding */
        .main .block-container {
            padding: 1rem 0.5rem !important;
            max-width: 100% !important;
        }

        /* Stack columns vertically */
        .row-widget.stHorizontal {
            flex-direction: column !important;
        }

        /* Full-width buttons */
        .stButton > button {
            width: 100% !important;
            padding: 14px 20px !important;
            font-size: 16px !important;
        }

        /* Larger touch targets */
        .stCheckbox, .stRadio {
            min-height: 44px !important;
        }

        /* Responsive text */
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 18px !important; }

        /* Sidebar adjustments */
        section[data-testid="stSidebar"] {
            width: 100% !important;
            max-width: 100% !important;
        }

        /* Full-width inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }

        /* Optimize maps */
        .folium-map {
            height: 400px !important;
        }

        /* Card spacing */
        .metric-card {
            margin-bottom: 12px !important;
            padding: 16px !important;
        }

        /* Hide desktop-only elements */
        .desktop-only {
            display: none !important;
        }

        /* Touch-friendly navigation */
        .nav-pill {
            padding: 14px 20px !important;
            margin: 8px 0 !important;
            font-size: 16px !important;
        }
    }

    /* Tablet optimization (768px - 1024px) */
    @media only screen and (min-width: 768px) and (max-width: 1024px) {
        .main .block-container {
            padding: 2rem 1rem !important;
        }

        h1 { font-size: 28px !important; }
        h2 { font-size: 24px !important; }
    }
    </style>
    """


def mobile_nav_menu():
    """Bottom navigation bar for mobile"""
    user_role = st.session_state.user.get("role", "user")

    # Define mobile menu items based on role
    if user_role == "admin":
        menu_items = [
            ("🏠", "Dashboard"),
            ("🗺️", "Hotspot Mapping"),
            ("🚨", "Emergency SOS"),
            ("📊", "Impact Analytics"),
            ("⚙️", "Admin Panel")
        ]
    elif user_role == "volunteer":
        menu_items = [
            ("🏠", "Dashboard"),
            ("🧰", "Volunteer Desk"),
            ("🗺️", "Hotspot Mapping"),
            ("🚨", "Emergency SOS"),
            ("💬", "Messages")
        ]
    elif user_role == "vet":
        menu_items = [
            ("🏠", "Dashboard"),
            ("🩺", "Vet Desk"),
            ("📂", "Case Management"),
            ("💉", "Vaccination Tracker"),
            ("💬", "Messages")
        ]
    else:
        menu_items = [
            ("🏠", "Dashboard"),
            ("🧪", "AI Disease Detection"),
            ("🗺️", "Hotspot Mapping"),
            ("🐕", "Adoption Portal"),
            ("💬", "Community Feed")
        ]

    st.markdown("""
    <style>
    .mobile-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
        border-top: 1px solid #2d3748;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        z-index: 9999;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.5);
    }

    /* Add bottom padding to main content */
    @media only screen and (max-width: 768px) {
        .main {
            padding-bottom: 80px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Render bottom nav
    cols = st.columns(len(menu_items))

    for idx, (icon, page) in enumerate(menu_items):
        with cols[idx]:
            if st.button(
                    f"{icon}",
                    key=f"mobile_nav_{page}",
                    use_container_width=True,
                    type="primary" if st.session_state.nav == page else "secondary"
            ):
                st.session_state.nav = page
                st.rerun()


def optimize_map_for_mobile(map_height=400):
    """Return optimized map height for mobile"""
    if is_mobile():
        return map_height
    else:
        return 600


def mobile_upload_widget(label, file_types, key):
    """Mobile-optimized file uploader"""
    if is_mobile():
        st.markdown(f"**{label}**")
        return st.file_uploader(
            "Upload image",
            type=file_types,
            key=key,
            label_visibility="collapsed"
        )
    else:
        return st.file_uploader(label, type=file_types, key=key)