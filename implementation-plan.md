# Implementation Plan: Mutual Fund FAQ Assistant (RAG-Based)

> ⚠️ **"Facts-only. No investment advice."**

---

## Overview

This document outlines a **phased, step-by-step implementation plan** for building the PPFAS Mutual Fund FAQ Assistant. The system uses a RAG (Retrieval-Augmented Generation) architecture grounded exclusively in Groww website content.

**Total Estimated Phases:** 7  
**AMC in Scope:** PPFAS — Parag Parikh Financial Advisory Services  
**Source:** [groww.in](https://groww.in) only

---

## Phase 0 — Project Setup & Environment

### Step 0.1 — Initialize Project Structure

Create the following folder layout:

```
ppfas-faq-assistant/
├── scraper/
│   ├── scrape.py
│   └── urls.py
├── corpus/
│   └── chunks/          # Stored text chunks (JSON)
├── embeddings/
│   └── store/           # ChromaDB or FAISS index files
├── backend/
│   ├── main.py          # FastAPI app
│   ├── retriever.py
│   ├── query_guard.py
│   └── llm.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   ├── test_scraper.py
│   ├── test_query_guard.py
│   └── test_retriever.py
├── README.md
├── .env.example
└── requirements.txt
```

### Step 0.2 — Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux
pip install -r requirements.txt
```

**`requirements.txt` (initial):**
```
playwright
beautifulsoup4
groq
sentence-transformers
chromadb
fastapi
uvicorn
python-dotenv
httpx
```

> **Note:** Groq provides LLM inference only — it does not offer an embedding API.
> Embeddings are generated **locally** using `sentence-transformers` (free, no additional API key required).

### Step 0.3 — Configure Environment Variables

Create `.env` from `.env.example`:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_LLM_MODEL=openai/gpt-oss-120b
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./embeddings/store
```

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key from [console.groq.com](https://console.groq.com/keys) |
| `GROQ_LLM_MODEL` | Groq model — `llama-3.1-8b-instant` (fast) or `llama-3.3-70b-versatile` (accurate) |
| `EMBEDDING_MODEL` | Local sentence-transformers model name |
| `CHROMA_PERSIST_DIR` | Path to ChromaDB persistence directory |

> [!IMPORTANT]
> Never commit `.env` to version control. Add it to `.gitignore` immediately.

---

## Phase 1 — Web Scraper

### Step 1.1 — Define Target URLs

Create `scraper/urls.py` with all 7 PPFAS scheme URLs:

```python
PPFAS_URLS = [
    "https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-elss-tax-saver-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-conservative-hybrid-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-liquid-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-arbitrage-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-dynamic-asset-allocation-fund-direct-growth",
]
```

### Step 1.2 — Build the Scraper

- Use **Playwright** (for JavaScript-rendered pages) or **BeautifulSoup** (for static HTML)
- Extract the following fields per scheme page:

| Field | Notes |
|-------|-------|
| Expense Ratio | Under fund details section |
| Exit Load | Policy and duration |
| Minimum SIP Amount | Monthly SIP minimum |
| Minimum Lump Sum | One-time investment minimum |
| Riskometer Classification | e.g., Very High / High |
| Benchmark Index | e.g., Nifty 500 TRI |
| ELSS Lock-in Period | Only for ELSS scheme |
| Fund Manager(s) | Name(s) |
| AUM | Assets under management |
| Fund Category | e.g., Flexi Cap / ELSS |

- Store each chunk as a JSON object:

```json
{
  "scheme_name": "Parag Parikh Long Term Value Fund",
  "field": "expense_ratio",
  "value": "0.58%",
  "source_url": "https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth",
  "last_scraped_at": "2026-08-25T08:00:00Z"
}
```

### Step 1.3 — Validate Scraper Output

- Run scraper against all 7 URLs
- Verify all target fields are captured
- Log missing or unparsed fields for debugging

### Step 1.4 — Schedule Corpus Refresh

- Set up a **cron job** or **GitHub Actions workflow** to re-run scraper nightly
- Overwrite existing chunks with fresh data
- Log `last_scraped_at` timestamp per field

---

## Phase 2 — Corpus Ingestion & Vector Store

### Step 2.1 — Text Chunking

- Each scraped fact = one chunk (fine-grained, field-level chunking)
- Prepend scheme name to chunk text for context:

```
"Parag Parikh Long Term Value Fund — Expense Ratio: 0.58% (Direct Plan)"
```

### Step 2.2 — Generate Embeddings

- Use **`sentence-transformers`** locally with model `all-MiniLM-L6-v2` (fast, free, no API key)
- Embed each chunk text
- Store embedding vector + metadata in ChromaDB

```python
collection.add(
    documents=[chunk["value"]],
    metadatas=[{
        "scheme_name": chunk["scheme_name"],
        "field": chunk["field"],
        "source_url": chunk["source_url"],
        "last_scraped_at": chunk["last_scraped_at"]
    }],
    ids=[unique_id]
)
```

### Step 2.3 — Validate Vector Store

- Run a test similarity search for known queries
- Verify top-K results return correct scheme facts
- Check metadata fields are correctly stored and retrievable

---

## Phase 3 — Backend (FastAPI)

### Step 3.1 — Query Guard (Classifier)

Build `backend/query_guard.py` to classify queries **before** any retrieval:

| Query Type | Classification | Action |
|------------|---------------|--------|
| "What is the expense ratio of…" | ✅ Factual | Pass to retriever |
| "Should I invest in…" | 🚫 Advisory | Return refusal |
| "Which fund is better?" | 🚫 Comparative | Return refusal |
| "Will returns go up?" | 🚫 Predictive | Return refusal |
| Contains PAN/Aadhaar patterns | 🚫 PII | Return PII refusal |

- Implement using a **keyword/regex ruleset** first (fast, no LLM cost)
- Optionally upgrade to a small classifier LLM call for edge cases

### Step 3.2 — Retrieval Engine

Build `backend/retriever.py`:

| **Chunking strategy** | Semantic chunking by section (e.g., one chunk per fund fact) |
| **Embedding model** | `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API needed) |
| **Vector DB** | ChromaDB (local) or FAISS for lightweight deployment |
| **Metadata stored** | `source_url`, `scheme_name`, `last_scraped_at`, `section_title` |

1. Embed the user query using the same embedding model
2. Run similarity search against ChromaDB (top-K = 3–5 chunks)
3. Optionally re-rank results by `last_scraped_at` (prefer freshest data)
4. Return chunks + metadata to the LLM

### Step 3.3 — LLM Answer Generator (Groq)

Build `backend/llm.py` using the **Groq Python SDK** with a strictly constrained system prompt:

```python
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

system_prompt = """
You are a facts-only mutual fund FAQ assistant for PPFAS schemes on Groww.
Rules:
- Answer using ONLY the retrieved context below. Do not use prior knowledge.
- Keep your answer to 3 sentences maximum.
- Do NOT provide investment advice, opinions, predictions, or comparisons.
- Always end with:
    Source: <source_url>
    Last updated from sources: <last_scraped_at>
- If the context does not answer the question, say:
    "I don't have this information. Please visit: <groww_url>"
"""

response = client.chat.completions.create(
    model=os.environ["GROQ_LLM_MODEL"],   # openai/gpt-oss-120b
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
    ],
    max_tokens=256,
    temperature=0.0   # Deterministic — no creativity for factual Q&A
)
```

| Property | Detail |
|----------|--------|
| **LLM Provider** | [Groq](https://groq.com) — ultra-low latency inference |
| **Model** | `openai/gpt-oss-120b` (via Groq) |
| **Temperature** | `0.0` — deterministic, no hallucination drift |
| **Max tokens** | `256` — enforces concise responses |
| **Citation** | Exactly 1 source URL per response |
| **Footer** | `Last updated from sources: <date>` |

### Step 3.4 — Refusal Handler

Build `backend/refusal_handler.py` with a templated response:

```
"This assistant only answers factual questions about PPFAS mutual fund schemes
on Groww — such as expense ratios, exit loads, or SIP minimums.
For investment guidance, please consult a SEBI-registered advisor.
Explore PPFAS funds at: https://groww.in/mutual-funds/category/ppfas-mutual-fund"
```

### Step 3.5 — FastAPI Endpoint

Build `backend/main.py` with a single POST endpoint:

```
POST /ask
Body: { "query": "What is the exit load for Parag Parikh ELSS?" }

Response: {
  "answer": "...",
  "source_url": "https://groww.in/...",
  "last_updated": "2026-08-25",
  "is_refusal": false
}
```

- Add CORS headers for frontend integration
- Add basic rate limiting to prevent abuse

---

## Phase 4 — Frontend (Chat UI)

### Step 4.1 — Build the HTML Structure

Create `frontend/index.html` with:

- **Header** — App title + disclaimer banner (`"Facts-only. No investment advice."`)
- **Welcome section** — Brief intro paragraph
- **Example questions** — 3 clickable pre-filled prompts:
  1. *"What is the expense ratio of Parag Parikh Long Term Value Fund?"*
  2. *"What is the exit load of the ELSS Tax Saver Fund?"*
  3. *"What is the minimum SIP amount for Parag Parikh Liquid Fund?"*
- **Chat window** — Message bubbles (user + assistant)
- **Input bar** — Text input + Send button
- **Response card footer** — Source link + Last updated date

### Step 4.2 — Style with Vanilla CSS

- Clean, minimal design (no frameworks)
- Persistent disclaimer banner at top (fixed/sticky)
- Clear visual separation of user vs assistant messages
- Refusal responses styled distinctly (e.g., muted tone)
- Mobile-responsive layout

### Step 4.3 — Wire Up JavaScript

Create `frontend/app.js`:

- On send: POST query to `/ask` backend endpoint
- Render response as a message bubble
- Append source link + last updated footer to every assistant response
- Render refusal responses with appropriate styling
- Handle loading states and error states gracefully

---

## Phase 5 — Testing

### Step 5.1 — Unit Tests

| Module | Test Cases |
|--------|-----------|
| Scraper | Fields extracted correctly per URL; handles missing fields |
| Query Guard | Correctly classifies factual vs advisory vs PII queries |
| Retriever | Returns relevant chunks for known queries |
| LLM | Response ≤ 3 sentences; includes citation; no advice |
| Refusal Handler | Returns polite message + Groww link |

### Step 5.2 — Integration Tests

Run end-to-end test scenarios:

| Query | Expected Outcome |
|-------|-----------------|
| "What is the expense ratio of PPFAS Long Term Value Fund?" | Factual answer + source + date |
| "What is the ELSS lock-in period?" | 3 years — with source link |
| "Should I invest in PPFAS?" | Polite refusal |
| "Which fund gives better returns?" | Polite refusal |
| "My PAN is ABCDE1234F, which fund is good?" | PII refusal |
| "What is the benchmark for Parag Parikh Large Cap?" | Factual answer |

### Step 5.3 — Compliance Check

- ✅ No PII collected or logged
- ✅ All source URLs resolve to `groww.in`
- ✅ No advice or comparative language in any answer
- ✅ Every response has exactly 1 citation
- ✅ Every response has `Last updated from sources:` footer

---

## Phase 6 — Scheduler

### Step 6.1 — GitHub Action Workflow

- Create `.github/workflows/scheduler.yml`
- Set trigger to `schedule` using cron expression `30 4 * * *` (which corresponds to 10:00 AM IST)
- Set up Python environment and install dependencies
- Run the ingestion component to scrape latest data, normalize, chunk, embed, and update ChromaDB.

### Step 6.2 — Ingestion Script

- Create `ingest.py` or ensure `scraper/scrape.py` covers the entire flow (scraping -> chunking -> embedding -> ChromaDB update)
- Ensure it can be run unattended by the GitHub Action.

---

## Phase 7 — Documentation & Delivery

### Step 7.1 — Write README.md

Cover:
- Project overview & disclaimer
- Selected AMC (PPFAS) and all 7 scheme URLs
- Architecture summary (link to `architecture.md`)
- Setup instructions (env, install, run)
- How to refresh the corpus
- Known limitations

### Step 7.2 — Final Review Checklist

| Criterion | Status |
|-----------|--------|
| All 7 PPFAS scheme pages scraped | ☐ |
| Vector store populated and searchable | ☐ |
| Query guard blocks advisory queries | ☐ |
| All answers ≤ 3 sentences | ☐ |
| All answers include 1 citation | ☐ |
| All answers include `Last updated` footer | ☐ |
| Refusals are polite and include Groww link | ☐ |
| UI shows disclaimer prominently | ✅ |
| No PII handled anywhere in the system | ☐ |
| README complete | ☐ |

---



## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Groq for LLM** | Ultra-low latency inference; free tier available; Llama models are strong for structured factual Q&A |
| **sentence-transformers for embeddings** | Groq has no embedding API; local model avoids extra API dependency and is free |
| **Temperature = 0.0** | Facts-only use case requires deterministic, non-creative output |
| Field-level chunking | Avoids mixing unrelated facts in a single chunk; improves retrieval precision |
| Query Guard runs before retrieval | Saves embedding + LLM cost on refused queries |
| Playwright over BeautifulSoup | Groww pages are JavaScript-rendered; static parsers may miss dynamic content |
| ChromaDB over FAISS | Persistent storage + metadata filtering out of the box |
| Templated refusals (not LLM-generated) | Consistent, compliant, zero hallucination risk on refusals |
| Vanilla CSS frontend | Keeps the stack minimal; no build toolchain required |
