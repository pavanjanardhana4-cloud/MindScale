"""
MindScale AI - Goal Tracking Service
Handles database interactions and NLP analysis for the Daily Goal Tracking feature.
"""

import datetime
import json
from database.db import get_connection, save_score
from nlp_engine.nlp_service import analyze_text
from utils.ai_service import detect_emotion, load_ai_models

def check_daily_recorded(user_id):
    """Check if the user has already recorded a goal entry for today."""
    today = datetime.date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM daily_goal_tracking WHERE user_id = ? AND date = ?",
        (user_id, today)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None

def save_daily_goal(user_id, goal_action, goal_activity, effort_score):
    """
    Saves a daily goal entry, performs NLP analysis on activity text,
    and returns the processed data.
    """
    today = datetime.date.today().isoformat()
    
    # NLP Analysis
    nlp_results = analyze_text(goal_activity)
    sentiment_score = nlp_results['sentiment_score']
    
    # Progress indicator logic (heuristic)
    action_keywords = ["study", "practice", "build", "apply", "learn", "complete", "worked", "did", "finished"]
    progress_score = 0.0
    
    if goal_action == "yes":
        progress_score += 50.0
    elif goal_action == "partial":
        progress_score += 25.0
        
    # Boost progress score if action keywords are mentioned
    mentions = [word for word in action_keywords if word in goal_activity.lower()]
    progress_score += min(50.0, len(mentions) * 10.0)
    
    # Normalize effort score to 0-100
    normalized_effort = effort_score * 10.0
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO daily_goal_tracking 
               (user_id, date, goal_action, goal_activity, effort_score, sentiment_score, progress_score) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, today, goal_action, goal_activity, effort_score, sentiment_score, progress_score)
        )
        conn.commit()
        conn.close()
        
        # Also save effort as a general score for trend analysis
        save_score(user_id, "goal_effort", normalized_effort)
        
        return True
    except Exception as e:
        print(f"Error saving daily goal: {e}")
        return False

def get_goal_metrics(user_id):
    """Calculates consistency, average effort, and recent history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM daily_goal_tracking WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not rows:
        return None
        
    total_days = len(rows)
    consistent_days = sum(1 for r in rows if r['goal_action'] in ['yes', 'partial'])
    
    consistency = (consistent_days / total_days) * 100 if total_days > 0 else 0
    avg_effort = sum(r['effort_score'] for r in rows) / total_days if total_days > 0 else 0
    
    return {
        "consistency": round(consistency, 1),
        "avg_effort": round(avg_effort, 1),
        "history": rows[:7] # Last 7 entries
    }
