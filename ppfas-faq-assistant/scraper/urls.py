"""
urls.py — All 7 PPFAS scheme URLs from Groww.
Only Groww URLs are used as the source of truth (no third-party sites).
"""

PPFAS_URLS = [
    "https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-elss-tax-saver-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-conservative-hybrid-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-liquid-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-arbitrage-fund-direct-growth",
    "https://groww.in/mutual-funds/parag-parikh-dynamic-asset-allocation-fund-direct-growth",
]

# Human-readable scheme names mapped to their Groww URL slug
SCHEME_NAMES = {
    "parag-parikh-long-term-value-fund-direct-growth": "Parag Parikh Long Term Value Fund",
    "parag-parikh-elss-tax-saver-fund-direct-growth": "Parag Parikh ELSS Tax Saver Fund",
    "parag-parikh-large-cap-fund-direct-growth": "Parag Parikh Large Cap Fund",
    "parag-parikh-conservative-hybrid-fund-direct-growth": "Parag Parikh Conservative Hybrid Fund",
    "parag-parikh-liquid-fund-direct-growth": "Parag Parikh Liquid Fund",
    "parag-parikh-arbitrage-fund-direct-growth": "Parag Parikh Arbitrage Fund",
    "parag-parikh-dynamic-asset-allocation-fund-direct-growth": "Parag Parikh Dynamic Asset Allocation Fund",
}

# Fields to extract per scheme page
TARGET_FIELDS = [
    "expense_ratio",
    "exit_load",
    "minimum_sip",
    "minimum_lump_sum",
    "riskometer",
    "benchmark",
    "lock_in_period",   # Only applicable to ELSS; "Not applicable" for others
    "fund_manager",
    "aum",
    "fund_category",
]
