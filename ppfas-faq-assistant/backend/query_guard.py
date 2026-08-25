"""
query_guard.py — Pre-LLM classifier that decides whether a query is factual or
should be refused before any retrieval is attempted.

Classification categories:
  - FACTUAL   → pass to retrieval engine
  - ADVISORY  → return polite refusal
  - PII       → return PII refusal
  - COMPARATIVE → return polite refusal
  - PREDICTIVE → return polite refusal

Usage:
    from backend.query_guard import classify_query, QueryType
    result = classify_query("What is the expense ratio of PPFAS ELSS?")
"""
import re
from enum import Enum

class QueryType(Enum):
    FACTUAL = "factual"
    ADVISORY = "advisory"
    PII = "pii"
    COMPARATIVE = "comparative"
    PREDICTIVE = "predictive"

def classify_query(query: str) -> QueryType:
    query_lower = query.lower()
    
    # Check for PII (PAN / Aadhaar)
    pan_pattern = r'[A-Za-z]{5}\d{4}[A-Za-z]{1}'
    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    
    if re.search(pan_pattern, query) or re.search(aadhaar_pattern, query):
        return QueryType.PII
        
    # Check for Advisory/Comparative/Predictive
    advisory_keywords = [
        "should i", "invest in", "recommend", "advice", "good to invest"
    ]
    for kw in advisory_keywords:
        if kw in query_lower:
            return QueryType.ADVISORY
            
    comparative_keywords = ["better", "best", "compare", "vs", "versus"]
    for kw in comparative_keywords:
        if kw in query_lower:
            return QueryType.COMPARATIVE
            
    predictive_keywords = ["will returns", "go up", "go down", "forecast", "prediction", "future"]
    for kw in predictive_keywords:
        if kw in query_lower:
            return QueryType.PREDICTIVE
            
    return QueryType.FACTUAL
