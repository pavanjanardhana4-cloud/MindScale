"""
MindScale AI - Database Module
SQLite database initialization and connection management.
"""

import sqlite3
from pathlib import Path

# Database file path (relative to project root)
DB_PATH = Path(__file__).parent.parent / "MindScale.db"


def get_connection():
    """Get a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Initialize database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Migrate from old username schema to email if needed
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "username" in columns and "email" not in columns:
            cursor.execute("DROP TABLE users")

    # Users table (email-based auth)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            short_term_goal TEXT,
            long_term_goal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration for existing users table if goals are missing
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    if "short_term_goal" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN short_term_goal TEXT")
    if "long_term_goal" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN long_term_goal TEXT")

    # NEW: Daily Goal Tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_goal_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            goal_action TEXT NOT NULL,
            goal_activity TEXT,
            effort_score INTEGER NOT NULL,
            sentiment_score REAL,
            progress_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, date)
        )
    """)

    # Scores table (for storing assessment results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score_type TEXT NOT NULL,
            score_value REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Questionnaire responses (stores full response data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questionnaire_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            questionnaire_id TEXT NOT NULL,
            responses TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # NEW: Per-question response table for granular tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            questionnaire_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            answer_value TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # NEW: Assessment summary table for composite tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessment_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            composite_score REAL NOT NULL,
            overall_risk TEXT NOT NULL,
            individual_scores_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # NEW: Emotion data table (NO images)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotion_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id TEXT,
            emotion_json TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # OAuth pending states (to handle session loss during redirect)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_pending_states (
            state TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Google Fit tokens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS google_fit_tokens (
            user_id INTEGER PRIMARY KEY,
            token_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # NEW: NLP Question History
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_question_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # NEW: NLP Response Analysis (Linguistic & Keystroke)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nlp_response_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            response_text TEXT,
            sentiment_score REAL,
            sentiment_label TEXT,
            word_count INTEGER,
            pronoun_ratio REAL,
            negation_count INTEGER,
            emotional_intensity REAL,
            behavioral_score REAL,
            keystroke_score REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # NEW: Session-level Emotional Risk index
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_session_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            emotional_risk_index REAL,
            avg_sentiment REAL,
            avg_keystroke_stress REAL,
            variability_factor REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # --- MindScale Composite Index (MCI) Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mindscale_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            psychological_index REAL DEFAULT 0,
            nlp_emotional_score REAL DEFAULT 0,
            voice_emotion_score REAL DEFAULT 0,
            emotional_insight_score REAL DEFAULT 0,
            goal_progress_score REAL DEFAULT 0,
            chat_sentiment_score REAL DEFAULT 0,
            mindscale_composite_index REAL DEFAULT 0,
            analysis_insight TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )
    """)

    # Migration for mindscale_scores if emotional_insight_score is missing
    cursor.execute("PRAGMA table_info(mindscale_scores)")
    mci_columns = [row[1] for row in cursor.fetchall()]
    if "emotional_insight_score" not in mci_columns:
        cursor.execute("ALTER TABLE mindscale_scores ADD COLUMN emotional_insight_score REAL DEFAULT 0")

    conn.commit()
    conn.close()


def get_user_by_email(email: str):
    """Fetch user by email. Returns None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(email: str, password_hash: str, short_term_goal: str = None, long_term_goal: str = None) -> tuple[bool, str]:
    """
    Create a new user. Returns (success, message).
    """
    email = email.lower().strip()
    if not email or "@" not in email:
        return False, "Please enter a valid email address."
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, short_term_goal, long_term_goal) VALUES (?, ?, ?, ?)",
            (email, password_hash, short_term_goal, long_term_goal)
        )
        conn.commit()
        conn.close()
        return True, "Account created successfully! Please login."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."


def save_score(user_id: int, score_type: str, score_value: float):
    """Save a score for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scores (user_id, score_type, score_value) VALUES (?, ?, ?)",
        (user_id, score_type, score_value)
    )
    conn.commit()
    conn.close()


def get_user_scores(user_id: int):
    """Retrieve all scores for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM scores WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_questionnaire_response(user_id: int, questionnaire_id: str, responses: str, total_score: int):
    """Save questionnaire response (responses as JSON string)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO questionnaire_responses (user_id, questionnaire_id, responses, total_score) VALUES (?, ?, ?, ?)",
        (user_id, questionnaire_id, responses, total_score)
    )
    conn.commit()
    conn.close()


def get_questionnaire_responses(user_id: int, questionnaire_id: str | None = None):
    """Retrieve questionnaire responses for a user. Optionally filter by questionnaire_id."""
    conn = get_connection()
    cursor = conn.cursor()
    if questionnaire_id:
        cursor.execute(
            "SELECT * FROM questionnaire_responses WHERE user_id = ? AND questionnaire_id = ? ORDER BY created_at DESC",
            (user_id, questionnaire_id)
        )
    else:
        cursor.execute(
            "SELECT * FROM questionnaire_responses WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_pending_state(state: str, user_id: int):
    """Save a pending OAuth state for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO oauth_pending_states (state, user_id) VALUES (?, ?)", (state, user_id))
    conn.commit()
    conn.close()


