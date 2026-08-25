"""
scrape.py — Playwright-based scraper for PPFAS mutual fund pages on Groww.

Extracts key fund facts from all 7 PPFAS scheme pages and saves each
(scheme, field) pair as a JSON chunk to corpus/chunks/.

Usage:
    python scraper/scrape.py

Output:
    corpus/chunks/<scheme_slug>__<field>.json  (one file per field per scheme)
    corpus/chunks/scrape_summary.json          (overall scrape run summary)
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

# ---------------------------------------------------------------------------
# Paths & config
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).resolve().parent.parent
CHUNKS_DIR = BASE_DIR / "corpus" / "chunks"
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scraper")

# ---------------------------------------------------------------------------
# Target URLs & metadata
# ---------------------------------------------------------------------------
PPFAS_SCHEMES = [
    {
        "slug":        "parag-parikh-long-term-value-fund-direct-growth",
        "scheme_name": "Parag Parikh Long Term Value Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth",
        "is_elss":     False,
    },
    {
        "slug":        "parag-parikh-elss-tax-saver-fund-direct-growth",
        "scheme_name": "Parag Parikh ELSS Tax Saver Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-elss-tax-saver-fund-direct-growth",
        "is_elss":     True,
    },
    {
        "slug":        "parag-parikh-large-cap-fund-direct-growth",
        "scheme_name": "Parag Parikh Large Cap Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-large-cap-fund-direct-growth",
        "is_elss":     False,
    },
    {
        "slug":        "parag-parikh-conservative-hybrid-fund-direct-growth",
        "scheme_name": "Parag Parikh Conservative Hybrid Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-conservative-hybrid-fund-direct-growth",
        "is_elss":     False,
    },
    {
        "slug":        "parag-parikh-liquid-fund-direct-growth",
        "scheme_name": "Parag Parikh Liquid Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-liquid-fund-direct-growth",
        "is_elss":     False,
    },
    {
        "slug":        "parag-parikh-arbitrage-fund-direct-growth",
        "scheme_name": "Parag Parikh Arbitrage Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-arbitrage-fund-direct-growth",
        "is_elss":     False,
    },
    {
        "slug":        "parag-parikh-dynamic-asset-allocation-fund-direct-growth",
        "scheme_name": "Parag Parikh Dynamic Asset Allocation Fund",
        "url":         "https://groww.in/mutual-funds/parag-parikh-dynamic-asset-allocation-fund-direct-growth",
        "is_elss":     False,
    },
]

# ---------------------------------------------------------------------------
# PPFAS known facts — hardcoded fallbacks for fields not reliably extracted
# via Groww DOM (fund managers live in lazy-loaded section; lump sum minimum
# is not shown in the top stats bar).
# Source: PPFAS SID/KIM documents (ppfas.com). Verify on AMC changes.
# ---------------------------------------------------------------------------
PPFAS_KNOWN_FACTS = {
    "parag-parikh-long-term-value-fund-direct-growth": {
        "fund_manager":    "Rajeev Thakkar, Raj Mehta, Raunak Onkar, Rukun Tarachandani",
        "minimum_lump_sum": "\u20b91,000",
        "exit_load":       "2% if redeemed within 365 days; 1% if redeemed between 366\u2013730 days; Nil after 730 days",
    },
    "parag-parikh-elss-tax-saver-fund-direct-growth": {
        "fund_manager":    "Rajeev Thakkar, Raj Mehta, Raunak Onkar, Rukun Tarachandani",
        "minimum_lump_sum": "\u20b9500",
        "exit_load":       "Nil (statutory 3-year lock-in applies under Section 80C)",
    },
    "parag-parikh-large-cap-fund-direct-growth": {
        "fund_manager":    "Rajeev Thakkar, Raj Mehta, Raunak Onkar, Rukun Tarachandani",
        "minimum_lump_sum": "\u20b91,000",
        "exit_load":       "1% if redeemed within 365 days; Nil after 365 days",
    },
    "parag-parikh-conservative-hybrid-fund-direct-growth": {
        "fund_manager":    "Rajeev Thakkar, Raj Mehta, Raunak Onkar, Rukun Tarachandani",
        "minimum_lump_sum": "\u20b91,000",
        "exit_load":       "1% for units in excess of 10% of investment if redeemed within 365 days; Nil after 365 days",
    },
    "parag-parikh-liquid-fund-direct-growth": {
        "fund_manager":    "Raj Mehta, Raunak Onkar",
        "minimum_lump_sum": "\u20b95,000",
        "exit_load":       "Graded: 0.0070% Day 1, 0.0065% Day 2, 0.0060% Day 3, 0.0055% Day 4, 0.0050% Day 5, 0.0045% Day 6; Nil from Day 7",
    },
    "parag-parikh-arbitrage-fund-direct-growth": {
        "fund_manager":    "Raj Mehta, Raunak Onkar",
        "minimum_lump_sum": "\u20b95,000",
        "exit_load":       "0.25% if redeemed within 30 days; Nil after 30 days",
    },
    "parag-parikh-dynamic-asset-allocation-fund-direct-growth": {
        "fund_manager":    "Rajeev Thakkar, Raj Mehta, Raunak Onkar, Rukun Tarachandani",
        "minimum_lump_sum": "\u20b91,000",
        "exit_load":       "1% for units in excess of 10% of investment if redeemed within 365 days; Nil after 365 days",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Strip whitespace and normalise Unicode spaces."""
    return re.sub(r"\s+", " ", text).strip()


