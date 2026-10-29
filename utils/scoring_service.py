"""
MindScale AI - Scoring Service
Handles normalization, weighting, and composite index calculations for the MindScale Composite Index (MCI).
"""

import sqlite3
import json
from datetime import date
import numpy as np
from database.db import get_connection

def normalize_risk_score(raw_score, max_score):
    """
    Normalizes a risk score (where high is bad) to a 0-100 wellness score (where 100 is good).
    Formula: 100 - (raw_score / max_score * 100)
    """
    if max_score <= 0:
        return 50.0 # Neutral default
    percentage = (raw_score / max_score) * 100
    return max(0.0, min(100.0, 100.0 - percentage))

def get_latest_psychological_index(user_id):
    """
    Calculates the MindScale Psychological Index.
    Combines PHQ-9, GAD-7, PSS-10, Burnout, and NLP reflection.
    """
    from database.db import get_latest_assessment_summary
    summary = get_latest_assessment_summary(user_id)
    
    if not summary:
        return 50.0
        
    scores = json.loads(summary['individual_scores_json'] or "{}")
    
    # Normalization (Max values based on clinical standards)
    phq9 = normalize_risk_score(scores.get('depression_phq9', 0), 27)
    gad7 = normalize_risk_score(scores.get('anxiety_gad7', 0), 21)
    pss10 = normalize_risk_score(scores.get('stress_pss10', 0), 40)
    burnout = normalize_risk_score(scores.get('burnout_student', 0), 40) # Student burnout max approx 40
    
    # NLP Reflection (100 is already good)
    nlp_ref = summary.get('nlp_reflection_score', 50.0)
    
    # Weighted sum
    index = (0.25 * phq9) + (0.20 * gad7) + (0.20 * pss10) + (0.20 * burnout) + (0.15 * nlp_ref)
    return round(index, 2)

def get_latest_nlp_emotional_score(user_id):
    """
    Calculates the NLP Emotional Score.
    Uses sentiment, pronoun density, negation usage, and keystroke stress.
    """
    from database.db import get_user_nlp_sessions
    sessions = get_user_nlp_sessions(user_id, limit=1)
    
    if not sessions:
        return 50.0
        
    latest = sessions[0]
    
    # Normalize components
    sentiment = (latest['avg_sentiment'] + 1) * 50 # -1 to 1 -> 0 to 100
    pronoun_score = 100 - (latest.get('pronoun_ratio', 0) * 100) # High 'I' density can correlate with distress
    negation_score = 100 - (latest.get('negation_count', 0) * 10) # Simple penalty
    keystroke_stress = 100 - latest['avg_keystroke_stress']
    
    score = (0.40 * sentiment) + (0.20 * pronoun_score) + (0.20 * negation_score) + (0.20 * keystroke_stress)
    return round(max(0.0, min(100.0, score)), 2)

def get_latest_voice_emotion_score(user_id):
    """
    Calculates the Voice Emotion Score.
    Uses energy/pitch/rate stability and voice sentiment.
    """
    # Assuming voice_stress in DB is actually a stress score (high=bad)
    # We ideally need the stability metrics too if stored. 
    # For now, using the voice_stress and inverting it plus a sentiment proxy.
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score_value FROM scores WHERE user_id = ? AND score_type = 'voice_stress' ORDER BY created_at DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return 50.0
        
    stress_score = row['score_value']
    voice_wellness = 100 - stress_score
    
    # We use voice wellness as a base. Stability metrics would refine this.
    return round(voice_wellness, 2)

def get_latest_goal_progress_score(user_id):
    """
    Calculates the Daily Goal Progress Score.
    Uses consistency, effort, and NLP progress scores.
    """
    from utils.goal_service import get_goal_metrics
    metrics = get_goal_metrics(user_id)
    
    if not metrics:
        return 50.0
        
    score = (0.40 * metrics['consistency']) + (0.35 * metrics['avg_effort'] * 10) + (0.25 * metrics.get('nlp_progress_avg', 50))
    return round(score, 2)

