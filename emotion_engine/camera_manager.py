import cv2
import numpy as np
from PIL import Image
import streamlit as st

class CameraManager:
    """Manages browser-based camera input via st.camera_input."""
    
    def __init__(self):
        pass

    def request_consent(self):
        """Handle user consent with a checkbox."""
        st.info("💡 **Privacy Note**: Emotion sampling works entirely in your browser. We extract numeric probabilities only; no images or video are ever stored.")
        consent = st.checkbox("Enable facial emotion analysis during assessment", key="emotion_consent")
        return consent

    def process_image(self, uploaded_file):
        """
        Convert Streamlit's uploaded file (PIL Image) to OpenCV format.
        """
        if uploaded_file is None:
            return None
            
        # Convert to PIL Image
        img = Image.open(uploaded_file)
        # Convert to RGB (OpenCV uses BGR, but DeepFace handles RGB if specified or we convert)
        img_array = np.array(img)
        # DeepFace expects BGR if using opencv backend
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        return img_bgr

    def release(self):
        """No hardware release needed for st.camera_input."""
        pass

    def show_status(self):
        """Display a visible indicator in Streamlit."""
        st.success("📸 Camera Ready for Snapshot")
