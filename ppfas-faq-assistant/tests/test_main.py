import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ask_factual_query():
    response = client.post("/ask", json={"query": "What is the expense ratio of PPFAS Long Term Value Fund?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "source_url" in data
    assert "last_updated" in data
    assert data["is_refusal"] == False

def test_ask_advisory_query():
    response = client.post("/ask", json={"query": "Should I invest in PPFAS?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] == True
    # The exact string is defined in refusal_handler.py, we just check for is_refusal=True
    
def test_ask_comparative_query():
    response = client.post("/ask", json={"query": "Which fund gives better returns?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] == True

def test_ask_pii_query():
    response = client.post("/ask", json={"query": "My PAN is ABCDE1234F, which fund is good?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] == True

def test_status_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    assert "status" in response.json()