def get_latest_chat_sentiment_score(user_id):
    """
    Calculates the average sentiment of the last 3 user messages.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Fetch latest chat sentiment scores saved by the chatbot
    cursor.execute("SELECT score_value FROM scores WHERE user_id = ? AND score_type = 'chat_sentiment' ORDER BY created_at DESC LIMIT 3", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 50.0
        
    avg_sentiment = sum(row['score_value'] for row in rows) / len(rows)
    return round(avg_sentiment, 2)

def get_latest_emotional_insight_score(user_id):
    """
    Calculates the Emotional Insight Score based on facial emotion sampling.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emotion_json FROM emotion_data WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return 50.0
        
    wellness_scores = []
    for row in rows:
        try:
            probs = json.loads(row['emotion_json'])
            # Wellness = 1.0 - (sad + fear + angry + disgust)
            negative = probs.get('sad', 0) + probs.get('fear', 0) + probs.get('angry', 0) + probs.get('disgust', 0)
            wellness_scores.append(1.0 - negative)
        except:
            continue
            
    if not wellness_scores:
        return 50.0
        
    avg_wellness = sum(wellness_scores) / len(wellness_scores)
    return round(max(0.0, min(100.0, avg_wellness * 100)), 2)

def generate_ai_insight(mci, psych, nlp, voice, goal, chat, face):
    """
    Generates a short explanation for the user based on component scores.
    """
    insights = []
    
    if mci >= 80:
        base = f"Your MindScale Index is {mci:.0f}. You are showing excellent overall wellness."
    elif mci >= 60:
        base = f"Your MindScale Index is {mci:.0f}. You are doing well, with healthy indicators across most modules."
    else:
        base = f"Your MindScale Index is {mci:.0f}. It might be a good time to focus on some self-care."
        
    insights.append(base)
    
    # Specific component callouts
    if psych < 50:
        insights.append("Clinical indicators suggest you might be feeling overwhelmed lately.")
    if nlp < 50:
        insights.append("Your writing patterns show some signs of emotional tension.")
    if voice < 50:
        insights.append("Voice analysis detected slight emotional stress or fatigue in your speech.")
    if goal < 50:
        insights.append("You might find it helpful to set smaller, more achievable daily goals to build momentum.")
    if chat < 50:
        insights.append("Your recent interactions suggest you've been feeling a bit lower than usual.")
    if face < 50:
        insights.append("Your facial expressions during assessments show signs of focus or subtle emotional intensity.")
        
    if len(insights) == 1:
        insights.append("All your wellness indicators are currently balanced and stable.")
        
    return " ".join(insights)

def calculate_and_save_mci(user_id):
    """
    Calculates all MCI components and saves the record to the database.
    """
    psych = get_latest_psychological_index(user_id)
    nlp = get_latest_nlp_emotional_score(user_id)
    voice = get_latest_voice_emotion_score(user_id)
    goal = get_latest_goal_progress_score(user_id)
    chat = get_latest_chat_sentiment_score(user_id)
    face = get_latest_emotional_insight_score(user_id)
    
    # MCI Final Weighting (Updated to include Facial Emotional Insight)
    mci = (0.30 * psych) + (0.15 * nlp) + (0.15 * voice) + (0.20 * goal) + (0.10 * chat) + (0.10 * face)
    mci = round(mci, 2)
    
    insight = generate_ai_insight(mci, psych, nlp, voice, goal, chat, face)
    current_date = date.today().isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO mindscale_scores (
                user_id, date, psychological_index, nlp_emotional_score, 
                voice_emotion_score, emotional_insight_score, goal_progress_score, 
                chat_sentiment_score, mindscale_composite_index, analysis_insight
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                psychological_index=excluded.psychological_index,
                nlp_emotional_score=excluded.nlp_emotional_score,
                voice_emotion_score=excluded.voice_emotion_score,
                emotional_insight_score=excluded.emotional_insight_score,
                goal_progress_score=excluded.goal_progress_score,
                chat_sentiment_score=excluded.chat_sentiment_score,
                mindscale_composite_index=excluded.mindscale_composite_index,
                analysis_insight=excluded.analysis_insight
        """, (user_id, current_date, psych, nlp, voice, face, goal, chat, mci, insight))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving MCI: {e}")
        return False
    finally:
        conn.close()

def get_mci_history(user_id, limit=7):
    """Retrieves recent MCI history for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mindscale_scores 
        WHERE user_id = ? 
        ORDER BY date DESC LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows][::-1] # Ascending order for charts