def get_pending_state(state: str):
    """Retrieve user_id for a given OAuth state."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM oauth_pending_states WHERE state = ?", (state,))
    row = cursor.fetchone()
    conn.close()
    return row["user_id"] if row else None


def delete_pending_state(state: str):
    """Delete a pending OAuth state."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM oauth_pending_states WHERE state = ?", (state,))
    conn.commit()
    conn.close()


def save_google_fit_token(user_id: int, token_json: str):
    """Save Google Fit token for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO google_fit_tokens (user_id, token_json) VALUES (?, ?)", (user_id, token_json))
    conn.commit()
    conn.close()


def get_google_fit_token(user_id: int):
    """Get Google Fit token for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT token_json FROM google_fit_tokens WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["token_json"] if row else None


def get_user_by_id(user_id: int):
    """Fetch user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_granular_responses(user_id: int, all_responses: dict):
    """Save individual question answers across multiple questionnaires."""
    conn = get_connection()
    cursor = conn.cursor()
    for questionnaire_id, answers in all_responses.items():
        for q_id, val in answers.items():
            cursor.execute(
                "INSERT INTO user_responses (user_id, questionnaire_id, question_id, answer_value) VALUES (?, ?, ?, ?)",
                (user_id, questionnaire_id, q_id, str(val))
            )
    conn.commit()
    conn.close()


def save_assessment_summary(user_id: int, composite_score: float, overall_risk: str, individual_scores: dict):
    """Save overall assessment results."""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO assessment_summary (user_id, composite_score, overall_risk, individual_scores_json) VALUES (?, ?, ?, ?)",
        (user_id, composite_score, overall_risk, json.dumps(individual_scores))
    )
    conn.commit()
    conn.close()


def get_latest_assessment_summary(user_id: int):
    """Get the most recent composite assessment result."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM assessment_summary WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_latest_granular_responses(user_id: int):
    """Get the latest answer for every question across all questionnaires."""
    conn = get_connection()
    cursor = conn.cursor()
    # Complex query to get most recent answer per question
    cursor.execute("""
        SELECT questionnaire_id, question_id, answer_value 
        FROM user_responses 
        WHERE id IN (
            SELECT MAX(id) 
            FROM user_responses 
            WHERE user_id = ? 
            GROUP BY questionnaire_id, question_id
        )
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Organize by questionnaire
    results = {}
    for r in rows:
        q_id = r['questionnaire_id']
        question_id = r['question_id']
        if q_id not in results:
            results[q_id] = {}
        results[q_id][question_id] = r['answer_value']
    return results


def save_emotion_log(user_id: int, emotion_probs: dict, question_id: str = None):
    """Save extracted emotion probabilities to database."""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emotion_data (user_id, question_id, emotion_json) VALUES (?, ?, ?)",
        (user_id, question_id, json.dumps(emotion_probs))
    )
    conn.commit()
    conn.close()


def get_user_emotions(user_id: int, limit: int = 100):
    """Retrieve historical emotion data for user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM emotion_data WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- NLP HELPERS ---

def save_nlp_session_summary(user_analysis: dict):
    """Save aggregated session analysis."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_session_analysis 
           (user_id, session_id, emotional_risk_index, avg_sentiment, avg_keystroke_stress, variability_factor) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_analysis['user_id'], user_analysis['session_id'], 
            user_analysis['emotional_risk_index'], user_analysis['avg_sentiment'],
            user_analysis['avg_keystroke_stress'], user_analysis['variability_factor']
        )
    )
    conn.commit()
    conn.close()

def save_nlp_response_analysis(response_data: dict):
    """Save per-question NLP and keystroke analysis."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO nlp_response_analysis 
           (user_id, session_id, question_id, response_text, sentiment_score, sentiment_label, 
            word_count, pronoun_ratio, negation_count, emotional_intensity, behavioral_score, keystroke_score) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            response_data['user_id'], response_data['session_id'], response_data['question_id'],
            response_data.get('response_text', ""), response_data['sentiment_score'], response_data['sentiment_label'],
            response_data['word_count'], response_data['pronoun_ratio'], response_data['negation_count'],
            response_data['emotional_intensity'], response_data['behavioral_score'], response_data['keystroke_score']
        )
    )
    conn.commit()
    conn.close()

def log_question_presentation(user_id: int, session_id: str, question_ids: list):
    """Log which questions were shown to the user this session."""
    conn = get_connection()
    cursor = conn.cursor()
    for q_id in question_ids:
        cursor.execute(
            "INSERT INTO user_question_history (user_id, session_id, question_id) VALUES (?, ?, ?)",
            (user_id, session_id, q_id)
        )
    conn.commit()
    conn.close()

def get_recent_question_ids(user_id: int, limit_sessions: int = 2):
    """Get question IDs from the last N sessions for this user."""
    conn = get_connection()
    cursor = conn.cursor()
    # Find the session IDs for the last N sessions
    cursor.execute(
        "SELECT DISTINCT session_id FROM user_question_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit_sessions)
    )
    sessions = [row[0] for row in cursor.fetchall()]
    
    if not sessions:
        return []
        
    # Get all question IDs for those sessions
    placeholders = ','.join(['?'] * len(sessions))
    cursor.execute(
        f"SELECT question_id FROM user_question_history WHERE session_id IN ({placeholders})",
        sessions
    )
    q_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return q_ids

def get_user_nlp_sessions(user_id: int, limit: int = 20):
    """Retrieve historical NLP session analysis for trends."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_session_analysis WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

