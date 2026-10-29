"""
MindScale AI - PHQ-9 (Patient Health Questionnaire)
9-item depression screening. Over the last 2 weeks.
"""

# Response options (same for all questions)
OPTIONS = [
    {"value": 0, "label": "Not at all"},
    {"value": 1, "label": "Several days"},
    {"value": 2, "label": "More than half the days"},
    {"value": 3, "label": "Nearly every day"},
]

QUESTIONS = [
    {"id": "q1", "text": "Little interest or pleasure in doing things"},
    {"id": "q2", "text": "Feeling down, depressed, or hopeless"},
    {"id": "q3", "text": "Trouble falling or staying asleep, or sleeping too much"},
    {"id": "q4", "text": "Feeling tired or having little energy"},
    {"id": "q5", "text": "Poor appetite or overeating"},
    {"id": "q6", "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down"},
    {"id": "q7", "text": "Trouble concentrating on things, such as reading the newspaper or watching television"},
    {"id": "q8", "text": "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual"},
    {"id": "q9", "text": "Thoughts that you would be better off dead, or of hurting yourself in some way"},
]


def get_questionnaire() -> dict:
    """Return PHQ-9 questionnaire definition."""
    return {
        "id": "phq9",
        "name": "PHQ-9",
        "full_name": "Patient Health Questionnaire-9",
        "description": "A 9-item depression screening. Over the last 2 weeks, how often have you been bothered by the following?",
        "questions": QUESTIONS,
        "options": OPTIONS,
        "max_score": 27,
    }


def calculate_score(responses: dict) -> int:
    """
    Calculate total score from responses.
    responses: {question_id: value} e.g. {"q1": 1, "q2": 2, ...}
    """
    total = 0
    for q in QUESTIONS:
        total += responses.get(q["id"], 0)
    return total


def interpret_score(score: int) -> dict:
    """
    Interpret PHQ-9 score. Returns severity and recommendation.
    """
    if score <= 4:
        return {"severity": "Minimal", "level": "minimal", "recommendation": "No significant depression indicated."}
    elif score <= 9:
        return {"severity": "Mild", "level": "mild", "recommendation": "Watchful waiting; repeat PHQ-9 at follow-up."}
    elif score <= 14:
        return {"severity": "Moderate", "level": "moderate", "recommendation": "Consider treatment plan, counseling, or follow-up."}
    elif score <= 19:
        return {"severity": "Moderately severe", "level": "moderately_severe", "recommendation": "Active treatment is recommended."}
    else:
        return {"severity": "Severe", "level": "severe", "recommendation": "Immediate treatment is recommended. Please consult a healthcare provider."}

