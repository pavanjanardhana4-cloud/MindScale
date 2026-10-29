# MindScale AI 🛡️

A modular, multi-modal mental wellness assessment platform built with **Streamlit**. MindScale AI combines psychological questionnaires, facial emotion detection, NLP text analysis, voice analysis, and an AI chatbot to compute a composite **MindScale Composite Index (MCI)** — a single, unified mental wellness score updated in real-time after every module.

---

## ✨ Features

| Module | Description |
|---|---|
| 🏠 **Dashboard** | Personal wellness overview with MCI gauge, component breakdown, and trend charts |
| 📋 **Questionnaire** | Multi-step validated assessments (PHQ-9, GAD-7, etc.) with live facial emotion capture |
| 💬 **NLP Analysis** | Adaptive open-ended questioning with keystroke dynamics, sentiment & behavioral scoring |
| 🎙️ **Voice Analysis** | Speech recording with acoustic feature extraction and AI-powered emotion inference |
| 🤖 **AI Chatbot** | Context-aware mental health support powered by Groq LLaMA 3 with crisis detection |
| 📍 **Nearby Clinics** | Location-based hospital/clinic finder using OpenStreetMap |
| 🎯 **Goal Tracker** | Daily goal check-ins with effort scoring and consistency tracking |

---

## 🔍 Feature Details

### 🏠 Dashboard

The Dashboard is the central hub of MindScale AI and provides a comprehensive, real-time overview of the user's mental health journey.

- **MindScale Composite Index (MCI) Gauge** — A donut/gauge chart showing the current MCI score (0–100), computed as a weighted composite of all six wellness dimensions. The score updates every time the user completes any module.
- **AI-Generated Insight** — An auto-generated textual insight describing what the current MCI score means in plain language.
- **Component Breakdown (Bar Chart)** — A horizontal bar chart breaking down the MCI into its six sub-scores: Psychological Index, Emotional Insight Score, NLP Emotional Score, Voice Emotion Score, Goal Progress Score, and Chat Sentiment Score.
- **Daily Wellness Trend Line** — A time-series line chart showing how the MCI score has changed day by day.
- **Voice Analysis Subpanel** — An expandable section showing acoustic stability metrics (Energy Stability, Speech Rate Balance, Pitch Stability, Voice Sentiment) from the last voice session.
- **Behavioral & Linguistic Analytics** — Displays the latest NLP session metrics: Emotional Risk Index (%), Average Sentiment score, and Keystroke Stress (%), with a trend chart across the last 10 sessions.
- **Chat Sentiment** — Shows the average sentiment score derived from the most recent chatbot conversation.
- **Goal Progress** — Displays Goal Consistency (% of days checked in), Average Daily Effort Score (1–10), a table of recent goal activities, and a Goal Activity Sentiment Trend chart. Cross-module insights are shown (e.g., "High emotional risk + low goal effort detected — be kind to yourself.").
- **Emotional Insights (Facial Emotion)** — Displays the Dominant Emotion, Distress Shift from baseline, Analysis Confidence %, Emotion Stability bar, and an Average Emotion Distribution bar chart from the last 50 emotion snapshots.
- **Wellness Trends (Multi-module line chart)** — A combined line chart showing all score types (voice, questionnaire, NLP, chatbot, etc.) plotted over time.

---

### 📋 Questionnaire — Holistic Assessment Center

The Questionnaire module runs a multi-step psychological assessment using validated clinical instruments, with optional live facial emotion capture during the assessment.

