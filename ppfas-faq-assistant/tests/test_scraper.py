"""
test_scraper.py — Unit tests for the Groww scraper.

Tests:
    - All 7 URLs return a valid response
    - All required fields are extracted per scheme
    - source_url matches the input URL
    - last_scraped_at is a valid ISO timestamp
    - No chunks from non-Groww domains
"""

# TODO (Phase 5): Implement scraper tests
# See eval.md — Section 5.1 for test criteria.

import os
import json
import datetime
from pathlib import Path
import pytest
from scraper.scrape import CHUNKS_DIR, validate_chunks

def test_validate_chunks_passes():
    if not os.path.exists(CHUNKS_DIR):
        pytest.skip("Chunks directory not found. Scraper needs to run first.")
    
    files = list(Path(CHUNKS_DIR).glob("*.json"))
    if len(files) < 10:
        pytest.skip("Not enough chunks. Scraper needs to run first.")
        
    assert validate_chunks() == True

def test_chunk_format_and_domain():
    if not os.path.exists(CHUNKS_DIR):
        pytest.skip("Chunks directory not found.")
        
    for chunk_file in Path(CHUNKS_DIR).glob("*__*.json"):
        with open(chunk_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert "scheme_name" in data
        assert "field" in data
        assert "value" in data
        assert "source_url" in data
        assert "last_scraped_at" in data
        
        # Domain check
        assert data["source_url"].startswith("https://groww.in/")
        
        # Date format check
        try:
            dt = datetime.datetime.strptime(data["last_scraped_at"], "%Y-%m-%dT%H:%M:%SZ")
            assert dt is not None
        except ValueError:
            pytest.fail(f"Invalid timestamp format in {chunk_file.name}")
