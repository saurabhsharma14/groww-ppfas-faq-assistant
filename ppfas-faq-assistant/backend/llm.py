"""
llm.py — LLM Answer Generator using the Groq API.
"""
import os
from groq import Groq

def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    if not context_chunks:
        return {
            "answer": "I don't have this information. Please visit: https://groww.in/mutual-funds/category/ppfas-mutual-fund",
            "source_url": "",
            "last_updated": ""
        }

    context_str = "\n".join([f"- {c['content']}" for c in context_chunks])
    
    system_prompt = """
You are a facts-only mutual fund FAQ assistant for PPFAS schemes on Groww.
Rules:
- Answer using ONLY the retrieved context below. Do not use prior knowledge.
- Keep your answer to 3 sentences maximum.
- Do NOT provide investment advice, opinions, predictions, or comparisons.
- Do NOT append any source links, URLs, or timestamps to your answer. We handle that in the UI.
- Format key metrics (like numbers, percentages, and dates) in **bold** using markdown.
- Note: "Parag Parikh Long Term Value Fund" is exactly the same as "Parag Parikh Flexi Cap Fund". Treat them interchangeably.
- If the context does not answer the question, say:
    "I don't have this information. Please visit: https://groww.in/mutual-funds/category/ppfas-mutual-fund"
"""
    
    # We will let the LLM substitute these using the top chunk if it generates an answer.
    # But since we want to output exactly 1 source and 1 last_updated in the response payload too,
    # we'll pick the top chunk's metadata.
    top_meta = context_chunks[0]["metadata"]
    source_url = top_meta.get("source_url", "")
    last_updated_raw = top_meta.get("last_scraped_at", "")
    
    last_updated = last_updated_raw
    if last_updated_raw:
        try:
            from datetime import datetime, timedelta
            dt = datetime.strptime(last_updated_raw, "%Y-%m-%dT%H:%M:%SZ")
            dt_ist = dt + timedelta(hours=5, minutes=30)
            last_updated = dt_ist.strftime("%d-%m-%Y %H:%M:%S")
        except Exception:
            pass
    
    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return {
                "answer": "Error: GROQ_API_KEY environment variable is not set.",
                "source_url": "",
                "last_updated": ""
            }

        client = Groq(api_key=api_key)
        # fallback to llama-3.1-8b-instant if not set
        model = os.environ.get("GROQ_LLM_MODEL", "llama-3.1-8b-instant")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
            ],
            max_tokens=4096,
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        if not content:
            # Some models might put everything in reasoning or return empty
            answer = "The retrieved context answers this, but the model returned an empty response."
        else:
            answer = content.strip()
        
        return {
            "answer": answer,
            "source_url": source_url,
            "last_updated": last_updated
        }
    except Exception as e:
        return {
            "answer": f"An error occurred while generating the answer: {str(e)}",
            "source_url": "",
            "last_updated": ""
        }
