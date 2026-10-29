from deepface import DeepFace
import cv2
import numpy as np

class EmotionModel:
    """Wrapper for DeepFace to extract emotion probabilities from frames."""
    
    def __init__(self):
        # Pre-initialize by doing a dummy analysis to load models if needed
        # We use 'opencv' as backends for speed
        self.emotions_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

    def analyze_frame(self, frame):
        """
        Analyze a single frame and return emotion probabilities.
        Returns: dict or None if no face detected.
        """
        try:
            # Analyze frame for emotions only
            # enforce_detection=True ensures we only get data if a face is clear
            results = DeepFace.analyze(
                frame, 
                actions=['emotion'], 
                enforce_detection=True,
                detector_backend='opencv',
                silent=True
            )
            
            if results and len(results) > 0:
                # results is a list of results for each face found
                # For this project, we assume the user is the only one in frame
                main_face = results[0]
                # Convert numpy float32 to standard python floats for JSON serialization
                # DeepFace returns 0-100, we normalize to 0-1
                return {k: float(v) / 100.0 for k, v in main_face['emotion'].items()}
                
        except Exception as e:
            # No face detected or other error
            return None
            
        return None

    def get_average_emotions(self, frames):
        """Average emotion probabilities across multiple frames."""
        if not frames:
            return None
            
        accumulated = {label: 0.0 for label in self.emotions_labels}
        valid_count = 0
        
        for frame in frames:
            probs = self.analyze_frame(frame)
            if probs:
                valid_count += 1
                for label in self.emotions_labels:
                    accumulated[label] += probs.get(label, 0.0)
        
        if valid_count == 0:
            return None
            
        return {label: accumulated[label] / valid_count for label in self.emotions_labels}
