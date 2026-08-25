# PPFAS Mutual Fund FAQ Assistant (RAG-Based)

> ⚠️ **"Facts-only. No investment advice."**

This project is a factual Mutual Fund FAQ Assistant focused specifically on PPFAS (Parag Parikh Financial Advisory Services) schemes. It uses a RAG (Retrieval-Augmented Generation) architecture, grounded *exclusively* in the official content from [groww.in](https://groww.in).

## Scope

- **AMC:** Parag Parikh Financial Advisory Services (PPFAS)
- **Schemes Included:**
  1. Parag Parikh Long Term Value Fund
  2. Parag Parikh ELSS Tax Saver Fund
  3. Parag Parikh Large Cap Fund
  4. Parag Parikh Conservative Hybrid Fund
  5. Parag Parikh Liquid Fund
  6. Parag Parikh Arbitrage Fund
  7. Parag Parikh Dynamic Asset Allocation Fund

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- A [Groq API key](https://console.groq.com/keys) for LLM inference.

### 2. Installation
Clone the repository and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in the values:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_LLM_MODEL=openai/gpt-oss-120b
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./embeddings/store
```

### 4. Running the System
1. **Initialize Corpus:** Run the scraper to populate ChromaDB.
   ```bash
   python scraper/scrape.py
   ```
2. **Start Backend:**
   ```bash
   uvicorn backend.main:app --reload
   ```
3. **Start Frontend:**
   Open `frontend/index.html` in your browser.

## Known Limitations

- **Source Restriction:** The assistant only accesses data explicitly scraped from Groww.in pages listed in its configuration.
- **No Advisory:** The assistant includes a Query Guard that aggressively rejects any queries seeking investment advice, comparisons, or predictions.
- **Latency:** While Groq handles LLM generation instantly, retrieving and embedding documents locally via `sentence-transformers` can introduce brief local processing delays depending on hardware.
- **Refresh Frequency:** Updates reflect the last scraped timestamp (daily refresh via scheduled jobs); intra-day NAV changes might not be instantly available.

## Sample Q&A

Here are some example queries and how the assistant is designed to respond:

**1. Q: What is the expense ratio of Parag Parikh Long Term Value Fund?**
> **A:** The expense ratio of Parag Parikh Long Term Value Fund (Direct Plan) is 0.58%.
> *Source: https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth*
> *Last updated from sources: 2026-08-25T10:00:00Z*

**2. Q: What is the exit load of the ELSS Tax Saver Fund?**
> **A:** An exit load of 2% is applicable if units are redeemed within 365 days of allotment. For ELSS funds, there is a mandatory lock-in period of 3 years.
> *Source: https://groww.in/mutual-funds/parag-parikh-elss-tax-saver-fund-direct-growth*
> *Last updated from sources: 2026-08-25T10:00:00Z*

**3. Q: What is the minimum SIP amount for Parag Parikh Liquid Fund?**
> **A:** The minimum SIP amount for Parag Parikh Liquid Fund is ₹1,000.
> *Source: https://groww.in/mutual-funds/parag-parikh-liquid-fund-direct-growth*
> *Last updated from sources: 2026-08-25T10:00:00Z*

**4. Q: Should I invest in PPFAS Mutual Funds?**
> **A:** This assistant only answers factual questions about PPFAS mutual fund schemes on Groww — such as expense ratios, exit loads, or SIP minimums. For investment guidance, please consult a SEBI-registered advisor.
> *Explore PPFAS funds at: https://groww.in/mutual-funds/category/ppfas-mutual-fund*

**5. Q: What is the benchmark index for Parag Parikh Large Cap Fund?**
> **A:** The benchmark index for the Parag Parikh Large Cap Fund is NIFTY 100 TRI.
> *Source: https://groww.in/mutual-funds/parag-parikh-large-cap-fund-direct-growth*
> *Last updated from sources: 2026-08-25T10:00:00Z*