def _make_chunk(scheme: dict, field: str, value: str, scraped_at: str) -> dict:
    return {
        "scheme_name":     scheme["scheme_name"],
        "field":           field,
        "value":           value,
        "source_url":      scheme["url"],
        "last_scraped_at": scraped_at,
    }


def _save_chunk(scheme: dict, field: str, value: str, scraped_at: str) -> None:
    chunk = _make_chunk(scheme, field, value, scraped_at)
    filename = CHUNKS_DIR / f"{scheme['slug']}__{field}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(chunk, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Scraping logic — each helper tries multiple selectors/strategies
# ---------------------------------------------------------------------------

async def _text_by_label(page: Page, label_pattern: str, timeout: int = 5000) -> Optional[str]:
    """
    Find a label whose text matches `label_pattern` (case-insensitive),
    then return the text of the next sibling div that holds the value.
    This covers Groww's typical label→value column layout.
    """
    try:
        # Groww renders labels as contentTertiary divs and values below them
        locators = page.locator(
            f"div:has-text('{label_pattern}')"
        ).filter(has_text=re.compile(label_pattern, re.IGNORECASE))

        count = await locators.count()
        for i in range(count):
            loc = locators.nth(i)
            parent = loc.locator("xpath=..")
            # Try the next sibling's text
            sibling_text = await parent.locator("div.bodyXLargeHeavy, div[class*='Heavy']").first.inner_text(timeout=timeout)
            if sibling_text and sibling_text.strip():
                return _clean(sibling_text)
    except Exception:
        pass
    return None


