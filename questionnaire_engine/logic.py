def check_condition(answers, condition):
    """
    Check if a question should be visible based on previous answers.
    Condition format: {"depends_on": "q1", "operator": "==", "value": 5}
    """
    if not condition:
        return True
    
    dep_id = condition.get("depends_on")
    operator = condition.get("operator")
    target_value = condition.get("value")
    
    if dep_id not in answers:
        return False
        
    actual_value = answers[dep_id]
    
    if operator == "==":
        return actual_value == target_value
    elif operator == "!=":
        return actual_value != target_value
    elif operator == ">":
        return actual_value > target_value
    elif operator == "<":
        return actual_value < target_value
    elif operator == ">=":
        return actual_value >= target_value
    elif operator == "<=":
        return actual_value <= target_value
        
    return True
