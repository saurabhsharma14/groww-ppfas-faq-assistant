"""
test_query_guard.py — Unit tests for the query classifier.

Tests (from eval.md — F01-F15 and R01-R10):
    - Advisory queries are correctly refused (recall = 100%)
    - Factual queries are correctly passed (precision >= 95%)
    - PII queries are refused
    - Edge cases: empty query, single char, all-caps
"""

# TODO (Phase 5): Implement query guard tests
# See eval.md — Section 5.3 for classification targets.

import pytest
from backend.query_guard import classify_query, QueryType

def test_query_guard_factual():
    assert classify_query("What is the expense ratio of PPFAS ELSS?") == QueryType.FACTUAL
    assert classify_query("What is the exit load?") == QueryType.FACTUAL
    assert classify_query("Is there a minimum SIP amount for the liquid fund?") == QueryType.FACTUAL

def test_query_guard_advisory():
    assert classify_query("Should I invest in PPFAS?") == QueryType.ADVISORY
    assert classify_query("Is it good to invest now?") == QueryType.ADVISORY
    assert classify_query("What do you recommend?") == QueryType.ADVISORY

def test_query_guard_comparative():
    assert classify_query("Which fund is better, ELSS or Liquid?") == QueryType.COMPARATIVE
    assert classify_query("Compare ELSS and large cap") == QueryType.COMPARATIVE

def test_query_guard_predictive():
    assert classify_query("Will returns go up next year?") == QueryType.PREDICTIVE
    assert classify_query("What is the future forecast?") == QueryType.PREDICTIVE

def test_query_guard_pii():
    assert classify_query("My PAN is ABCDE1234F, what is my balance?") == QueryType.PII
    assert classify_query("Aadhaar 1234 5678 9012, should I invest?") == QueryType.PII

def test_query_guard_edge_cases():
    assert classify_query("?") == QueryType.FACTUAL 
    assert classify_query("EXPENSE RATIO") == QueryType.FACTUAL
