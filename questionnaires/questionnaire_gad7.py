"""
MindScale AI - GAD-7 (Generalized Anxiety Disorder 7-item scale)
7-item anxiety screening. Over the last 2 weeks.
"""

# Response options (same for all questions)
OPTIONS = [
    {"value": 0, "label": "Not at all"},
    {"value": 1, "label": "Several days"},
    {"value": 2, "label": "More than half the days"},
    {"value": 3, "label": "Nearly every day"},
]

QUESTIONS = [
    {"id": "q1", "text": "Feeling nervous, anxious, or on edge"},
    {"id": "q2", "text": "Not being able to stop or control worrying"},
    {"id": "q3", "text": "Worrying too much about different things"},
    {"id": "q4", "text": "Trouble relaxing"},
    {"id": "q5", "text": "Being so restless that it's hard to sit still"},
    {"id": "q6", "text": "Becoming easily annoyed or irritable"},
    {"id": "q7", "text": "Feeling afraid as if something awful might happen"},
]


def get_questionnaire() -> dict:
    """Return GAD-7 questionnaire definition."""
    return {
        "id": "gad7",
        "name": "GAD-7",
        "full_name": "Generalized Anxiety Disorder 7-item scale",
        "description": "Over the last 2 weeks, how often have you been bothered by the following?",
        "questions": QUESTIONS,
        "options": OPTIONS,
        "max_score": 21,
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
    Interpret GAD-7 score. Returns severity and recommendation.
    """
    if score <= 4:
        return {"severity": "Minimal", "level": "minimal", "recommendation": "No to low anxiety indicated."}
    elif score <= 9:
        return {"severity": "Mild", "level": "mild", "recommendation": "Watchful waiting; repeat GAD-7 at follow-up."}
    elif score <= 14:
        return {"severity": "Moderate", "level": "moderate", "recommendation": "Consider treatment plan, counseling, or follow-up."}
    else:
        return {"severity": "Severe", "level": "severe", "recommendation": "Active treatment is recommended. Please consult a healthcare provider."}

