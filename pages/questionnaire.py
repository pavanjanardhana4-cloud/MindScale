import streamlit as st
import json
import time
from questionnaire_engine import QuestionnaireRenderer, calculate_composite_index
from emotion_engine.emotion_sampler import EmotionSampler
from emotion_engine.emotion_scoring import get_session_summary
from database.db import (
    save_granular_responses, 
    save_assessment_summary, 
    get_all_latest_granular_responses
)

def render():
    st.markdown("# 📝 Holistic Assessment Center")
    st.markdown("Please complete the following assessments to help us understand your wellness profile.")
    st.markdown("---")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to take assessments.")
        return

    # --- Emotion Engine Integration ---
    if "emotion_sampler" not in st.session_state:
        st.session_state.emotion_sampler = EmotionSampler(user_id)
    
    sampler = st.session_state.emotion_sampler
    
    col_c, col_s = st.columns([1, 1])
    with col_c:
        consent = sampler.camera.request_consent()
    
    if consent:
        with st.sidebar:
            st.divider()
            if "baseline_emotion" not in st.session_state:
                st.warning("⚠️ **Baseline Required**")
                st.info("👋 To begin, capture your baseline mood below.")
                baseline_photo = st.camera_input("Capture Baseline Mood", key="persistent_camera")
                if baseline_photo:
                    with st.spinner("Analyzing baseline..."):
                        sampler.capture_snapshot(baseline_photo, label="Baseline")
                        st.success("✅ Baseline captured!")
                        time.sleep(1)
                        st.rerun()
            else:
                st.success("🟢 Emotion Analysis Active")
                st.info("📸 Use the camera below to sync your mood whenever requested or if you feel a shift.")
                snap = st.camera_input("Sync Mood Snapshot", key="persistent_camera")
                if snap:
                    # Determine current step context
                    q_step = st.session_state.get("current_q_step", 0)
                    sampler.capture_snapshot(snap, label="Assessment Sync", question_id=f"step_{q_step}")
                    st.toast("Mood synced for this section!")
    else:
        # If user revokes consent
        if "baseline_emotion" in st.session_state:
            del st.session_state.baseline_emotion
            st.session_state.emotion_log = []

    # Initialize Engine
    import os
    from pathlib import Path
    
    # Secure path to schema relative to this file
    base_dir = Path(__file__).parent.parent
    schema_path = base_dir / "questionnaire_engine" / "schema.json"
    
    active_sampler = sampler if (consent and "baseline_emotion" in st.session_state) else None
    renderer = QuestionnaireRenderer(str(schema_path), sampler=active_sampler)
    schema = renderer.schema
    
    # Get all questionnaire IDs from schema
    q_ids = [q['id'] for q in schema['questionnaires']]
    num_steps = len(q_ids)
    
    # Track current step in session state
    if "current_q_step" not in st.session_state:
        st.session_state.current_q_step = 0
        
    current_idx = st.session_state.current_q_step
    
    # Progress indicator
    st.progress((current_idx) / num_steps)
    st.write(f"Step {current_idx + 1} of {num_steps}")

    selected_id = q_ids[current_idx]
    
    # Determine button label
    is_last_step = current_idx == (num_steps - 1)
    btn_label = "Complete Assessment & Finalize" if is_last_step else "Next Assessment ➡️"
    
    # Render the current questionnaire
    answers = renderer.render(selected_id, button_label=btn_label)
    
    if answers:
        # Store answers for the current step in session state
        st.session_state[f"answers_{selected_id}"] = answers

        # If not last step, just move forward
        if not is_last_step:
            st.session_state.current_q_step += 1
            st.success(f"Part {current_idx + 1} complete! Moving to next section...")
            st.rerun()
        else:
            # Final Submission Logic
            st.write("🔄 Finalizing your wellness profile...")
            
            # 1. Collect all answers from session state
            all_responses = {}
            for q_id in q_ids:
                q_answers = st.session_state.get(f"answers_{q_id}", {})
                all_responses[q_id] = q_answers
                
            # 2. Save granular responses to DB
            save_granular_responses(user_id, all_responses)
            
            # 3. Calculate and save composite summary
            composite_data = calculate_composite_index(schema, all_responses)
            save_assessment_summary(
                user_id=user_id,
                composite_score=composite_data['composite_score'],
                overall_risk=composite_data['overall_risk'],
                individual_scores=composite_data['individual_scores']
            )
            # 4. Handle Emotion Engine Finalization
            if active_sampler:
                # Release camera immediately
                active_sampler.camera.release()
                st.info("📸 Camera released and session closed.")
            
            # 5. Trigger MCI Update
            from utils.scoring_service import calculate_and_save_mci
            calculate_and_save_mci(user_id)
            
            # 6. Clean up session state
            st.session_state.current_q_step = 0
            for q_id in q_ids:
                if f"answers_{q_id}" in st.session_state:
                    del st.session_state[f"answers_{q_id}"]
            
            if "baseline_emotion" in st.session_state:
                del st.session_state.baseline_emotion
            if "emotion_log" in st.session_state:
                st.session_state.emotion_log = []
            
            st.balloons()
            st.success("✨ All assessments completed! Your wellness profile has been updated.")
            if st.button("Go to Dashboard"):
                # Simplified navigation
                st.session_state.current_page = "Dashboard"
                st.rerun()

    # Reset option if someone wants to start over
    if current_idx > 0:
        st.markdown("---")
        if st.button("🗑️ Start Over"):
            st.session_state.current_q_step = 0
            # Also clear current answers
            for q_id in q_ids:
                if f"answers_{q_id}" in st.session_state:
                    del st.session_state[f"answers_{q_id}"]
            st.rerun()
