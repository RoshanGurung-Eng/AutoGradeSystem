
from .config import EXPECTED_KEYWORDS

def grade_text(final_text):
    """Grade based on keyword matching."""
    student_words = set(final_text.lower().split())
    matched = student_words & EXPECTED_KEYWORDS
    score = len(matched) / len(EXPECTED_KEYWORDS)
    return score, matched, EXPECTED_KEYWORDS - matched