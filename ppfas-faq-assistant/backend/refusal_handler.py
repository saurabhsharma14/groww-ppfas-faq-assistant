"""
refusal_handler.py — Returns a templated response for non-factual queries.
"""
from backend.query_guard import QueryType

def get_refusal_message(query_type: QueryType) -> str:
    if query_type == QueryType.PII:
        return ("For your security, please do not share personal information like PAN or Aadhaar. "
                "I can only answer factual questions about PPFAS mutual funds.")
        
    return ("This assistant only answers factual questions about PPFAS mutual fund schemes "
            "on Groww — such as expense ratios, exit loads, or SIP minimums.\n"
            "For investment guidance, please consult a SEBI-registered advisor.\n"
            "Explore PPFAS funds at: https://groww.in/mutual-funds/category/ppfas-mutual-fund")