- **Multi-Step Wizard** — Questionnaires are loaded from a central `schema.json` file and rendered one at a time. A progress bar shows which step the user is on (e.g., "Step 2 of 4"). The user can navigate forward or start over.
- **Validated Clinical Tools** — The schema includes standardized instruments such as PHQ-9 (depression), GAD-7 (anxiety), PSS (stress), and Burnout scales. Each question is rendered with its appropriate input type (radio, slider, etc.) as defined in the schema.
- **Facial Emotion Sampling (Optional)** — With user consent, the sidebar shows a live camera input. The user first captures a **Baseline Mood** snapshot. Subsequent periodic snapshots are captured throughout the assessment and tagged by question step. All emotion data is stored without images — only probability vectors (happy, sad, angry, fearful, disgusted, surprised, neutral) are saved to the database.
- **Composite Scoring** — Upon completing all questionnaire steps, a Composite Index is calculated across all instruments using the `questionnaire_engine`, producing a composite score and an overall risk label (Low / Moderate / High). Results are stored in `assessment_summary`.
- **Granular Storage** — Every individual question answer is also saved to `user_responses` for fine-grained historical tracking.
- **MCI Trigger** — After submission, the MindScale Composite Index is automatically recalculated and saved for the day.

---

### 💬 NLP Analysis — Behavioral & Linguistic Assessment

The NLP module goes beyond structured questionnaires by analysing *how* users express themselves in free-form text, as well as *how they type*.

- **Adaptive Question Selection** — 5 reflective open-ended questions are selected per session from a question bank (`questions.json`). The selection algorithm avoids repeating questions from the last 2 sessions (tracked via `user_question_history`), ensuring fresh prompts every time.
- **Custom Keystroke Tracking Component** — A custom Streamlit JS component captures per-keystroke timestamps, hesitation events, correction/delete events, and typing speed in real time — without ever storing the text externally. This data is sent back to Python when the form is submitted.
- **NLP Metrics (per response)**:
  - **Sentiment Score & Label** — Polarity score (–1 to +1) and label (positive/neutral/negative) computed with TextBlob.
  - **Word Count** — Length of the response.
  - **Pronoun Ratio** — Ratio of first-person pronouns ("I", "me", "my") to total words; a clinical indicator of self-focus and rumination.
  - **Negation Count** — Number of negation words ("not", "never", "can't"), linked to cognitive distortions.
  - **Emotional Intensity** — A custom intensity score derived from word-level affect.
- **Keystroke Metrics (per response)**:
  - **Hesitation Ratio** — Proportion of pauses > threshold during typing, indicating cognitive load or uncertainty.
  - **Correction Ratio** — Frequency of backspace/delete events, indicating self-editing or distress.
  - **Average Typing Speed** — Characters per second.
- **Behavioral Stress Score** — A per-question composite derived from sentiment polarity, hesitation ratio, correction ratio, and typing speed.
- **Session-Level Aggregation** — Across all 5 questions, a session summary is computed:
  - **Emotional Risk Index (%)** — Aggregated risk score for the session.
  - **Average Sentiment** — Mean sentiment across all responses.
  - **Average Keystroke Stress (%)** — Mean keystroke stress across responses.
  - **Variability Factor** — Variance in sentiment between responses, indicating emotional inconsistency.
- **Results Display** — After submission, per-response breakdowns are shown in expandable sections (question text, answer, sentiment label, keystroke stress, word count).
- **MCI Trigger** — Session results are saved and the MCI is recalculated immediately.

---

### 🎙️ Voice Analysis

The Voice module analyses acoustic features of a short voice recording to infer stress levels and emotional sentiment.

- **In-Browser Recording** — Uses `audio-recorder-streamlit` to capture audio directly from the microphone in the browser. The user speaks for 5–10 seconds and can listen back before running analysis.
- **Acoustic Feature Extraction (librosa)**:
  - **Pitch (Mean Hz)** — Fundamental frequency estimated using `librosa.yin()`. Higher or more erratic pitch can correlate with stress or anxiety.
  - **Energy (RMS Mean)** — Root Mean Square energy, indicating vocal intensity and arousal level.
  - **Speech Rate Proxy (ZCR)** — Zero-Crossing Rate × 100 as an estimate of speech tempo.
