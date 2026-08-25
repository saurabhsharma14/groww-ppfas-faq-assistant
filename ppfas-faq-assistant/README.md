# PPFAS Mutual Fund FAQ Assistant

> ⚠️ **Facts-only. No investment advice.**

A lightweight RAG-based FAQ assistant for PPFAS mutual fund schemes on Groww.
Answers factual queries about expense ratios, exit loads, SIP minimums, and more —
with verified source citations and no investment advice.

---

## Selected AMC & Schemes

**AMC:** PPFAS — Parag Parikh Financial Advisory Services

| # | Scheme | Groww URL |
|---|--------|-----------|
| 1 | Long Term Value Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth) |
| 2 | ELSS Tax Saver Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-elss-tax-saver-fund-direct-growth) |
| 3 | Large Cap Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-large-cap-fund-direct-growth) |
| 4 | Conservative Hybrid Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-conservative-hybrid-fund-direct-growth) |
| 5 | Liquid Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-liquid-fund-direct-growth) |
| 6 | Arbitrage Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-arbitrage-fund-direct-growth) |
| 7 | Dynamic Asset Allocation Fund | [groww.in](https://groww.in/mutual-funds/parag-parikh-dynamic-asset-allocation-fund-direct-growth) |

---

## Architecture Overview (RAG)

```
User Query
    │
    ▼
Query Guard ──── Advisory / PII ──▶ Refusal Handler ──▶ Response
    │
  Factual
    │
    ▼
Retrieval Engine (sentence-transformers + ChromaDB)
    │
    ▼
LLM Answer Generator (Groq — openai/gpt-oss-120b, temp=0.0)
    │
    ▼
Response (≤3 sentences + 1 Groww citation + Last updated date)
```

**Tech Stack:**

| Layer | Technology |
|-------|-----------|
| Scraper | Python + Playwright |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) — local |
| Vector Store | ChromaDB |
| LLM | Groq (`openai/gpt-oss-120b`) |
| Backend | FastAPI |
| Frontend | HTML + Vanilla CSS + JavaScript |

---

## Setup Instructions

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd ppfas-faq-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 5. Run the scraper (Phase 1)

```bash
python scraper/scrape.py
```

### 6. Ingest corpus into ChromaDB (Phase 2)

```bash
python backend/ingest.py
```

### 7. Start the backend

```bash
uvicorn backend.main:app --reload
```

### 8. Open the frontend

Open `frontend/index.html` in your browser, or serve it locally:

```bash
python -m http.server 3000 --directory frontend
```

---

## Known Limitations

- **Corpus freshness:** Data accuracy depends on when the scraper last ran. The `Last updated` date in each response indicates freshness.
- **Scraping fragility:** Any Groww page layout change may break field extraction and require scraper maintenance.
- **Scope:** Only 7 PPFAS schemes are covered. Queries about other AMCs will be refused.
- **No real-time NAV:** Live NAV is not retrieved; users are redirected to Groww for current prices.
- **English only:** No multilingual support in v1.
- **No authentication:** The assistant is stateless and does not personalise responses.

---

## Disclaimer

> This assistant provides **facts-only** information about PPFAS mutual fund schemes sourced exclusively from [groww.in](https://groww.in). It does **not** provide investment advice, recommendations, or return projections. For investment decisions, consult a SEBI-registered financial advisor.
