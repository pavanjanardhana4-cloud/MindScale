import re
import os
import nltk
from textblob import TextBlob

# Ensure NLTK data is available in a predictable location
nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
if not os.path.exists(nltk_data_path):
    os.makedirs(nltk_data_path, exist_ok=True)
if nltk_data_path not in nltk.data.path:
    nltk.data.path.append(nltk_data_path)

def ensure_nltk_data():
    requirements = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
        ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng')
    ]
    for path, package in requirements:
        try:
            nltk.data.find(path)
        except (LookupError, AttributeError):
            nltk.download(package, quiet=True)

ensure_nltk_data()

def analyze_text(text):
    """
    Analyzes text for sentiment, word count, sentence count,
    pronoun frequency, and negations.
    """
    if not text:
        return {
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "word_count": 0,
            "sentence_count": 0,
            "pronoun_ratio": 0.0,
            "negation_count": 0,
            "emotional_intensity": 0.0
        }
    
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity  # -1 to 1
    
    # Classification
    if sentiment > 0.1: label = "positive"
    elif sentiment < -0.1: label = "negative"
    else: label = "neutral"
    
    words = text.split()
    word_count = len(words)
    sentence_count = len(blob.sentences)
    
    # Pronoun frequency ("I", "me", "my")
    pronouns = re.findall(r"\b(i|me|my|mine|myself)\b", text.lower())
    pronoun_ratio = len(pronouns) / word_count if word_count > 0 else 0
    
    # Negation count
    negations = re.findall(r"\b(not|no|never|none|neither|nor|cannot|can't|don't|doesn't|didn't|won't|shan't|isn't|aren't|wasn't|weren't|hasn't|haven't|hadn't|couldn't|shouldn't|wouldn't|mightn't|mustn't)\b", text.lower())
    negation_count = len(negations)
    
    # Emotional intensity (simple heuristic based on subjectivity and word count)
    intensity = blob.sentiment.subjectivity 
    
    return {
        "sentiment_score": round(sentiment, 2),
        "sentiment_label": label,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "pronoun_ratio": round(pronoun_ratio, 2),
        "negation_count": negation_count,
        "emotional_intensity": round(intensity, 2)
    }