- **Stress Score (0–100)** — A composite stress score is computed from normalized energy (40%), speech rate (40%), and pitch (20%), mapped to three levels: **Low** (< 35), **Moderate** (35–70), **High** (> 70).
- **AI Transcription & Emotion Detection** — If the Whisper speech model and emotion model are loaded:
  - The audio is transcribed to text using **OpenAI Whisper** (via Hugging Face Transformers).
  - The transcribed text is classified into emotions (happy, sad, angry, anxious, neutral, surprised) using a Transformer-based emotion classifier.
- **Contextual Insights** — A personalized message is shown based on the detected emotion and stress level (e.g., a calming suggestion for "sad/angry/anxious" detections, an encouraging message for "happy").
- **MCI Trigger** — The voice stress score is saved and the MCI is recalculated.

---

### 🤖 AI Chatbot

A conversational mental health support assistant powered by Groq's LLaMA 3 model, with awareness of the user's clinical context gathered from other modules.

- **Context-Aware Responses** — Before each reply, the chatbot reads the user's latest scores from all modules (questionnaire risk, NLP emotional risk, voice stress, goal consistency) and injects this clinical context into the system prompt. This allows the AI to give personalised, relevant responses rather than generic ones.
- **Real-Time Emotion Detection** — Every user message is passed through a Transformer-based emotion classifier. The detected emotion (happy, sad, anxious, angry, surprised, neutral) is included in the system prompt so the LLM can adapt its tone accordingly.
- **Crisis / Suicide Risk Detection** — A keyword-based `suicide_help_check()` function scans each user message. If a crisis phrase is detected, the chatbot immediately responds with empathetic support and India-specific helpline numbers (Kiran: 1800-599-0019, AASRA: +91-22-27546669) instead of sending the message to the LLM.
- **Session Mood Insights Panel** — An expandable panel shows all emotions detected during the current conversation session and the running average sentiment score (0.0–1.0), visualised as a progress bar.
- **Periodic Sentiment Saving** — Every 3 or more exchanges, the average chat sentiment is saved to the `scores` table and the MCI is recalculated in the background.
- **LLM Backend** — Powered by `llama-3.1-8b-instant` via the Groq API for fast inference. Falls back gracefully if the API key is not configured.
- **Persistent Chat History** — Chat messages are stored in Streamlit session state for the duration of the session.

---

### 📍 Nearby Clinics

Helps users find mental health hospitals and clinics near them, entirely without any proprietary mapping APIs.

- **Free-Text Location Input** — The user enters any location (city name, address, landmark, or PIN code). The input is geocoded to (latitude, longitude) using the **OpenStreetMap Nominatim API**.
- **Adjustable Search Radius** — A slider lets the user set the search radius from 1 km to 20 km (default 5 km).
- **Hospital Query via Overpass API** — Uses the Overpass QL API to fetch all `amenity=hospital` nodes, ways, and relations within the specified radius. Supports all three OSM element types to maximise coverage.
- **Distance Calculation (Haversine)** — Great-circle distances between the user's location and each hospital are computed using the Haversine formula and displayed in kilometres.
- **Address Resolution** — If a hospital's address tags are missing from OSM data, a reverse-geocode call to Nominatim is made (limited to 15 hospitals to respect API rate limits).
- **Results Display** — Hospitals are listed in order of proximity, showing name, distance, and address. Summary metrics (total hospitals found, closest distance) are shown at the top.

---

### 🎯 Goal Tracker

Keeps users accountable to their personal wellness goals through a structured daily check-in that also feeds into the MCI.

- **Goal Setting at Registration** — When creating an account, users set a **Short-Term Goal** (3–6 months) and a **Long-Term Goal** (3–5 years). These are stored in the `users` table and displayed on the Goal Tracker page.
- **Daily Check-In Gate** — The check-in is enforced every day. If a user has not checked in today, they are shown the check-in form before accessing any other module. A sidebar warning ("⏰ Daily Goal Check-In Pending") is also displayed.
- **Check-In Form**:
  - **Did you work on your goal today?** — Radio selection: Yes / Partially / No.
  - **What did you do today?** — A short text field (max 150 characters) for a brief activity description.
  - **Effort Score (1–10)** — A slider to self-rate effort level for the day.
