import streamlit.components.v1 as components
import json

def nlp_assessment_wizard(question_list):
    """
    Renders a full 5-question wizard in a single HTML component.
    Captures keystroke events for each question and returns the full dataset.
    """
    
    questions_json = json.dumps(question_list)
    
    html_code = f"""
    <div id="nlp-wizard" style="color: #e5e7eb; font-family: sans-serif; background: #050816; padding: 20px; border-radius: 18px; border: 1px solid rgba(148,163,184,0.1);">
        <div id="progress-container" style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 5px;">
                <span id="step-label">Step 1 of 5</span>
                <span>Est. time: 4-5 mins</span>
            </div>
            <div style="width: 100%; height: 6px; background: #1f2933; border-radius: 3px;">
                <div id="progress-bar" style="width: 20%; height: 100%; background: #38bdf8; border-radius: 3px; transition: width 0.3s;"></div>
            </div>
        </div>

        <div id="question-container">
            <h3 id="question-text" style="font-size: 1.2rem; margin-bottom: 15px; min-height: 3em;">Loading...</h3>
            <textarea id="nlp_input" 
                style="width: 100%; height: 160px; background: #020617; color: #e5e7eb; 
                       border: 1px solid rgba(148, 163, 184, 0.4); border-radius: 12px; 
                       padding: 12px; font-size: 1rem; outline: none; resize: none;"
                placeholder="Share your thoughts..."></textarea>
            
            <div id="controls" style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
                <span id="char-count" style="font-size: 0.8rem; color: #9ca3af;">Words: 0</span>
                <button id="next_btn" 
                    style="background: linear-gradient(135deg, #38bdf8, #0ea5e9); color: white; 
                           border: none; border-radius: 999px; 
                           padding: 10px 25px; cursor: pointer; font-weight: 600; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3);">
                    Next Question →
                </button>
            </div>
        </div>
    </div>

    <script>
        const questions = {questions_json};
        let currentIdx = 0;
        const results = [];
        let currentEvents = [];

        const textarea = document.getElementById('nlp_input');
        const nextBtn = document.getElementById('next_btn');
        const qText = document.getElementById('question_text');
        const stepLabel = document.getElementById('step-label');
        const progressBar = document.getElementById('progress-bar');
        const charCount = document.getElementById('char-count');

        function updateUI() {{
            const q = questions[currentIdx];
            qText.innerText = q.text;
            stepLabel.innerText = `Step ${{currentIdx + 1}} of ${{questions.length}}`;
            progressBar.style.width = `${{((currentIdx + 1) / questions.length) * 100}}%`;
            textarea.value = "";
            currentEvents = [];
            nextBtn.innerText = currentIdx === questions.length - 1 ? "Submit Assessment ✓" : "Next Question →";
            updateWordCount();
        }}

        function updateWordCount() {{
            const text = textarea.value.trim();
            const words = text ? text.split(/\s+/).length : 0;
            charCount.innerText = `Words: ${{words}}`;
        }}

        textarea.addEventListener('input', updateWordCount);

        textarea.addEventListener('keydown', (e) => {{
            currentEvents.push({{ type: 'keydown', key: e.key, ts: Date.now() }});
        }});

        textarea.addEventListener('keyup', (e) => {{
            currentEvents.push({{ type: 'keyup', key: e.key, ts: Date.now() }});
        }});

        nextBtn.addEventListener('click', () => {{
            const text = textarea.value.trim();
            if (!text) {{
                alert("Please provide a response before moving forward.");
                return;
            }}

            // Save result for current question
            results.push({{
                question_id: questions[currentIdx].id,
                text: text,
                events: currentEvents
            }});

            if (currentIdx < questions.length - 1) {{
                currentIdx++;
                updateUI();
            }} else {{
                // Final submission
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: results
                }}, '*');
                
                document.getElementById('nlp-wizard').innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <h2 style="color: #38bdf8;">Assessment Complete!</h2>
                        <p>Processing your emotional insights...</p>
                    </div>
                `;
            }}
        }});

        // Initialize
        updateUI();
    </script>
    """
    
    return components.html(html_code, height=450)
