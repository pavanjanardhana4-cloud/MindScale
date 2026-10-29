"""
MindScale AI - Questionnaire Loader
Loads and registers available questionnaires from questionnaire modules.
"""

from . import questionnaire_phq9
from . import questionnaire_gad7

# Registry: {questionnaire_id: module}
_MODULES = {
    "phq9": questionnaire_phq9,
    "gad7": questionnaire_gad7,
}


def load_questionnaires() -> dict:
    """
    Load all questionnaire modules and return registry.
    Returns {id: module} for modules that have get_questionnaire, calculate_score, interpret_score.
    """
    return _MODULES.copy()


def get_available_questionnaires() -> list[dict]:
    """
    Return list of questionnaire definitions (id, name, description) for selection.
    """
    result = []
    for module in _MODULES.values():
        definition = module.get_questionnaire()
        result.append({
            "id": definition["id"],
            "name": definition["name"],
            "full_name": definition.get("full_name", definition["name"]),
            "description": definition.get("description", ""),
        })
    return result


def get_questionnaire(questionnaire_id: str) -> dict | None:
    """
    Get full questionnaire definition by id.
    Returns None if not found.
    """
    module = _MODULES.get(questionnaire_id)
    if module is None:
        return None
    return module.get_questionnaire()


def calculate_score(questionnaire_id: str, responses: dict) -> int | None:
    """
    Calculate total score for a questionnaire.
    Returns None if questionnaire or module not found.
    """
    module = _MODULES.get(questionnaire_id)
    if module is None or not hasattr(module, "calculate_score"):
        return None
    return module.calculate_score(responses)


def interpret_score(questionnaire_id: str, score: int) -> dict | None:
    """
    Interpret score for a questionnaire.
    Returns None if questionnaire or module not found.
    """
    module = _MODULES.get(questionnaire_id)
    if module is None or not hasattr(module, "interpret_score"):
        return None
    return module.interpret_score(score)