- **Progress Metrics** — The Goal Tracker page (accessible from the sidebar) shows:
  - **Goal Consistency (%)** — Percentage of days with a completed check-in.
  - **Average Daily Effort Score (out of 10)**.
  - The user's current short-term and long-term goals displayed as info cards.
- **MCI Trigger** — After each check-in, the effort score and activity sentiment are saved and the MCI is recalculated immediately.

---

## 🧮 MindScale Composite Index (MCI)

The MCI is a daily composite wellness score (0–100) computed from six weighted sub-scores:

| Component | Source Module |
|---|---|
| Psychological Index | Questionnaire (PHQ-9, GAD-7, etc.) |
| Emotional Insight Score | Facial Emotion Detection during assessments |
| NLP Emotional Score | Sentiment, negation, pronoun ratio, keystroke stress |
| Voice Emotion Score | Acoustic stress score from voice recording |
| Goal Progress Score | Daily check-in effort & activity sentiment |
| Chat Sentiment Score | Emotion detected during chatbot conversations |

The MCI is recalculated and saved after **every module submission**, so the dashboard always reflects the latest data.

---

## 🗂️ Project Structure

```
mindscale_v5/
├── app.py                        # Main entry point & global UI/routing
│
├── auth/
│   ├── auth.py                   # Email/password auth, bcrypt hashing, session management
│   └── google_fit_auth.py        # Google Fit OAuth integration
│
├── database/
│   └── db.py                     # SQLite schema, auto-migrations & all DB helper functions
│
├── pages/
│   ├── dashboard.py              # MCI dashboard & trend visualizations
│   ├── questionnaire.py          # Multi-step assessment wizard
│   ├── nlp_analysis.py           # NLP open-ended Q&A interface
│   ├── voice_analysis.py         # Audio recording & emotion inference
│   ├── chatbot.py                # Groq LLaMA 3 chatbot with crisis detection
│   ├── nearby_clinics.py         # OpenStreetMap-powered clinic locator
│   └── goal_tracker.py           # Goal setting & daily check-in
│
├── emotion_engine/
│   ├── emotion_model.py          # DeepFace wrapper for emotion prediction
│   ├── emotion_sampler.py        # Frame sampling & DB logging logic
│   ├── emotion_scoring.py        # Converts raw emotion probabilities → wellness score
│   └── camera_manager.py         # Webcam consent & lifecycle management
│
├── nlp_engine/
│   ├── nlp_service.py            # Sentiment, pronoun ratio, negation count, intensity
│   ├── keystroke_tracker.py      # Keystroke timing capture logic
│   ├── keystroke_analytics.py    # Aggregated keystroke stress calculation
│   ├── scoring.py                # Behavioral score & session risk computation
│   ├── selection_service.py      # Adaptive question selection (avoids recent repeats)
│   ├── questions.json            # Open-ended question bank
│   └── component/                # Custom Streamlit JS component for keystroke capture
│
├── questionnaire_engine/
│   ├── renderer.py               # Questionnaire UI renderer
│   ├── scoring.py                # Per-questionnaire score calculator
│   ├── logic.py                  # Questionnaire routing/flow logic
│   └── schema.json               # All questionnaire definitions (PHQ-9, GAD-7, …)
│
├── utils/
│   ├── scoring_service.py        # MCI computation & daily saving
│   ├── ai_service.py             # Whisper, emotion model loading, Groq client, context builder
│   ├── goal_service.py           # Goal progress & daily tracking helpers
│   ├── google_fit_service.py     # Google Fit data fetching
│   └── scoring.py                # Shared scoring utilities
│
├── questionnaires/               # Additional questionnaire data/assets
├── .streamlit/                   # Streamlit theme & server config
├── requirements.txt              # Python dependencies
├── packages.txt                  # System-level packages (for Streamlit Cloud)
└── nltk.txt                      # NLTK corpora to auto-download on deploy
```

