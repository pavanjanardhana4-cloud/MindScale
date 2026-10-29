import numpy as np

def calculate_behavioral_score(sentiment_score, hesitation_ratio, correction_ratio, typing_speed_cps):
    """
    Computes a score from 0-100 indicating behavioral stress level for a single question.
    Higher = more stress/risk.
    
    Weights:
    - Sentiment (-1 to 1): Normalized, negative is higher stress. (40%)
    - Hesitation Ratio (0-1): Higher is more hesitation. (30%)
    - Correction Ratio (0-1): Higher is more backspacing. (20%)
    - Typing Speed: Normalized (avg human is 4-5 cps). (10%)
    """
    
    # Normalize Sentiment (-1 to 1 -> 0 to 1 where 1 is negative)
    sentiment_factor = (1 - sentiment_score) / 2
    
    # Normalize Typing Speed (0 to 10 cps -> 0 to 1 where 0 is high speed)
    # We penalize SLOW typing if combined with other factors
    speed_factor = max(0, min(1, (5 - typing_speed_cps) / 5)) if typing_speed_cps < 5 else 0
    
    # Weighted calculation
    score = (
        (sentiment_factor * 0.4) + 
        (hesitation_ratio * 0.3) + 
        (correction_ratio * 0.2) + 
        (speed_factor * 0.1)
    ) * 100
    
    return round(max(0, min(100, score)), 2)

def calculate_session_risk(question_analyses):
    """
    Aggregates per-question analyses into a session-level Emotional Risk Index.
    
    Weights:
    - Avg Sentiment: (40%)
    - Avg Keystroke Stress (Behavioral Stress Score): (40%)
    - Variability Factor: (20%)
    """
    if not question_analyses:
        return 0, 0, 0, 0
    
    # Extract metrics
    sentiments = [q['sentiment_score'] for q in question_analyses]
    behavioral_scores = [q['behavioral_score'] for q in question_analyses]
    
    avg_sentiment = np.mean(sentiments)
    avg_behavioral = np.mean(behavioral_scores)
    
    # Normalized avg sentiment for risk (1 is negative)
    sentiment_risk_factor = (1 - avg_sentiment) / 2
    
    # Behavioral risk (already 0-100)
    behavioral_risk_factor = avg_behavioral / 100
    
    # Variability (Std deviation of sentiment)
    # Higher variability = higher risk factor (instability)
    if len(sentiments) > 1:
        sentiment_std = np.std(sentiments)
        # Scale std (0-1 range roughly, std > 0.5 is high variability)
        variability_factor = min(1, sentiment_std * 2) 
    else:
        variability_factor = 0
        
    # Final Risk Index
    risk_index = (
        (sentiment_risk_factor * 0.4) + 
        (behavioral_risk_factor * 0.4) + 
        (variability_factor * 0.2)
    ) * 100
    
    return {
        "emotional_risk_index": round(max(0, min(100, risk_index)), 2),
        "avg_sentiment": round(avg_sentiment, 2),
        "avg_keystroke_stress": round(avg_behavioral, 2),
        "variability_factor": round(variability_factor, 2)
    }
