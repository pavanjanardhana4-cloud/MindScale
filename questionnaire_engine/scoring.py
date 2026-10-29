import json

def calculate_questionnaire_score(q_data, answers):
    """
    Calculate raw and weighted scores for a single questionnaire.
    """
    raw_score = 0
    weighted_score = 0
    max_possible_raw = 0
    
    for q in q_data['questions']:
        ans = answers.get(q['id'])
        if ans is None:
            continue
            
        if q['type'] in ['likert', 'radio', 'slider', 'multiple_choice']:
            val = float(ans)
            raw_score += val
            weighted_score += val * q.get('weight', 1.0)
            
            # Estimate max possible (simplified for PHQ-9 style where all have same max)
            if q['type'] == 'likert' and q.get('options'):
                max_possible_raw += max(opt['value'] for opt in q['options'])
            elif q['type'] == 'slider':
                max_possible_raw += q.get('max_val', 10)
            elif q['type'] == 'radio' and q.get('options'):
                max_possible_raw += max(opt['value'] for opt in q['options'])

    return {
        "raw": raw_score,
        "weighted": weighted_score,
        "max_raw": max_possible_raw
    }

def map_to_risk_band(q_data, score):
    """
    Map a numeric score to a risk band label.
    """
    risk_bands = q_data.get('risk_bands', [])
    for band in risk_bands:
        if band['min'] <= score <= band['max']:
            return band['label']
    return "Unknown"

def calculate_composite_index(schema, all_responses):
    """
    Calculate the final composite mental health index.
    all_responses: {q_id: {answers}}
    """
    individual_scores = {}
    risk_levels = {}
    composite_score = 0.0
    
    for q in schema['questionnaires']:
        q_id = q['id']
        answers = all_responses.get(q_id, {})
        if not answers:
            continue
            
        score_data = calculate_questionnaire_score(q, answers)
        individual_scores[q_id] = score_data['raw']
        risk_levels[q_id] = map_to_risk_band(q, score_data['raw'])
        
        # Calculate contribution to composite
        # We normalize the individual score to 0-100 first
        if score_data['max_raw'] > 0:
            percentage = (score_data['raw'] / score_data['max_raw']) * 100
            # PHQ-9/GAD-7 high score = high distress. 
            # We want an index where high = BETTER, so we invert it?
            # User says "Mental Health Index". Usually 0-100 where 100 is best.
            # Risk assessments are usually 0-max where max is worst.
            # Let's keep it as "Distress Index" or invert for "Wellness Index".
            # The user asked for "composite mental health index". 
            # I'll invert it: 100 - actual_distress_percentage
            wellness_basis = 100 - percentage
            composite_score += wellness_basis * q.get('composite_weight', 0)
        else:
            # For non-scored like NLP, maybe fixed contribution if completed?
            # Or just ignore if weight is 0.
            if q['id'] == 'nlp_open' and answers.get('reflection'):
                composite_score += 100 * q.get('composite_weight', 0)

    # Final overall risk
    if composite_score >= 80: overall_risk = "Excellent"
    elif composite_score >= 60: overall_risk = "Good"
    elif composite_score >= 40: overall_risk = "Fair"
    elif composite_score >= 20: overall_risk = "Caution"
    else: overall_risk = "Risk"

    return {
        "individual_scores": individual_scores,
        "risk_levels": risk_levels,
        "composite_score": round(composite_score, 2),
        "overall_risk": overall_risk
    }
