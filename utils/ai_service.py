import os
import streamlit as st
from groq import Groq
from transformers import pipeline

@st.cache_resource
def load_ai_models():
    """
    Load and cache emotion detection and speech recognition models.
    """
    try:
        emotion_pipe = pipeline(
            "text-classification", 
            model="j-hartmann/emotion-english-distilroberta-base"
        )
        speech_pipe = pipeline(
            "automatic-speech-recognition", 
            model="openai/whisper-tiny.en"
        )
        return emotion_pipe, speech_pipe
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None

def get_groq_client():
    """
    Returns a configured Groq client.
    """
    api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def detect_emotion(text, emotion_model):
    """
    Detects emotion from text using the provided model.
    """
    if not text or not emotion_model:
        return "neutral"
        
    try:
        result = emotion_model(text)[0]["label"].lower()
        mapping = {
            "joy": "happy",
            "sadness": "sad",
            "anger": "angry",
            "fear": "anxious",
            "surprise": "surprised",
            "neutral": "neutral"
        }
        return mapping.get(result, "neutral")
    except Exception:
        return "neutral"

def suicide_help_check(text):
    """
    Checks for suicide-related keywords.
    """
    keywords = ["suicide", "kill myself", "want to die", "end my life"]
    for word in keywords:
        if word in text.lower():
            return True
    return False

def get_user_mental_context(user_id):
    """
    Fetches the latest mental health metrics for a user from the database.
    Returns a dictionary of context data.
    """
    from database.db import (
        get_latest_assessment_summary, 
        get_user_nlp_sessions, 
        get_user_scores
    )
    
    context = {}
    
    # 1. Holistic Assessment (Composite)
    summary = get_latest_assessment_summary(user_id)
    if summary:
        context['holistic'] = {
            'score': summary['composite_score'],
            'risk': summary['overall_risk']
        }
        
    # 2. NLP Analysis
    nlp_sessions = get_user_nlp_sessions(user_id, limit=1)
    if nlp_sessions:
        latest_nlp = nlp_sessions[0]
        context['nlp'] = {
            'risk_index': latest_nlp['emotional_risk_index'],
            'avg_sentiment': latest_nlp['avg_sentiment']
        }
        
    # 3. Voice Analysis
    scores = get_user_scores(user_id)
    voice_scores = [s for s in scores if s['score_type'] == 'voice_stress']
    if voice_scores:
        latest_voice = voice_scores[0]
        context['voice'] = {
            'stress_score': latest_voice['score_value']
        }
        
    return context

def format_context_for_bot(context):
    """
    Formats the context dictionary into a text summary for the AI system prompt.
    """
    if not context:
        return "No recent clinical assessment data available for this user."
        
    parts = ["Here is the user's latest clinical assessment data:"]
    
    if 'holistic' in context:
        parts.append(f"- Holistic Wellness: Score {context['holistic']['score']}/100 ({context['holistic']['risk']} profile).")
    
    if 'nlp' in context:
        parts.append(f"- Behavioral/NLP Risk: {context['nlp']['risk_index']}% emotional risk based on writing patterns.")
        
    if 'voice' in context:
        parts.append(f"- Voice Stress: {context['voice']['stress_score']}/100 stress level detected in last recording.")
        
    return "\n".join(parts)
