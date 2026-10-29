"""
MindScale AI - Voice Analysis Page

Enhanced voice analysis with acoustic features and AI-based sentiment detection.
"""

import io
from typing import Dict, Optional, Tuple

import librosa
import numpy as np
import streamlit as st
import soundfile as sf

from utils.ai_service import load_ai_models, detect_emotion

def extract_voice_features(
    audio_bytes: bytes,
    sr: int = 16000,
) -> Optional[Dict[str, float]]:
    """
    Extract simple voice features from raw audio bytes using librosa.
    """
    try:
        # Load audio with librosa (mono)
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=sr, mono=True)
    except Exception:
        return None

    if y.size == 0:
        return None

    # Trim leading / trailing silence for more robust stats
    y_trimmed, _ = librosa.effects.trim(y, top_db=25)
    if y_trimmed.size == 0:
        y_trimmed = y

    # Energy (RMS)
    rms = librosa.feature.rms(y=y_trimmed)[0]
    energy_mean = float(np.mean(rms))

    # Pitch estimation using librosa.yin (fundamental frequency)
    try:
        f0 = librosa.yin(
            y_trimmed,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
        )
        # Filter out unvoiced / invalid values
        f0 = f0[np.isfinite(f0)]
        pitch_mean_hz = float(np.mean(f0)) if f0.size > 0 else 0.0
    except Exception:
        pitch_mean_hz = 0.0

    # Speech-rate proxy using zero-crossing rate
    zcr = librosa.feature.zero_crossing_rate(y_trimmed)[0]
    zcr_mean = float(np.mean(zcr))
    speech_rate_est = float(zcr_mean * 100)

    return {
        "pitch_mean_hz": pitch_mean_hz,
        "energy_mean": energy_mean,
        "speech_rate_est": speech_rate_est,
    }

def compute_stress_score(features: Dict[str, float]) -> Tuple[int, str]:
    """
    Compute a simple stress score (0–100) from acoustic features.
    """
    pitch = features.get("pitch_mean_hz", 0.0)
    energy = features.get("energy_mean", 0.0)
    speech_rate = features.get("speech_rate_est", 0.0)

    norm_energy = np.clip(energy / 0.1, 0.0, 1.0)
    norm_rate = np.clip(speech_rate / 50.0, 0.0, 1.0)
    norm_pitch = np.clip((pitch - 80.0) / 200.0, 0.0, 1.0)

    raw = 0.4 * norm_energy + 0.4 * norm_rate + 0.2 * norm_pitch
    score = int(round(np.clip(raw, 0.0, 1.0) * 100))

    if score < 35: level = "low"
    elif score < 70: level = "moderate"
    else: level = "high"

    return score, level

def render():
    """Render the voice analysis page."""
    st.markdown("# 🎤 Voice & sentiment Analysis")
    st.markdown("Record your voice to analyze both acoustic stress and emotional sentiment.")
    st.markdown("---")

    # Load AI models for sentiment/transcription
    emotion_model, speech_model = load_ai_models()

    st.markdown("### Step 1: Record your voice")
    st.caption("Click the button below and speak for about 5-10 seconds.")

    # Import the recorder lazily
    try:
        from audio_recorder_streamlit import audio_recorder
    except ImportError:
        st.error("Please install audio-recorder-streamlit")
        return

    audio_bytes = audio_recorder(
        text="Click to record / stop",
        pause_threshold=2.0,
        sample_rate=16000,
    )

    if not audio_bytes:
        st.info("Waiting for recording...")
        return

    st.audio(audio_bytes, format="audio/wav")

    if st.button("Run Full Analysis"):
        with st.status("Analyzing voice...") as status:
            # 1. Acoustic Features
            st.write("Extracting acoustic features (pitch, energy)...")
            features = extract_voice_features(audio_bytes)
            
            # 2. Transcription & Sentiment
            st.write("Transcribing voice and detecting sentiment...")
            sentiment = "Unknown"
            transcription = ""
            if features and speech_model and emotion_model:
                try:
                    # Whisper expects float32
                    audio_file = io.BytesIO(audio_bytes)
                    data, sr = sf.read(audio_file)
                    if data.dtype != np.float32:
                        data = data.astype(np.float32)
                    if len(data.shape) > 1:
                        data = data.mean(axis=1)
                    
                    transcription = speech_model({"sampling_rate": sr, "raw": data})["text"]
                    sentiment = detect_emotion(transcription, emotion_model)
                except Exception as e:
                    st.error(f"Sentiment error: {e}")

            status.update(label="Analysis Complete!", state="complete")

        if features is None:
            st.error("Could not process audio.")
            return

        score, level = compute_stress_score(features)
        
        # Results Display
        st.markdown("---")
        st.subheader("Analysis Results")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Stress Score", f"{score}/100", delta=level, delta_color="inverse")
        c2.metric("Detected Sentiment", sentiment.capitalize())
        c3.metric("Pitch (mean)", f"{features['pitch_mean_hz']:.1f} Hz")

        if transcription:
            st.write(f"**Transcription:** *\"{transcription}\"*")

        st.markdown("### Insights")
        if sentiment in ["sad", "angry", "anxious"]:
            st.warning(f"Your voice conveys **{sentiment}** sentiment with a **{level}** stress level. Take a deep breath.")
        elif sentiment == "happy":
            st.success(f"You sound **happy**! Your stress level is **{level}**.")
        else:
            st.info(f"Your voice is **{sentiment}** with a **{level}** stress level.")

        # Save to DB if available
        user_id = st.session_state.get("user_id")
        if user_id:
            try:
                from database.db import save_score
                save_score(user_id, "voice_stress", float(score))
                # Trigger MCI Update
                from utils.scoring_service import calculate_and_save_mci
                calculate_and_save_mci(user_id)
            except:
                pass

