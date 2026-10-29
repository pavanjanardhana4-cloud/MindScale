import json
import streamlit as st
import time
from .logic import check_condition

class QuestionnaireRenderer:
    def __init__(self, schema_path, sampler=None):
        self.sampler = sampler
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
            
    def get_questionnaire(self, q_id):
        for q in self.schema['questionnaires']:
            if q['id'] == q_id:
                return q
        return None

    def render(self, q_id, button_label="Submit Assessment"):
        q_data = self.get_questionnaire(q_id)
        if not q_data:
            st.error(f"Questionnaire {q_id} not found.")
            return None

        st.subheader(q_data['title'])
        st.caption(f"Category: {q_data['category']}")
        
        # Initialize answers in session state if not present
        if f"answers_{q_id}" not in st.session_state:
            st.session_state[f"answers_{q_id}"] = {}
        
        answers = st.session_state[f"answers_{q_id}"]
        form_id = f"form_{q_id}"
        
        # Periodic sampling check (Disabled in snapshot model)
        if self.sampler:
            pass

        with st.container():
            for q in q_data['questions']:
                # Check conditional logic
                if not check_condition(answers, q.get("conditional_logic")):
                    continue
                
                # Render based on type
                if q['type'] == 'likert' or q['type'] == 'radio':
                    options = [opt['label'] for opt in q['options']]
                    values = {opt['label']: opt['value'] for opt in q['options']}
                    
                    # Find current index for default value
                    current_val = answers.get(q['id'])
                    index = 0
                    if current_val is not None:
                        for i, opt in enumerate(q['options']):
                            if opt['value'] == current_val:
                                index = i
                                break
                    
                    selection = st.radio(
                        q['text'],
                        options,
                        index=index,
                        key=f"{q_id}_{q['id']}"
                    )
                    
                    # Context-triggered sampling check
                    prev_val = answers.get(q['id'])
                    new_val = values[selection]
                    if new_val != prev_val:
                        answers[q['id']] = new_val
                        # If Depression/Anxiety and score >= 2, trigger high risk scoring
                        if q_id in ['depression_phq9', 'anxiety_gad7'] and new_val >= 2:
                            st.session_state.emotion_high_risk_active = True
                            st.session_state.emotion_high_risk_start = time.time()
                            # (Snapshot handled manually in UI if needed)
                    
                elif q['type'] == 'slider':
                    current_val = answers.get(q['id'], q.get('min_val', 0))
                    val = st.slider(
                        q['text'],
                        min_value=q.get('min_val', 0),
                        max_value=q.get('max_val', 10),
                        value=current_val,
                        key=f"{q_id}_{q['id']}"
                    )
                    answers[q['id']] = val
                    
                elif q['type'] == 'multiple_choice':
                    options = [opt['label'] for opt in q['options']]
                    values = {opt['label']: opt['value'] for opt in q['options']}
                    
                    current_val = answers.get(q['id'])
                    index = 0
                    if current_val is not None:
                         for i, opt in enumerate(q['options']):
                            if opt['value'] == current_val:
                                index = i
                                break
                                
                    selection = st.selectbox(
                        q['text'],
                        options,
                        index=index,
                        key=f"{q_id}_{q['id']}"
                    )
                    answers[q['id']] = values[selection]
                    
                elif q['type'] == 'text':
                    current_text = answers.get(q['id'], "")
                    text = st.text_area(
                        q['text'],
                        value=current_text,
                        key=f"{q_id}_{q['id']}"
                    )
                    answers[q['id']] = text

            if st.button(button_label, key=f"submit_{q_id}"):
                return answers
                
        return None
