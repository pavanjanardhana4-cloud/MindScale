"""
MindScale AI - Authentication Module
Handles signup, login, logout, and session management.
"""

import re
import streamlit as st
import bcrypt

from database.db import init_db, get_user_by_email, create_user as db_create_user


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def create_user(email: str, password: str, confirm_password: str, short_term_goal: str = "", long_term_goal: str = "") -> tuple[bool, str]:
    """
    Create a new user account.
    Returns (success, message).
    """
    email = email.lower().strip()
    if not email:
        return False, "Please enter your email address."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    if not password:
        return False, "Please enter a password."
    if password != confirm_password:
        return False, "Passwords do not match."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    # Validate goal lengths
    if len(short_term_goal) > 200:
        return False, "Short term goal must be under 200 characters."
    if len(long_term_goal) > 200:
        return False, "Long term goal must be under 200 characters."

    password_hash = hash_password(password)
    success, message = db_create_user(email, password_hash, short_term_goal, long_term_goal)
    return success, message


def login_user(email: str, password: str) -> tuple[bool, str]:
    """
    Authenticate user and establish session.
    Returns (success, message).
    """
    email = email.lower().strip()
    if not email:
        return False, "Please enter your email address."
    if not password:
        return False, "Please enter your password."

    user = get_user_by_email(email)
    if not user:
        return False, "Invalid email or password."
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid email or password."

    # Set session state
    st.session_state.logged_in = True
    st.session_state.email = user["email"]
    st.session_state.user_id = user["id"]
    return True, f"Welcome back, {user['email']}!"


def logout_user() -> None:
    """Clear session and log out the user."""
    st.session_state.logged_in = False
    st.session_state.email = None
    st.session_state.user_id = None
    st.session_state.current_page = "Dashboard"


def init_session_state():
    """Initialize required session state variables."""
    defaults = {
        "logged_in": False,
        "email": None,
        "user_id": None,
        "current_page": "Dashboard",
        "placeholder_score": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_login():
    """Render login/signup interface."""
    init_db()

    st.markdown("<h1 class='main-header'>🛡️ MindScale AI</h1>", unsafe_allow_html=True)
    st.markdown("Welcome to MindScale AI - Your mental wellness companion.")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Demo Login"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login")

            if submitted:
                success, message = login_user(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 characters)")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            st.markdown("---")
            st.subheader("Your Goals")
            short_term_goal = st.text_area(
                "What is one goal you want to achieve in the next 3–6 months?",
                max_chars=200,
                placeholder="e.g., Learn Python for data analysis"
            )
            long_term_goal = st.text_area(
                "Where do you see yourself in the next 3–5 years?",
                max_chars=200,
                placeholder="e.g., Leading a technical team in a wellness-tech company"
            )
            
            submitted = st.form_submit_button("Sign Up")

            if submitted:
                success, message = create_user(new_email, new_password, confirm_password, short_term_goal, long_term_goal)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    with tab3:
        st.info("Click below to try the app without creating an account.")
        if st.button("Login as Demo User"):
            st.session_state.logged_in = True
            st.session_state.email = "demo@MindScale.ai"
            st.session_state.user_id = 1
            st.success("Logged in as demo user!")
            st.rerun()

