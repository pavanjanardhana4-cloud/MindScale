"""
MindScale AI - Goal Tracker & Daily Check-In
UI for tracking user goals and performing daily check-ins.
"""

import streamlit as st
from utils.goal_service import check_daily_recorded, save_daily_goal, get_goal_metrics

def render_daily_checkin():
    """Renders the daily check-in UI."""
    st.markdown("## 🎯 Daily Goal Check-In")
    st.markdown("Taking less than 10 seconds to stay focused on your vision.")
    st.markdown("---")
    
    with st.form("daily_checkin_form"):
        # 1. Action
        goal_action = st.radio(
            "1️⃣ Did you work on your goal today?",
            options=["Yes", "Partially", "No"],
            horizontal=True
        )
        
        # 2. Activity
        goal_activity = st.text_input(
            "2️⃣ What did you do today related to your goal?",
            max_chars=150,
            placeholder="e.g., Practiced coding for 1 hour"
        )
        
        # 3. Effort
        effort_score = st.slider(
            "3️⃣ How much effort did you put toward your goal today?",
            min_value=1,
            max_value=10,
            value=5
        )
        
        submitted = st.form_submit_button("Submit Check-In")
        
        if submitted:
            if not goal_activity and goal_action != "No":
                st.warning("Please share a brief activity description.")
            else:
                user_id = st.session_state.user_id
                success = save_daily_goal(
                    user_id, 
                    goal_action.lower(), 
                    goal_activity, 
                    effort_score
                )
                if success:
                    # Trigger MCI Update
                    from utils.scoring_service import calculate_and_save_mci
                    calculate_and_save_mci(user_id)
                    
                    st.success("✨ Check-in complete! Let's make today great.")
                    st.session_state.daily_checkin_completed = True
                    st.rerun()
                else:
                    st.error("Failed to save your check-in. Please try again.")

def render():
    """Renders the independent Goal Tracker page (optional expansion)."""
    st.markdown("# 🚀 Goal Tracker")
    st.markdown("Manage and visualize your personal growth journey.")
    st.markdown("---")
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to track your goals.")
        return
        
    metrics = get_goal_metrics(user_id)
    
    if not metrics:
        st.info("Start your first daily check-in to see your metrics here!")
        render_daily_checkin()
        return

    # Check if check-in is needed today
    if not check_daily_recorded(user_id):
        st.warning("You haven't completed your check-in for today!")
        render_daily_checkin()
    else:
        st.success("✅ Today's goal check-in is complete.")
        
    st.markdown("---")
    st.subheader("Current Focus")
    
    # We'll need a way to fetch the user's goals from the users table
    from database.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT short_term_goal, long_term_goal FROM users WHERE id = ?", (user_id,))
    user_goals = cursor.fetchone()
    conn.close()
    
    if user_goals:
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**Short-term Goal (3-6m):**\n{user_goals['short_term_goal']}")
        with c2:
            st.success(f"**Long-term Goal (3-5y):**\n{user_goals['long_term_goal']}")
            
    # Metrics
    m1, m2 = st.columns(2)
    m1.metric("Goal Consistency", f"{metrics['consistency']}%")
    m2.metric("Avg Daily Effort", f"{metrics['avg_effort']}/10")
