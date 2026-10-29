import numpy as np

def calculate_negative_emotion(probs):
    """Calculate sum of sad + fear + angry."""
    return probs.get('sad', 0.0) + probs.get('fear', 0.0) + probs.get('angry', 0.0)

def calculate_dominant_emotion_distribution(emotion_log):
    """Calculate average distribution of emotions across the log."""
    if not emotion_log:
        return None
        
    all_probs = [entry['emotion_probs'] for entry in emotion_log]
    labels = all_probs[0].keys()
    
    distribution = {label: float(np.mean([p.get(label, 0.0) for p in all_probs])) for label in labels}
    dominant = max(distribution, key=distribution.get)
    
    return distribution, dominant

def calculate_emotion_variability(emotion_log):
    """Calculate variability index based on standard deviation of dominant emotion."""
    if not emotion_log or len(emotion_log) < 2:
        return 0.0
        
    all_probs = [entry['emotion_probs'] for entry in emotion_log]
    # Use sum of variances across all emotion labels as a proxy for variability
    variances = []
    for label in all_probs[0].keys():
        vals = [p.get(label, 0.0) for p in all_probs]
        variances.append(np.var(vals))
        
    return float(np.mean(variances))

def calculate_emotion_shift_from_baseline(baseline, emotion_log):
    """
    Compute Emotion Shift Score:
    average_negative_emotion - baseline_negative_emotion
    """
    if not baseline or not emotion_log:
        return 0.0
        
    baseline_neg = calculate_negative_emotion(baseline)
    
    all_probs = [entry['emotion_probs'] for entry in emotion_log]
    current_neg_avg = np.mean([calculate_negative_emotion(p) for p in all_probs])
    
    return float(current_neg_avg - baseline_neg)

def get_session_summary(baseline, emotion_log):
    """Return dictionary of summary metrics."""
    if not emotion_log:
        return None
        
    dist, dominant = calculate_dominant_emotion_distribution(emotion_log)
    variability = calculate_emotion_variability(emotion_log)
    shift = calculate_emotion_shift_from_baseline(baseline, emotion_log)
    
    # Ensure confidence score is within [0.0, 1.0]
    confidence = max(0.0, min(1.0, 1.0 - (variability * 5))) # Adjusted multiplier for normalized data
    
    return {
        "dominant_emotion": dominant,
        "variability_index": round(variability, 4),
        "shift_score": round(shift, 4),
        "confidence_score": round(confidence, 2),
        "distribution": dist
    }
