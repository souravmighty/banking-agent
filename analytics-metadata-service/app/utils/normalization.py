import re
from typing import List, Set

def normalize_name(name: str) -> str:
    """Normalizes table, column, or metric names by stripping whitespace and lowercasing."""
    if not name:
        return ""
    return name.strip().lower()

def tokenize_text(text: str) -> Set[str]:
    """Tokenizes text into a set of lowercased alphanumeric words."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    # Also break down snake_case tokens
    expanded = set(words)
    for w in words:
        if "_" in w:
            for sub in w.split("_"):
                if sub:
                    expanded.add(sub)
    return expanded

def compute_text_relevance(query_tokens: Set[str], target_text: str) -> float:
    """Computes a simple token overlap relevance score between query tokens and target text."""
    if not query_tokens or not target_text:
        return 0.0
    target_tokens = tokenize_text(target_text)
    if not target_tokens:
        return 0.0
    intersection = query_tokens.intersection(target_tokens)
    if not intersection:
        return 0.0
    score = len(intersection) / len(query_tokens)
    # Extra boost if exact query is a substring
    return min(1.0, score)
