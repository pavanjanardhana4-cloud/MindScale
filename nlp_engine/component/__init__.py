import os
import streamlit.components.v1 as components

# Create a _RELEASE flag to toggle between localized development and component-ready release.
# For now, we'll keep it simple and point directly to the local index.html.
_RELEASE = True

if not _RELEASE:
    # During development, point to the dev server.
    _component_func = components.declare_component(
        "nlp_keystroke_assessment",
        url="http://localhost:3001",
    )
else:
    # In release, point to the build directory.
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    _component_func = components.declare_component("nlp_keystroke_assessment", path=parent_dir)

def nlp_keystroke_assessment(questions, key=None):
    """
    Renders the NLP assessment wizard and returns the captured results.
    results: list of {question_id, text, events}
    """
    component_value = _component_func(questions=questions, key=key, default=None)
    return component_value
