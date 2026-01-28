"""
Categorizer Module — Assigns a spending/revenue category to each transaction.

Strategy:
  1. Rule-based: scan text for keywords defined in config.CATEGORY_RULES.
  2. If no rule matches and OpenAI is available, ask the LLM.
  3. Final fallback: "other".
"""

import json
import re

from . import config

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def categorize(transaction: dict) -> str:
    """
    Return a category string for the given transaction.

    Parameters
    ----------
    transaction : dict
        Must contain at least 'description', 'raw_text', and 'type'.

    Returns
    -------
    str
        Category label (e.g. "sales", "supplies", "rent", "other").
    """
    # Sales are always categorized as "sales"
    if transaction.get("type") == "sale":
        return "sales"

    # Combine searchable text
    searchable = " ".join([
        transaction.get("description", ""),
        transaction.get("raw_text", ""),
        " ".join(i.get("name", "") for i in transaction.get("items", [])),
    ]).lower()

    # Rule-based matching
    category = _match_rules(searchable)
    if category:
        return category

    # LLM fallback
    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        return _categorize_with_llm(searchable)

    return "other"


def _match_rules(text: str) -> str | None:
    """Check keyword rules and return the first matching category."""
    for keyword, category in config.CATEGORY_RULES.items():
        if keyword in text:
            return category
    return None


_CATEGORIZATION_PROMPT = """\
You are a bookkeeping assistant for a small Brazilian business.
Given the following transaction text, return ONLY the category name
(one word, lowercase) from this list:

sales, supplies, rent, utilities, internet, phone, transport, food,
maintenance, wages, taxes, marketing, equipment, other

Transaction text:
"""


def _categorize_with_llm(text: str) -> str:
    """Use OpenAI to categorize when rules don't match."""
    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _CATEGORIZATION_PROMPT},
            {"role": "user", "content": text[:500]},
        ],
        temperature=0.0,
        max_tokens=20,
    )
    category = response.choices[0].message.content.strip().lower()
    # Validate against known categories
    valid = {
        "sales", "supplies", "rent", "utilities", "internet", "phone",
        "transport", "food", "maintenance", "wages", "taxes", "marketing",
        "equipment", "other",
    }
    return category if category in valid else "other"
