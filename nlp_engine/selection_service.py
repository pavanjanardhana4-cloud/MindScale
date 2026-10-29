import json
import random
from database.db import get_recent_question_ids

import os
from pathlib import Path

def load_questions():
    # Path relative to this file
    base_dir = Path(__file__).parent
    path = base_dir / "questions.json"
    with open(path, "r") as f:
        return json.load(f)["categories"]

def select_session_questions(user_id, session_id):
    """
    Selects 1 question from each of the 5 categories.
    Prevents repetition from the last 2 sessions if user has enough history.
    """
    all_categories = load_questions()
    recent_q_ids = get_recent_question_ids(user_id, limit_sessions=2)
    
    selected_questions = []
    
    for category, questions in all_categories.items():
        # Filter out questions shown in the last 2 sessions
        available = [q for q in questions if q['id'] not in recent_q_ids]
        
        # If too many were filtered (unlikely with 5 questions per cat), 
        # fallback to all questions for that category
        if not available:
            available = questions
            
        selected_questions.append(random.choice(available))
        
    return selected_questions
