"""
MindScale AI - Scoring Utilities
Helper functions for score calculation and display.
"""

import streamlit as st


def get_placeholder_score() -> int:
    """
    Return a placeholder wellness score for the dashboard.
    Uses session state to persist the value.
    """
    if "placeholder_score" not in st.session_state:
        st.session_state.placeholder_score = 72  # Default placeholder
    return st.session_state.placeholder_score


def set_placeholder_score(score: int) -> None:
    """Set the placeholder score in session state."""
    if 0 <= score <= 100:
        st.session_state.placeholder_score = score


def grade_from_score(score: float) -> str:
    """
    Map a 0–100 score to a letter grade.

    90–100 -> A
    75–89  -> B
    60–74  -> C
    40–59  -> D
    0–39   -> E
    """
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "E"


def combine_scores(
    emotion_score: float,
    questionnaire_score: float,
    nlp_score: float,
    voice_score: float,
) -> dict:
    """
    Combine individual module scores into a final score and grade.

    All inputs are expected to be in the 0–100 range.

    Formula:
        final_score =
            0.3 * emotion_score +
            0.2 * questionnaire_score +
            0.3 * nlp_score +
            0.2 * voice_score

    Returns:
        {
            "final_score": float,  # 0–100
            "grade": str,          # A–E
        }
    """
    # Clamp inputs to 0–100 to avoid surprises
    def _clamp(x: float) -> float:
        return max(0.0, min(100.0, float(x)))

    emotion = _clamp(emotion_score)
    questionnaire = _clamp(questionnaire_score)
    nlp = _clamp(nlp_score)
    voice = _clamp(voice_score)

    final_score = (
        0.3 * emotion
        + 0.2 * questionnaire
        + 0.3 * nlp
        + 0.2 * voice
    )
    # Round to 1 decimal place for nicer display
    final_score_rounded = round(final_score, 1)
    grade = grade_from_score(final_score_rounded)

    return {
        "final_score": final_score_rounded,
        "grade": grade,
    }


def compute_wellness_score(steps: float, sleep_hours: float, avg_hr: float) -> float:
    """
    Compute a 0–100 wellness score from Google Fit data.

    Weights:
    - Sleep consistency / duration: 40%
    - Activity level (steps): 35%
    - Heart rate stability: 25%
    """

    # Normalize steps: 0 at 0, 100 near 10k+ steps
    steps_norm = max(0.0, min(1.0, float(steps) / 10000.0))

    # Sleep: target 7–9 hours, drop off outside that range
    sleep = float(sleep_hours)
    if sleep <= 0:
        sleep_norm = 0.0
    elif 7 <= sleep <= 9:
        sleep_norm = 1.0
    elif sleep < 7:
        sleep_norm = max(0.0, (sleep - 4) / 3.0)  # 4h -> 0, 7h -> 1
    else:
        sleep_norm = max(0.0, (11 - sleep) / 2.0)  # 9h -> 1, 11h -> 0

    # Heart rate: assume 50–75 bpm is "calm"; penalize much higher/lower
    hr = float(avg_hr)
    if hr <= 0:
        hr_norm = 0.0
    elif 50 <= hr <= 75:
        hr_norm = 1.0
    elif hr < 50:
        hr_norm = max(0.0, (hr - 40) / 10.0)  # 40->0, 50->1
    else:
        hr_norm = max(0.0, (90 - hr) / 15.0)  # 75->1, 90->0

    score_0_1 = 0.4 * sleep_norm + 0.35 * steps_norm + 0.25 * hr_norm
    return round(score_0_1 * 100, 1)