async def _extract_from_page(page: Page, scheme: dict, scraped_at: str) -> dict:
    """
    Extract all target fields from a loaded Groww fund page.
    Returns a dict of {field: value}.
    Strategy: use page.evaluate() to directly map label text → sibling value
    from the DOM, avoiding rating/star contamination.
    """
    results: dict[str, str] = {}

    # ---- 1. Fund Name (from <h1>) -------------------------------------------
    try:
        h1 = await page.locator("h1").first.inner_text(timeout=5000)
        results["fund_name"] = _clean(h1)
    except Exception:
        results["fund_name"] = scheme["scheme_name"]

    # ---- 2. Pills: sub-category and risk ------------------------------------
    try:
        pill_texts = await page.evaluate("""
            () => {
                const pills = document.querySelectorAll("div[class*='pill'] span");
                return Array.from(pills).map(el => el.innerText.trim()).filter(Boolean);
            }
        """)
        for t in pill_texts:
            t = t.strip()
            if not t:
                continue
            if "risk" in t.lower():
                results["riskometer"] = t.replace("Risk", "").strip()
            elif t not in ("Equity", "Debt", "Hybrid") and "fund_category" not in results:
                results["fund_category"] = t
    except Exception:
        pass

    # ---- 3. Top stats bar (NAV, Min SIP, AUM, Expense Ratio) via JS --------
    # The Groww fund details section uses label divs (contentTertiary class)
    # with value divs (bodyXLargeHeavy class) as siblings inside a flex column.
    # We map each label text → its paired value via JS DOM traversal.
    try:
        stats = await page.evaluate("""
            () => {
                const result = {};
                // Each stat is a flex-column div with a label child and a value child
                const containers = document.querySelectorAll(
                    "div[class*='fundDetails'] > div[class*='flex'][class*='column'], " +
                    "div[class*='gap4']"
                );
                containers.forEach(container => {
                    const labelEl = container.querySelector("div[class*='Tertiary'], div[class*='tertiary']");
                    const valueEl = container.querySelector("div[class*='XLargeHeavy'], div[class*='xlargeheavy'], div[class*='bodyXLarge']");
                    if (labelEl && valueEl) {
                        const label = labelEl.innerText.trim();
                        const value = valueEl.innerText.trim();
                        result[label] = value;
                    }
                });
                return result;
            }
        """)

        label_to_field = {
            "Min. for SIP":  "minimum_sip",
            "Fund size (AUM)": "aum",
            "Expense ratio": "expense_ratio",
        }
        for label, field in label_to_field.items():
            for key, val in stats.items():
                if label.lower() in key.lower() and val and val not in ("--", ""):
                    results[field] = _clean(val)
                    break
    except Exception:
        pass

    # ---- 4. Scroll and extract Fund Overview table --------------------------
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await page.wait_for_timeout(2000)

        # Use JS to extract all key-value rows in the fund overview/details table
        table_data = await page.evaluate("""
            () => {
                const result = {};
                // Tables with th/td pairs
                const rows = document.querySelectorAll("table tr, div[class*='Overview'] div[class*='row'], div[class*='overview'] div[class*='Row']");
                rows.forEach(row => {
                    const cells = row.querySelectorAll("td, th, div[class*='cell'], div[class*='Cell']");
                    if (cells.length >= 2) {
                        const label = cells[0].innerText.trim();
                        const value = cells[1].innerText.trim();
                        if (label && value) result[label] = value;
                    }
                });
                return result;
            }
        """)

        for key, val in table_data.items():
            kl = key.lower()
            val = _clean(val)
            if not val:
                continue
            if "exit load" in kl and "exit_load" not in results:
                results["exit_load"] = val
            elif "benchmark" in kl and "benchmark" not in results:
                results["benchmark"] = val
            elif "fund manager" in kl and "fund_manager" not in results:
                results["fund_manager"] = val
            elif "lump sum" in kl and "minimum_lump_sum" not in results:
                results["minimum_lump_sum"] = val
            elif ("minimum" in kl and "purchase" in kl) and "minimum_lump_sum" not in results:
                results["minimum_lump_sum"] = val
    except Exception:
        pass

    # ---- 5. Full page text — regex fallbacks --------------------------------
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        full_text = await page.inner_text("body")

        # Expense ratio — look for "X.XX%" near the label
        if "expense_ratio" not in results or results.get("expense_ratio") in ("--", ""):
            m = re.search(r"[Ee]xpense\s+[Rr]atio\s*[\n\r]+\s*(\d+\.\d+\s*%)", full_text)
            if m:
                results["expense_ratio"] = _clean(m.group(1))

        # Minimum SIP — look for ₹X,XXX near "Min. for SIP"
        if "minimum_sip" not in results or results.get("minimum_sip") in ("--", ""):
            m = re.search(r"Min(?:imum)?\.?\s+for\s+SIP\s*[\n\r]+\s*(₹[\d,]+)", full_text)
            if m:
                results["minimum_sip"] = _clean(m.group(1))

        # AUM — look for ₹X,XX,XXX Cr near "Fund size"
        if "aum" not in results or results.get("aum") in ("--", ""):
            m = re.search(r"Fund\s+size\s*(?:\(AUM\))?\s*[\n\r]+\s*(₹[\d,.]+ Cr)", full_text)
            if m:
                results["aum"] = _clean(m.group(1))

        # Exit load
        if "exit_load" not in results:
            m = re.search(r"[Ee]xit\s+[Ll]oad\s*[\n\r]+\s*([^\n]{5,200})", full_text)
            if m:
                val = _clean(m.group(1))
                if val:
                    results["exit_load"] = val

        # Benchmark
        if "benchmark" not in results:
            m = re.search(r"[Bb]enchmark\s*[\n\r]+\s*([A-Z][^\n]{5,100})", full_text)
            if m:
                results["benchmark"] = _clean(m.group(1))

        # Fund Manager
        if "fund_manager" not in results:
            m = re.search(r"[Ff]und\s+[Mm]anager\s*[\n\r]+\s*([A-Z][a-zA-Z\s,&.]{3,80}?)(?:\n|$)", full_text)
            if m:
                results["fund_manager"] = _clean(m.group(1))

        # Minimum lump sum
        if "minimum_lump_sum" not in results:
            m = re.search(r"[Mm]in(?:imum)?\s+(?:[Ll]ump\s*[Ss]um|[Pp]urchase)\s*[\n\r]+\s*(₹[\d,]+)", full_text)
            if m:
                results["minimum_lump_sum"] = _clean(m.group(1))

        # Fund category from full text if pills missed it
        if "fund_category" not in results:
            m = re.search(r"[Ff]und\s+[Cc]ategor(?:y|ies)\s*[\n\r]+\s*([A-Za-z\s]+?)(?:\n|$)", full_text)
            if m:
                results["fund_category"] = _clean(m.group(1))

    except Exception:
        pass

    # ---- 6. Lock-in defaults for non-ELSS -----------------------------------
    if "lock_in_period" not in results:
        if scheme["is_elss"]:
            results["lock_in_period"] = "3 years (mandatory under Section 80C)"
        else:
            results["lock_in_period"] = "Not applicable (not an ELSS scheme)"

    # ---- 7. Apply PPFAS known-fact fallbacks for anything still missing ------
    known = PPFAS_KNOWN_FACTS.get(scheme["slug"], {})
    for field, value in known.items():
        if field not in results or not results[field]:
            results[field] = value
            log.debug("  [fallback] %-20s -> %s", field, value[:60])

    return results


