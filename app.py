"""
MindScale AI - Main Application Entry Point
A modular Streamlit application for mental wellness.
"""

import streamlit as st

from auth.auth import init_session_state, render_login, logout_user
from pages import (
    dashboard,
    questionnaire,
    nlp_analysis,
    voice_analysis,
    chatbot,
    nearby_clinics,
    goal_tracker,
)

# Page configuration
st.set_page_config(
    page_title="MindScale AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern dark UI (applied globally)
st.markdown(
    """
    <style>
    /* Overall app background */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050816 !important;
        color: #e5e7eb !important;
    }

    /* Main content area card effect */
    [data-testid="stAppViewContainer"] > .main {
        padding: 1.5rem 2rem;
    }
    [data-testid="stVerticalBlock"] {
        background: radial-gradient(circle at top left, #1f2933 0, #020617 55%);
        border-radius: 18px;
        padding: 1.5rem 1.75rem;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.72);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #020617 !important;
        border-right: 1px solid rgba(148, 163, 184, 0.25);
    }
    [data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }
    [data-testid="stSidebar"] h2 {
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    /* Header style helper */
    .main-header {
        font-size: 2rem;
        font-weight: 650;
        color: #e5e7eb;
        margin-bottom: 0.75rem;
    }

    /* Buttons: clean, modern */
    .stButton > button,
    div[data-testid="baseButton-secondary"] > button {
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.4);
        color: #e5e7eb;
        background: linear-gradient(135deg, #111827, #1f2937);
        padding: 0.45rem 1.3rem;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.6);
        transition: all 0.18s ease-out;
    }
    .stButton > button:hover,
    div[data-testid="baseButton-secondary"] > button:hover {
        border-color: #38bdf8;
        box-shadow: 0 12px 28px rgba(56, 189, 248, 0.4);
        transform: translateY(-1px);
        background: linear-gradient(135deg, #0f172a, #020617);
    }

    /* Inputs / text areas */
    textarea, input, select {
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 10px !important;
        border: 1px solid rgba(148, 163, 184, 0.4) !important;
    }
    textarea:focus, input:focus, select:focus {
        outline: none !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 1px #38bdf8 !important;
    }

    /* Metrics as subtle cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.4));
        padding: 0.9rem 1rem;
        border-radius: 14px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.8);
    }
    [data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="stMetric"] div {
        color: #e5e7eb !important;
    }

    /* Info / warning / error boxes */
    .stAlert {
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        background: rgba(15, 23, 42, 0.85);
    }

    /* Chat bubbles */
    [data-testid="stChatMessage"]:has(> div[data-testid="stChatMessageContent-user"]) {
        background: linear-gradient(135deg, #0f172a, #020617);
        border-radius: 18px;
    }
    [data-testid="stChatMessage"]:has(> div[data-testid="stChatMessageContent-assistant"]) {
        background: linear-gradient(135deg, #1d2636, #020617);
        border-radius: 18px;
    }

    /* Remove default top padding */
    .stSidebar > div:first-child {
        padding-top: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Google Fit OAuth callback removed (Feature deprecated)


def render_sidebar():
    """Render navigation sidebar with page selection."""
    st.sidebar.markdown("## 🛡️ MindScale AI")
    st.sidebar.markdown("---")

    # Define pages for navigation
    pages = {
        "Dashboard": dashboard,
        "Questionnaire": questionnaire,
        "NLP Analysis": nlp_analysis,
        "Voice Analysis": voice_analysis,
        "Nearby Clinics": nearby_clinics,
        "Chatbot": chatbot,
        "Goal Tracker": goal_tracker,
    }

    # Store page names for session state
    page_names = list(pages.keys())

    # Initialize selected page in session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Sidebar navigation
    selected = st.sidebar.radio(
        "Navigate",
        page_names,
        index=page_names.index(st.session_state.current_page),
        label_visibility="collapsed"
    )

    st.session_state.current_page = selected
    st.sidebar.markdown("---")

    # User info in sidebar (if logged in)
    if st.session_state.get("logged_in", False):
        st.sidebar.success(f"👤 {st.session_state.get('email', 'User')}")
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()

    return pages[selected]


def main():
    """Main application logic."""
    # Initialize session state
    init_session_state()

    # Google Fit callback removed

    # Show login if not authenticated
    if not st.session_state.get("logged_in", False):
        render_login()
        return

    # Render sidebar and get selected page module
    page_module = render_sidebar()

    # --- Daily Goal Check-In Trigger ---
    from utils.goal_service import check_daily_recorded
    from pages.goal_tracker import render_daily_checkin
    
    user_id = st.session_state.get("user_id")
    if user_id and not st.session_state.get("daily_checkin_completed", False):
        if not check_daily_recorded(user_id):
            render_daily_checkin()
            st.sidebar.warning("⏰ Daily Goal Check-In Pending")
            return # Stop here to show the check-in
        else:
            st.session_state.daily_checkin_completed = True

    # Render the selected page
    page_module.render()


if __name__ == "__main__":
    main()

