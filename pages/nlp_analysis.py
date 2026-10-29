import uuid
import streamlit as st
from nlp_engine.selection_service import select_session_questions
from nlp_engine.component import nlp_keystroke_assessment
from nlp_engine.nlp_service import analyze_text
from nlp_engine.keystroke_analytics import process_keystrokes
from nlp_engine.scoring import calculate_behavioral_score, calculate_session_risk
from database.db import save_nlp_response_analysis, save_nlp_session_summary, log_question_presentation

def render():
    """Render the Enhanced NLP Analysis Wizard."""
    st.markdown("# 🧠 Behavioral & Linguistic Assessment")
    st.markdown("This assessment measures emotional risk through both shared reflections and typing patterns.")
    st.markdown("---")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to take the NLP assessment.")
        return

    # Initialize NLP session
    if "nlp_session_active" not in st.session_state:
        st.session_state.nlp_session_active = False
        st.session_state.nlp_session_id = None
        st.session_state.nlp_questions = []

    if not st.session_state.nlp_session_active:
        st.markdown("""
        ### Instructions
        1. You will be asked **5 reflective questions** across different categories.
        2. Please share your thoughts naturally and in detail (at least 2-3 sentences per question).
        3. We analyze **what** you write and **how** you type to understand your state of mind.
        4. Estimated time: **4-5 minutes**.
        """)
        
        if st.button("🚀 Start Assessment"):
            session_id = str(uuid.uuid4())
            questions = select_session_questions(user_id, session_id)
            
            st.session_state.nlp_session_id = session_id
            st.session_state.nlp_questions = questions
            st.session_state.nlp_session_active = True
            
            # Log that these questions were shown
            log_question_presentation(user_id, session_id, [q['id'] for q in questions])
            st.rerun()
        return

    # Wizard Mode
    st.info("⚠️ Please do not refresh the page until the assessment is complete.")
    
    # Render the custom component
    results = nlp_keystroke_assessment(st.session_state.nlp_questions, key="nlp_wizard")
    
    if results:
        with st.spinner("Analyzing behavioral patterns..."):
            session_id = st.session_state.nlp_session_id
            question_analyses = []
            
            for res in results:
                q_id = res['question_id']
                text = res['text']
                events = res['events']
                
                # 1. NLP Analysis
                nlp_metrics = analyze_text(text)
                
                # 2. Keystroke Analytics
                ks_metrics = process_keystrokes(events)
                
                # 3. Behavioral Stress Score (Per Question)
                behav_score = calculate_behavioral_score(
                    nlp_metrics['sentiment_score'],
                    ks_metrics['hesitation_ratio'],
                    ks_metrics['correction_ratio'],
                    ks_metrics['avg_speed']
                )
                
                # Prepare combined data for storage
                q_data = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'question_id': q_id,
                    'response_text': text,
                    'behavioral_score': behav_score,
                    'keystroke_score': float(ks_metrics['hesitation_ratio'] * 100), # Simple proxy
                    **nlp_metrics
                }
                
                save_nlp_response_analysis(q_data)
                question_analyses.append(q_data)
            
            # 4. Session Level Aggregation
            session_summary = calculate_session_risk(question_analyses)
            session_summary['user_id'] = user_id
            session_summary['session_id'] = session_id
            
            save_nlp_session_summary(session_summary)
            
            # Trigger MCI Update
            from utils.scoring_service import calculate_and_save_mci
            calculate_and_save_mci(user_id)
            
            # Store in session for immediate feedback
            st.session_state.last_nlp_risk = session_summary['emotional_risk_index']
            st.session_state.nlp_session_active = False
            
            st.balloons()
            st.success("✅ Assessment complete! Your emotional risk index has been updated.")
            
            # Show summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Sentiment", f"{session_summary['avg_sentiment']}")
            with col2:
                st.metric("Keystroke Stress", f"{session_summary['avg_keystroke_stress']}%")
            with col3:
                st.metric("Emotional Risk Index", f"{session_summary['emotional_risk_index']}%")
            
            st.markdown("### 📝 Detailed Breakdown")
            for i, q_data in enumerate(question_analyses):
                # Find the question text from current session questions
                q_text = next((q['text'] for q in st.session_state.nlp_questions if q['id'] == q_data['question_id']), "Question")
                
                with st.expander(f"Response {i+1}: {q_data['sentiment_label'].upper()}"):
                    st.write(f"**Question:** {q_text}")
                    st.write(f"**Your Answer:** {q_data['response_text']}")
                    
                    inner_col1, inner_col2 = st.columns(2)
                    with inner_col1:
                        st.write(f"**Sentiment Label:** {q_data['sentiment_label'].capitalize()}")
                        st.write(f"**Sentiment Score:** {q_data['sentiment_score']}")
                    with inner_col2:
                        st.write(f"**Keystroke Stress:** {q_data['keystroke_score']:.1f}%")
                        st.write(f"**Word Count:** {q_data['word_count']}")

            if st.button("Go to Dashboard"):
                st.session_state.current_page = "Dashboard"
                st.rerun()

    # Reset option (Sidebar)
    if st.sidebar.button("🗑️ Reset NLP Assessment"):
        st.session_state.nlp_session_active = False
        st.rerun()