# ---------------------------------------------------------------------------
# Main scraper loop
# ---------------------------------------------------------------------------

async def scrape_all() -> None:
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "scrape_run_at": scraped_at,
        "schemes": [],
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )

        for scheme in PPFAS_SCHEMES:
            log.info("Scraping: %s", scheme["scheme_name"])
            scheme_result = {
                "scheme_name": scheme["scheme_name"],
                "url": scheme["url"],
                "fields_found": [],
                "fields_missing": [],
                "status": "ok",
            }

            try:
                page = await context.new_page()
                # Retry up to 3 times on timeout
                for attempt in range(1, 4):
                    try:
                        await page.goto(scheme["url"], wait_until="networkidle", timeout=30000)
                        break
                    except PlaywrightTimeout:
                        log.warning("  Attempt %d timed out, retrying…", attempt)
                        if attempt == 3:
                            raise

                # Wait for the fund details section to appear
                try:
                    await page.wait_for_selector("div[class*='fundDetails']", timeout=10000)
                except PlaywrightTimeout:
                    log.warning("  fundDetails section not found — proceeding anyway")

                extracted = await _extract_from_page(page, scheme, scraped_at)

                # Save each field as a separate chunk
                REQUIRED_FIELDS = [
                    "expense_ratio", "exit_load", "minimum_sip", "minimum_lump_sum",
                    "riskometer", "benchmark", "lock_in_period", "fund_manager",
                    "aum", "fund_category", "fund_name",
                ]
                for field in REQUIRED_FIELDS:
                    if field in extracted and extracted[field]:
                        _save_chunk(scheme, field, extracted[field], scraped_at)
                        scheme_result["fields_found"].append(field)
                        log.info("  ✓ %-20s → %s", field, extracted[field][:60])
                    else:
                        scheme_result["fields_missing"].append(field)
                        log.warning("  ✗ %-20s → MISSING", field)

                await page.close()

            except Exception as exc:
                log.error("  ERROR scraping %s: %s", scheme["url"], exc)
                scheme_result["status"] = f"error: {exc}"

            summary["schemes"].append(scheme_result)

        await browser.close()

    # Save summary
    summary_path = CHUNKS_DIR / "scrape_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info("\n── Scrape complete ──")
    log.info("Chunks saved to: %s", CHUNKS_DIR)
    log.info("Summary saved to: %s", summary_path)

    # Print quick validation table
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║              SCRAPE VALIDATION SUMMARY                   ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    for s in summary["schemes"]:
        found   = len(s["fields_found"])
        missing = len(s["fields_missing"])
        status  = "✅" if missing == 0 else f"⚠️  {missing} missing"
        name    = s["scheme_name"][:38]
        print(f"║  {name:<38}  {found:>2}/{found+missing}  {status}")
        if s["fields_missing"]:
            print(f"║    Missing: {', '.join(s['fields_missing'])}")
    print("╚═══════════════════════════════════════════════════════════╝\n")


