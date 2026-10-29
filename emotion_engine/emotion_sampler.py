import time
import streamlit as st
from .camera_manager import CameraManager
from .emotion_model import EmotionModel
from database.db import save_emotion_log

class EmotionSampler:
    """Orchestrates emotion sampling via browser-based snapshots."""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.camera = CameraManager()
        self.model = EmotionModel()
        
    def capture_snapshot(self, uploaded_file, label="Baseline", question_id=None):
        """
        Processes a single snapshot from st.camera_input.
        """
        if uploaded_file is None:
            return None
            
        frame = self.camera.process_image(uploaded_file)
        if frame is not None:
            probs = self.model.analyze_frame(frame)
            if probs:
                # Save to database
                save_emotion_log(self.user_id, probs, question_id)
                
                # Update session state
                if "emotion_log" not in st.session_state:
                    st.session_state.emotion_log = []
                
                log_entry = {
                    "question_id": question_id,
                    "timestamp": time.time(),
                    "emotion_probs": probs,
                    "label": label
                }
                st.session_state.emotion_log.append(log_entry)
                
                if label == "Baseline":
                    st.session_state.baseline_emotion = probs
                    
                return probs
        return None

    def handle_periodic_sampling(self, current_question_id=None, high_risk=False):
        """
        In browser mode, periodic sampling is replaced by manual snapshots 
        integrated into the questionnaire UI.
        """
        pass