---

## 🗄️ Database Schema

MindScale uses a local **SQLite** database (`MindScale.db`) with automatic schema migrations on startup.

| Table | Purpose |
|---|---|
| `users` | Email-based accounts with bcrypt-hashed passwords and goal fields |
| `scores` | Individual module score records (voice, chat, questionnaire, etc.) |
| `questionnaire_responses` | Full questionnaire submission history |
| `user_responses` | Per-question granular answer tracking |
| `assessment_summary` | Composite assessment results & risk labels |
| `emotion_data` | Facial emotion probability snapshots (no images stored) |
| `nlp_response_analysis` | Per-question NLP + keystroke metrics |
| `user_session_analysis` | Session-level emotional risk index |
| `mindscale_scores` | Daily MindScale Composite Index (MCI) records |
| `daily_goal_tracking` | Daily goal check-in, effort score & activity sentiment |
| `user_question_history` | NLP question rotation history for adaptive selection |
| `google_fit_tokens` | Stored Google Fit OAuth tokens |
| `oauth_pending_states` | Temporary OAuth state for redirect flow |

---

## ⚙️ Setup

### Prerequisites

- Python 3.10+
- A webcam (for emotion detection during assessments)
- A microphone (for voice analysis)
- A **Groq API key** (for the chatbot — get one free at [console.groq.com](https://console.groq.com))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Shashank3366/mindscale_v5.git
cd mindscale_v5

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure API keys
#    Create .streamlit/secrets.toml:
#
#    [secrets]
#    GROQ_API_KEY   = "your-groq-key-here"
#    GEMINI_API_KEY = "your-gemini-key-here"   # optional

# 5. Run the app
streamlit run app.py
```

The app will open at **http://localhost:8501** in your browser. The SQLite database is created automatically on first run.

---

## 🚀 Usage

1. **Register** with your email and password and set your short-term and long-term wellness goals.
2. On first login (and every subsequent day), complete the **Daily Goal Check-In** — this is required before accessing other modules.
3. Use the **sidebar** to navigate between modules:
   - Start with **Questionnaire** for a baseline psychological assessment. Optionally enable the webcam for emotion capture during the assessment.
   - Use **NLP Analysis** to answer 5 reflective open-ended questions. Type naturally — your responses and typing patterns are both analysed.
   - Use **Voice Analysis** to record a short voice note for acoustic stress and sentiment analysis.
   - Chat with the **AI Chatbot** for supportive, context-aware mental health conversations.
   - Use **Nearby Clinics** to find hospitals near your location.
4. View your **Dashboard** for a unified overview of your MCI score, trends, and behavioral insights.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **App Framework** | Streamlit ≥ 1.28 |
| **Database** | SQLite (Python `sqlite3`) |
| **Emotion Detection** | DeepFace + OpenCV (headless) |
| **Voice Processing** | librosa, soundfile, audio-recorder-streamlit |
| **Speech-to-Text** | OpenAI Whisper (via Hugging Face Transformers) |
| **Emotion Classification** | Hugging Face Transformers (text emotion model) |
| **NLP** | TextBlob, custom linguistic feature extraction |
| **LLM / Chatbot** | Groq API (`llama-3.1-8b-instant`) |
| **Visualisations** | Plotly |
| **Auth** | bcrypt password hashing |
| **Clinic Finder** | OpenStreetMap Nominatim + Overpass API |
| **Deep Learning Backend** | TensorFlow-CPU 2.15 + TF-Keras 2.15, PyTorch |

---

## ☁️ Deploying to Streamlit Cloud

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set `app.py` as the entry point.
4. Add your API keys under **Secrets** in the Streamlit Cloud dashboard.
5. System-level dependencies in `packages.txt` and NLTK corpora in `nltk.txt` are installed automatically by Streamlit Cloud.

---

## 📄 License

This project is for educational and research purposes.
