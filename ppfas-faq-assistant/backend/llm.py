"""
llm.py — LLM Answer Generator using the Groq API.
"""
import os
import json
from groq import AsyncGroq

async def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    if not context_chunks:
        return {
            "answer": "I don't have this information. Please visit: https://groww.in/mutual-funds/category/ppfas-mutual-fund",
            "source_url": "",
            "last_updated": ""
        }

    # Build context string
    context_str = ""
    for i, c in enumerate(context_chunks):
        meta = c["metadata"]
        context_str += f"[{i+1}] Fact: {c['content']} | Source URL: {meta.get('source_url', '')} | Last Updated: {meta.get('last_scraped_at', '')}\n"
    
    system_prompt = """
You are a facts-only mutual fund FAQ assistant for PPFAS schemes on Groww.
Rules:
- Answer using ONLY the retrieved context below. Do not use prior knowledge.
- Keep your answer to 3 sentences maximum.
- Do NOT provide investment advice, opinions, predictions, or comparisons.
- Format key metrics (like numbers, percentages, and dates) in **bold** using markdown.
- Note: "Parag Parikh Long Term Value Fund" is exactly the same as "Parag Parikh Flexi Cap Fund". Treat them interchangeably.
- If the context does not answer the question, output an answer indicating you don't know, and leave source_url empty.

You MUST reply in valid JSON format with EXACTLY three keys:
{
  "answer": "Your formatted answer text",
  "source_url": "The exact Source URL of the fund used to answer",
  "last_updated": "The exact Last Updated timestamp of the fund used to answer (UTC ISO format)"
}
"""

    try:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            return {"answer": "Error: GROQ_API_KEY environment variable is not set.", "source_url": "", "last_updated": ""}

        client = AsyncGroq(api_key=api_key)
        model = os.environ.get("GROQ_LLM_MODEL", "llama-3.1-8b-instant")
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=1024,
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        answer = data.get("answer", "I don't have this information.")
        source_url = data.get("source_url", "")
        last_updated_raw = data.get("last_updated", "")
        
        last_updated = last_updated_raw
        if last_updated_raw:
            try:
                from datetime import datetime, timedelta
                dt = datetime.strptime(last_updated_raw, "%Y-%m-%dT%H:%M:%SZ")
                dt_ist = dt + timedelta(hours=5, minutes=30)
                last_updated = dt_ist.strftime("%d-%m-%Y %H:%M:%S IST")
            except Exception:
                pass
                
        return {
            "answer": answer,
            "source_url": source_url,
            "last_updated": last_updated
        }
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "source_url": "", "last_updated": ""}
