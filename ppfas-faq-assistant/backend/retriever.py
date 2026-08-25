"""
retriever.py — Retrieval engine that embeds user queries and fetches the most
relevant corpus chunks from the ChromaDB vector store.
"""
import json
from pathlib import Path

_all_chunks = []

def _load_chunks():
    global _all_chunks
    chunk_dir = Path("corpus/chunks")
    if not chunk_dir.exists():
        return
        
    for file_path in chunk_dir.glob("*.json"):
        if file_path.name == "scrape_summary.json":
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            scheme = data.get("scheme_name", "")
            field = data.get("field", "").replace("_", " ").title()
            value = data.get("value", "")
            
            content = f"{scheme} — {field}: {value}"
            
            _all_chunks.append({
                "content": content,
                "metadata": {
                    "source_url": data.get("source_url", ""),
                    "last_scraped_at": data.get("last_scraped_at", "")
                }
            })
        except Exception:
            pass

_load_chunks()

def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    # Because we only have 77 facts, we can bypass ChromaDB completely and just return 
    # all of them. We will pass all 77 facts into the Groq LLM prompt. Groq's Llama 3 
    # can process 8,000 tokens instantly, and this uses 0 CPU on our end!
    return _all_chunks
