# Edge Cases: Mutual Fund FAQ Assistant (RAG-Based)

> ⚠️ **"Facts-only. No investment advice."**

This document catalogues known and anticipated edge cases across every layer of the system — scraper, corpus, vector store, query guard, retrieval engine, LLM, refusal handler, and frontend. Each entry includes the expected system behaviour and recommended mitigation.

---

## Table of Contents

1. [Scraper Edge Cases](#1-scraper-edge-cases)
2. [Corpus & Chunking Edge Cases](#2-corpus--chunking-edge-cases)
3. [Embedding & Vector Store Edge Cases](#3-embedding--vector-store-edge-cases)
4. [Query Guard Edge Cases](#4-query-guard-edge-cases)
5. [Retrieval Engine Edge Cases](#5-retrieval-engine-edge-cases)
6. [LLM Answer Generator Edge Cases](#6-llm-answer-generator-edge-cases)
7. [Refusal Handler Edge Cases](#7-refusal-handler-edge-cases)
8. [Frontend & UX Edge Cases](#8-frontend--ux-edge-cases)
9. [Privacy & Security Edge Cases](#9-privacy--security-edge-cases)
10. [Compliance Edge Cases](#10-compliance-edge-cases)

---

## 1. Scraper Edge Cases

### 1.1 — JavaScript Not Rendered

| Attribute | Detail |
|-----------|--------|
| **Scenario** | BeautifulSoup is used instead of Playwright; dynamic content (NAV, expense ratio) is not in static HTML |
| **Risk** | Fields extracted as `null` or empty string; silently incorrect corpus |
| **Expected Behaviour** | Scraper should detect empty fields and raise a warning |
| **Mitigation** | Use Playwright by default; add post-scrape field completeness check |

---

### 1.2 — Groww Page Structure Changes

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Groww redesigns the mutual fund page layout; CSS selectors / XPaths break |
| **Risk** | All 7 scrapes fail silently or return garbage data |
| **Expected Behaviour** | Scraper fails with a structured error log per URL |
| **Mitigation** | Assert required fields post-scrape; send alert if >1 field is missing |

---

### 1.3 — Scraper Rate-Limiting / Bot Detection

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Groww detects automated scraping and returns CAPTCHA or 429 |
| **Risk** | Corpus not refreshed; stale data served without warning |
| **Expected Behaviour** | Scraper logs failure with HTTP status; retries with backoff |
| **Mitigation** | Implement exponential backoff (3 retries); use realistic User-Agent headers |

---

### 1.4 — Partial Page Load / Network Timeout

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Network is slow; Playwright times out before the data section loads |
| **Risk** | Fields captured partially or not at all |
| **Expected Behaviour** | Scraper retries up to 3 times; logs the timeout |
| **Mitigation** | Set generous Playwright `wait_until="networkidle"` with a 30s timeout |

---

### 1.5 — Scheme Page Returns 404

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Groww changes a fund's URL slug (e.g., after rebrand) |
| **Risk** | That scheme's data is entirely missing from the corpus |
| **Expected Behaviour** | Log 404 per URL; do not update corpus for that scheme; retain last known data |
| **Mitigation** | URL health check step before scraping; alert on 404s |

---

### 1.6 — Missing Field for a Specific Scheme

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Exit load is "Nil" displayed as blank on Groww; scraper captures empty string |
| **Risk** | LLM has no data to answer; may hallucinate |
| **Expected Behaviour** | Store `"Nil"` or `"Not applicable"` explicitly; do not leave field blank |
| **Mitigation** | Post-parse normalisation step: blank exit load → `"Nil (no exit load)"` |

---

## 2. Corpus & Chunking Edge Cases

### 2.1 — Duplicate Chunks After Re-scrape

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Scheduler re-runs scraper; old and new chunks both exist in ChromaDB |
| **Risk** | Vector search returns outdated chunks alongside fresh ones; conflicting answers |
| **Expected Behaviour** | Re-ingestion replaces existing chunks for the same `(scheme_name, field)` key |
| **Mitigation** | Use deterministic chunk IDs (`scheme_slug__field`); upsert, not insert |

---

### 2.2 — Field Value Changes Between Scrapes

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Expense ratio for a fund is updated by the AMC; old value is in the corpus |
| **Risk** | Stale answer served until next scheduled refresh |
| **Expected Behaviour** | `last_scraped_at` in the footer alerts users to check the source |
| **Mitigation** | Run nightly refresh; display `Last updated` date prominently |

---

### 2.3 — ELSS Lock-In Field on Non-ELSS Schemes

| Attribute | Detail |
|-----------|--------|
| **Scenario** | A non-ELSS fund page has no lock-in section; chunk value is empty |
| **Risk** | LLM is asked about lock-in for Parag Parikh Liquid Fund and retrieves nothing |
| **Expected Behaviour** | Store explicit `"No lock-in period applicable"` for non-ELSS schemes |
| **Mitigation** | Populate this field explicitly during chunking for all non-ELSS schemes |

---

### 2.4 — Ambiguous Fund Name in Query

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User asks about "Parag Parikh Fund" without specifying which of the 7 schemes |
| **Risk** | Retrieval returns chunks from multiple schemes; answer is vague or incorrect |
| **Expected Behaviour** | LLM response should list the matching schemes and ask for clarification, or answer for all matches |
| **Mitigation** | Add a disambiguation step: if top-K chunks span >1 scheme, ask the user to specify |

---

## 3. Embedding & Vector Store Edge Cases

### 3.1 — Query in a Different Language

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User types query in Hindi or Hinglish: *"ELSS fund ka lock-in period kya hai?"* |
| **Risk** | Embedding similarity is low; wrong or no chunks retrieved |
| **Expected Behaviour** | Respond in English with a polite note that only English queries are supported |
| **Mitigation** | Detect non-English input; respond with a language limitation notice + Groww link |

---

### 3.2 — Vector Store Not Initialised

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Backend starts before the scraper has run; ChromaDB collection is empty |
| **Risk** | All queries return no results; LLM outputs fallback message for every query |
| **Expected Behaviour** | Backend startup check: if collection is empty, return a system maintenance message |
| **Mitigation** | Health check endpoint `/status` that verifies corpus is non-empty before accepting queries |

---

### 3.3 — Semantic Drift — Unrelated Chunks Retrieved

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Query: *"What is the SIP amount?"* retrieves chunks about NAV or riskometer instead of minimum SIP |
| **Risk** | LLM produces a hallucinated or irrelevant answer |
| **Expected Behaviour** | Set a similarity score threshold; discard chunks below threshold |
| **Mitigation** | Use ChromaDB distance filter; if no chunk exceeds threshold, redirect to Groww URL |

---

### 3.4 — ChromaDB Corruption / Disk Full

| Attribute | Detail |
|-----------|--------|
| **Scenario** | ChromaDB persistence directory is corrupted or disk is full |
| **Risk** | Backend crashes on vector search |
| **Expected Behaviour** | Backend catches exception; returns a service unavailable message with Groww link |
| **Mitigation** | Wrap all DB calls in try/except; add disk usage monitoring |

---

## 4. Query Guard Edge Cases

### 4.1 — Advisory Query Disguised as Factual

| Attribute | Detail |
|-----------|--------|
| **Scenario** | *"What is the historical return of PPFAS and is it safe to invest?"* — mixed factual + advisory |
| **Risk** | Query guard passes it as factual; LLM gives a partial answer with implied advice |
| **Expected Behaviour** | Detect advisory portion; split and refuse the advisory part; answer only factual portion |
| **Mitigation** | Flag queries containing advisory trigger words even if they also contain factual terms |

---

### 4.2 — Very Short or Single-Word Query

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User sends: `"expense"` or `"SIP"` or just `"?"` |
| **Risk** | Embedding is too vague; retrieval returns unrelated top-K chunks |
| **Expected Behaviour** | Prompt user to rephrase with a scheme name and specific question |
| **Mitigation** | Minimum query length check (e.g., >10 characters); respond with example questions |

---

### 4.3 — All-Caps or Noisy Query

| Attribute | Detail |
|-----------|--------|
| **Scenario** | `"WHAT IS EXPENSE RATIO OF PPFAS???"` or excessive punctuation |
| **Risk** | Minor — embedding usually handles this; but edge case for keyword-based guard |
| **Expected Behaviour** | Normalise query (lowercase, strip extra punctuation) before classification |
| **Mitigation** | Pre-process query: `.lower().strip()` before passing to guard and retriever |

---

### 4.4 — Query Guard Misclassifies a Factual Query as Advisory

| Attribute | Detail |
|-----------|--------|
| **Scenario** | *"Is the ELSS fund eligible for tax deduction?"* — factual (80C), but contains "eligible" which may trigger advisory flag |
| **Risk** | Valid factual query is refused; poor user experience |
| **Expected Behaviour** | Refusal message should include a Groww link where the user can find the answer |
| **Mitigation** | Build a whitelist of factual financial terms (`"tax deduction"`, `"80C"`, `"lock-in"`) that override advisory flags |

---

### 4.5 — Empty Query Submitted

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User clicks Send with an empty text box |
| **Risk** | Backend receives empty string; embedding fails or returns noise |
| **Expected Behaviour** | Frontend blocks submission; shows inline validation: *"Please enter a question"* |
| **Mitigation** | Client-side guard: disable Send button when input is empty |

---

## 5. Retrieval Engine Edge Cases

### 5.1 — No Chunks Returned (Zero Results)

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Query is factual but outside the scraped data (e.g., a field not collected) |
| **Risk** | LLM has no context; risks hallucinating an answer |
| **Expected Behaviour** | Return a fallback: *"I don't have this information. Please visit: \<groww_url\>"* |
| **Mitigation** | Check `len(results) == 0` before calling LLM; return templated fallback directly |

---

### 5.2 — Top-K Chunks All from Wrong Scheme

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Query mentions "liquid fund" but top-K returns chunks from the arbitrage fund |
| **Risk** | Answer is about the wrong scheme |
| **Expected Behaviour** | Filter retrieved chunks by scheme name if mentioned in the query |
| **Mitigation** | Add metadata pre-filter: if scheme name is detected in the query, restrict ChromaDB search to that scheme's chunks |

---

### 5.3 — Stale Chunks Ranked Higher Than Fresh Ones

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Old chunk (3 weeks ago) has higher cosine similarity than fresh chunk (today) |
| **Risk** | Outdated data served as the answer |
| **Expected Behaviour** | Re-rank retrieved chunks to prefer those with the latest `last_scraped_at` |
| **Mitigation** | Apply a recency boost: multiply similarity score by a freshness factor |

---

## 6. LLM Answer Generator Edge Cases

### 6.1 — LLM Ignores System Prompt and Gives Advice

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Despite `temperature=0.0` and strict system prompt, LLM appends *"This seems like a good fund"* |
| **Risk** | Compliance violation — advice given |
| **Expected Behaviour** | Post-generation content filter scans for advisory language patterns |
| **Mitigation** | Add a post-LLM filter: scan output for advisory keywords; replace with refusal if detected |

---

### 6.2 — LLM Exceeds 3-Sentence Limit

| Attribute | Detail |
|-----------|--------|
| **Scenario** | LLM returns 5 sentences despite `max_tokens=256` and prompt instruction |
| **Risk** | Verbose response; breaks UX contract |
| **Expected Behaviour** | Truncate to 3 sentences server-side before sending to frontend |
| **Mitigation** | Post-process: split on `.` and return first 3 complete sentences only |

---

### 6.3 — LLM Returns No Citation Link

| Attribute | Detail |
|-----------|--------|
| **Scenario** | LLM omits the `Source:` footer despite prompt instruction |
| **Risk** | Response without a citation violates the facts-only contract |
| **Expected Behaviour** | Server-side validation: if `Source:` is absent, append the scheme's Groww URL from chunk metadata |
| **Mitigation** | Always inject source URL from retrieved chunk metadata as a fallback, independent of LLM output |

---

### 6.4 — LLM Invents a Source URL

| Attribute | Detail |
|-----------|--------|
| **Scenario** | LLM hallucinates a plausible but incorrect Groww URL |
| **Risk** | User follows a broken or wrong link |
| **Expected Behaviour** | Discard LLM-generated URLs; always use the `source_url` from retrieved chunk metadata |
| **Mitigation** | Strip any URL from LLM output; append only the verified metadata URL |

---

### 6.5 — Groq API Rate Limit or Downtime

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Groq API returns 429 (rate limit) or 503 (downtime) |
| **Risk** | Query fails with an unhandled exception; user sees a 500 error |
| **Expected Behaviour** | Return a friendly error: *"Service temporarily unavailable. Please try again shortly or visit \<groww_url\>"* |
| **Mitigation** | Wrap Groq API call in try/except; implement retry with backoff (2 retries, 1s delay) |

---

### 6.6 — LLM Returns "I Don't Know" for a Covered Topic

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Retrieval found relevant chunks but LLM still says it has no information |
| **Risk** | Poor user experience; loss of trust |
| **Expected Behaviour** | Detect "I don't know" pattern in response; log it as a retrieval quality issue |
| **Mitigation** | Log query + retrieved chunks + LLM response for manual review; improve chunking or prompt |

---

## 7. Refusal Handler Edge Cases

### 7.1 — Refusal Link is Outdated or Broken

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Hardcoded Groww link in refusal template points to a deprecated URL |
| **Risk** | User clicks a broken link in the refusal response |
| **Expected Behaviour** | Refusal always links to the canonical PPFAS category page, not a specific dynamic URL |
| **Mitigation** | Use stable Groww category URL: `https://groww.in/mutual-funds/category/ppfas-mutual-fund` |

---

### 7.2 — Repeated Refusals Frustrate the User

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User keeps rephrasing an advisory query hoping to get past the guard |
| **Risk** | User frustration; poor UX |
| **Expected Behaviour** | After 2 consecutive refusals, show a more detailed help message with example valid questions |
| **Mitigation** | Track consecutive refusal count in session state; escalate message after threshold |

---

## 8. Frontend & UX Edge Cases

### 8.1 — Very Long User Query

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User pastes a 500-word paragraph as their question |
| **Risk** | Embedding quality degrades; backend processes unnecessary tokens |
| **Expected Behaviour** | Truncate input to 300 characters with a visible counter; warn user |
| **Mitigation** | `maxlength="300"` on the input field; character countdown displayed |

---

### 8.2 — Special Characters or Code Injection in Query

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User types `<script>alert('xss')</script>` or SQL injection patterns |
| **Risk** | XSS if the query is rendered as raw HTML in the chat window |
| **Expected Behaviour** | All user input must be HTML-escaped before rendering |
| **Mitigation** | Use `textContent` instead of `innerHTML` when rendering user messages in JS |

---

### 8.3 — No Internet / Backend Unreachable

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User's browser cannot reach the FastAPI backend |
| **Risk** | Silent failure; spinner runs forever |
| **Expected Behaviour** | Show a timeout error after 10s: *"Unable to connect. Please check your connection."* |
| **Mitigation** | Set `fetch` timeout; display user-friendly error in the chat window |

---

### 8.4 — Mobile Keyboard Covering the Input Box

| Attribute | Detail |
|-----------|--------|
| **Scenario** | On mobile, virtual keyboard pushes the chat input off-screen |
| **Risk** | User cannot see what they're typing |
| **Expected Behaviour** | Input bar stays visible above the keyboard |
| **Mitigation** | Use CSS `position: sticky; bottom: 0` on the input bar; test on iOS Safari |

---

### 8.5 — User Pastes PII into the Chat Input

| Attribute | Detail |
|-----------|--------|
| **Scenario** | User types: *"My PAN is ABCDE1234F. Can I invest?"* |
| **Risk** | PAN is logged in backend query logs |
| **Expected Behaviour** | Query Guard detects PAN pattern and refuses; backend must not log raw PII |
| **Mitigation** | Regex PII scrubber on the backend before any logging: mask PAN, Aadhaar, phone patterns |

---

## 9. Privacy & Security Edge Cases

### 9.1 — Query Logs Containing Sensitive Data

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Backend logs all incoming queries for debugging; a user typed their Aadhaar number |
| **Risk** | PII stored in plaintext logs |
| **Expected Behaviour** | Scrub PII patterns from query before logging |
| **Mitigation** | Regex-based PII masker runs on every query before it touches any log sink |

---

### 9.2 — API Key Exposed in Frontend Code

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Developer accidentally hardcodes Groq API key in `app.js` |
| **Risk** | API key visible to anyone who inspects the page source |
| **Expected Behaviour** | All API calls must be made server-side; frontend only calls the FastAPI `/ask` endpoint |
| **Mitigation** | Frontend never calls Groq or any external API directly; enforce via code review |

---

### 9.3 — `.env` File Committed to Git

| Attribute | Detail |
|-----------|--------|
| **Scenario** | Developer runs `git add .` and commits `.env` containing the Groq API key |
| **Risk** | API key exposed in public/private repo history |
| **Expected Behaviour** | `.gitignore` blocks `.env`; pre-commit hook warns if secrets detected |
| **Mitigation** | `.gitignore` entry for `.env`; optionally add `gitleaks` or `detect-secrets` pre-commit hook |

---

## 10. Compliance Edge Cases

### 10.1 — Performance Data Requested

| Attribute | Detail |
|-----------|--------|
| **Scenario** | *"What was the 3-year return of Parag Parikh Long Term Value Fund?"* |
| **Risk** | System retrieves NAV history and presents returns — which is prohibited per problem statement |
| **Expected Behaviour** | Detect performance/return queries; redirect to official Groww URL only |
| **Mitigation** | Query guard: flag queries containing `"return"`, `"CAGR"`, `"performance"`, `"grew"`, `"NAV history"` → redirect |

---

### 10.2 — Implied Recommendation in Factual Answer

| Attribute | Detail |
|-----------|--------|
| **Scenario** | *"What is the expense ratio of the ELSS fund?"* → LLM answers: *"0.60%, which is lower than average — making it a cost-efficient choice."* |
| **Risk** | The comparative/evaluative suffix constitutes implicit advice |
| **Expected Behaviour** | Post-generation filter strips evaluative language; returns plain fact only |
| **Mitigation** | Remove sentences containing `"making it"`, `"which means"`, `"good choice"`, `"better than"` patterns |

---

### 10.3 — User Asks for Fund Comparison

| Attribute | Detail |
|-----------|--------|
| **Scenario** | *"Compare the expense ratio of ELSS and Long Term Value Fund"* |
| **Risk** | System performs a comparison, which could imply one is better |
| **Expected Behaviour** | Refuse comparison queries; provide individual scheme Groww links |
| **Mitigation** | Query guard flags queries containing `"compare"`, `"vs"`, `"better"`, `"versus"`, `"difference between"` |

---

### 10.4 — Disclaimer Not Displayed

| Attribute | Detail |
|-----------|--------|
| **Scenario** | CSS bug hides the disclaimer banner on certain screen sizes |
| **Risk** | Compliance requirement not met; user unaware of facts-only scope |
| **Expected Behaviour** | Disclaimer must always be visible, regardless of device or screen size |
| **Mitigation** | Disclaimer is `position: sticky; top: 0`; tested at 320px, 768px, and 1440px widths |

---

## Summary Table

| # | Layer | Edge Case | Severity | Status |
|---|-------|-----------|----------|--------|
| 1.1 | Scraper | JS not rendered → empty fields | 🔴 High | |
| 1.2 | Scraper | Page structure change → full scrape failure | 🔴 High | |
| 1.3 | Scraper | Rate-limit / bot detection | 🟡 Medium | |
| 1.5 | Scraper | Scheme URL returns 404 | 🔴 High | |
| 2.1 | Corpus | Duplicate chunks after re-scrape | 🔴 High | |
| 2.4 | Corpus | Ambiguous fund name in query | 🟡 Medium | |
| 3.1 | Vector Store | Query in non-English language | 🟡 Medium | |
| 3.2 | Vector Store | Collection empty at startup | 🔴 High | |
| 3.3 | Vector Store | Semantic drift — wrong chunks | 🟡 Medium | |
| 4.1 | Query Guard | Mixed factual + advisory query | 🔴 High | |
| 4.4 | Query Guard | False positive refusal on factual query | 🟡 Medium | |
| 5.1 | Retrieval | Zero results returned | 🔴 High | |
| 6.1 | LLM | Advice slips through system prompt | 🔴 High | |
| 6.3 | LLM | Citation link missing from response | 🔴 High | |
| 6.4 | LLM | Hallucinated source URL | 🔴 High | |
| 6.5 | LLM | Groq API rate limit / downtime | 🟡 Medium | |
| 8.2 | Frontend | XSS injection via query input | 🔴 High | ✅ Mitigated |
| 9.1 | Privacy | PII in query logs | 🔴 High | |
| 9.3 | Security | `.env` committed to git | 🔴 High | |
| 10.1 | Compliance | Performance/return data requested | 🔴 High | |
| 10.2 | Compliance | Implied recommendation in answer | 🔴 High | |
| 10.3 | Compliance | Fund comparison query | 🔴 High | |
| 10.4 | Compliance | Disclaimer hidden by CSS | 🟡 Medium | ✅ Mitigated |

---

> [!NOTE]
> This document should be reviewed and updated each time a new component is added or a scraping failure is observed in production. Critical (🔴 High) items must be addressed before go-live.