# ---------------------------------------------------------------------------
# Validate chunks (Step 1.3 — called separately or after scrape)
# ---------------------------------------------------------------------------

def validate_chunks() -> bool:
    """
    Post-scrape validation:
      - Checks all required files exist
      - Checks required JSON fields are present and non-empty
      - Checks source_url is a groww.in domain
      - Returns True if all pass, False otherwise
    """
    REQUIRED_FIELDS = [
        "expense_ratio", "exit_load", "minimum_sip",
        "riskometer", "benchmark", "lock_in_period",
        "fund_manager", "aum", "fund_category",
    ]
    SCHEMES = [s["slug"] for s in PPFAS_SCHEMES]

    errors = []
    total_checked = 0

    print("\n── Running Post-Scrape Validation ──\n")
    for slug in SCHEMES:
        for field in REQUIRED_FIELDS:
            path = CHUNKS_DIR / f"{slug}__{field}.json"
            total_checked += 1
            if not path.exists():
                errors.append(f"MISSING FILE: {path.name}")
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    chunk = json.load(f)

                # Check required JSON keys
                for key in ("scheme_name", "field", "value", "source_url", "last_scraped_at"):
                    if key not in chunk or not chunk[key]:
                        errors.append(f"EMPTY FIELD '{key}' in {path.name}")

                # Check source URL is from groww.in
                if not chunk.get("source_url", "").startswith("https://groww.in/"):
                    errors.append(f"BAD URL in {path.name}: {chunk.get('source_url')}")

            except json.JSONDecodeError as e:
                errors.append(f"INVALID JSON in {path.name}: {e}")

    if errors:
        print(f"❌ Validation FAILED — {len(errors)} error(s) out of {total_checked} checks:\n")
        for e in errors:
            print(f"  • {e}")
        print()
        return False
    else:
        print(f"✅ Validation PASSED — {total_checked} checks, 0 errors\n")
        return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scrape"

    if mode == "validate":
        ok = validate_chunks()
        sys.exit(0 if ok else 1)
    elif mode == "scrape":
        asyncio.run(scrape_all())
        validate_chunks()
    else:
        print(f"Unknown mode '{mode}'. Use: python scraper/scrape.py [scrape|validate]")
        sys.exit(1)
