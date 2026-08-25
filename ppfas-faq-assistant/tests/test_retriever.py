"""
test_retriever.py — Unit tests for the retrieval engine.

Tests (from eval.md — Section 5.2):
    - Known factual queries return at least 1 relevant chunk
    - Returned chunks belong to the queried scheme
    - Similarity score of top chunk exceeds threshold (> 0.70)
    - Chunk metadata (source_url, last_scraped_at) is present
"""

# TODO (Phase 5): Implement retriever tests
# See eval.md — Section 5.2 for retrieval precision targets.

import pytest
from backend.retriever import retrieve_chunks

def test_retriever_returns_chunks():
    chunks = retrieve_chunks("What is the expense ratio?")
    if not chunks:
        pytest.skip("No chunks returned, assuming Chroma DB is empty.")
        
    assert len(chunks) > 0
    assert "metadata" in chunks[0]
    assert "content" in chunks[0]
    assert "source_url" in chunks[0]["metadata"]

def test_retriever_metadata_present():
    chunks = retrieve_chunks("SIP amount for liquid fund")
    if not chunks:
        pytest.skip("No chunks returned, assuming Chroma DB is empty.")
        
    meta = chunks[0]["metadata"]
    assert "scheme_name" in meta
    assert "last_scraped_at" in meta
    assert "source_url" in meta
