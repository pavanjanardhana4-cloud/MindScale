"""
MindScale AI - Chatbot Page

Conversational mental health support assistant powered by Groq and Transformers.
Based on the high-quality assistant from Hug folder.
"""

import os
import time
import streamlit as st

from utils.ai_service import (
    load_ai_models, 
    get_groq_client, 
    detect_emotion, 
    suicide_help_check,
    get_user_mental_context,
    format_context_for_bot
)

def render():
    """Render the chatbot page."""
    
    # Header
    st.markdown("<h1 style='text-align: center;'>🧠 MindScale AI Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Talk about your feelings and track your mood. You are safe here ❤️</p>", unsafe_allow_html=True)
    st.markdown("---")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.info("Please log in to use the chatbot.")
        return

    # Load models
    emotion_model, speech_model = load_ai_models()
    client = get_groq_client()

    if not client:
        st.error("GROQ_API_KEY not found. Please set it in your environment or Streamlit secrets.")
        return

    # Initialize session state for messages and sentiment
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi, I'm your mental health support assistant. How are you feeling today?"}
        ]
    if "mood_history" not in st.session_state:
        st.session_state.mood_history = []
    if "session_sentiments" not in st.session_state:
        st.session_state.session_sentiments = []

    # Get user mental context from other modules
    mental_context = get_user_mental_context(user_id)
    context_summary = format_context_for_bot(mental_context)

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # UI Enhancement: Chat Input
    st.markdown("---")
    prompt = st.chat_input("Share how you're feeling...")

    # Process Input
    if prompt:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Detect Emotion & Suicide Risk
        emotion = detect_emotion(prompt, emotion_model)
        st.session_state.mood_history.append(emotion)
        
        # Convert emotion to numeric sentiment proxy for scoring (0 to 1)
        sentiment_map = {"happy": 1.0, "surprised": 0.7, "neutral": 0.5, "anxious": 0.3, "sad": 0.1, "angry": 0.0}
        st.session_state.session_sentiments.append(sentiment_map.get(emotion, 0.5))
        
        # Check for emergency
        if suicide_help_check(prompt):
            response = (
                "💛 I'm really sorry you're feeling this way.\n\n"
                "You are **not alone** and help is available.\n\n"
                "🇮🇳 **India Suicide Helplines**\n\n"
                "📞 Kiran: 1800-599-0019\n"
                "📞 AASRA: +91-22-27546669\n\n"
                "Please consider reaching out to someone you trust."
            )
        else:
            # Get AI Response with Context Awareness
            with st.spinner("Thinking..."):
                try:
                    system_prompt = (
                        "You are a compassionate mental health assistant. "
                        f"Current detected user emotion: {emotion}.\n"
                        f"{context_summary}\n"
                        "Use the provided clinical context to personalize your support. "
                        "Respond kindly and supportively. Ask helpful follow-up questions."
                    )
                    
                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": system_prompt}
                        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    )
                    response = completion.choices[0].message.content
                    
                    # Periodic Sentiment Saving (Every 3 exchanges or when ending)
                    if len(st.session_state.session_sentiments) >= 3:
                        avg_sentiment = sum(st.session_state.session_sentiments) / len(st.session_state.session_sentiments)
                        from database.db import save_score
                        save_score(user_id, "chat_sentiment", avg_sentiment * 100) # Save as 0-100
                        
                        # Trigger MCI Update
                        from utils.scoring_service import calculate_and_save_mci
                        calculate_and_save_mci(user_id)
                        
                except Exception as e:
                    response = f"I'm sorry, I encountered an error: {e}"

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Dashboard-like snippets
    if st.session_state.mood_history:
        with st.expander("📊 Session Mood Insights"):
            st.write(f"Detected emotions this session: {', '.join(st.session_state.mood_history)}")
            if st.session_state.session_sentiments:
                avg_val = sum(st.session_state.session_sentiments) / len(st.session_state.session_sentiments)
                st.progress(avg_val)
                st.caption(f"Average session sentiment: {avg_val:.2f}")

