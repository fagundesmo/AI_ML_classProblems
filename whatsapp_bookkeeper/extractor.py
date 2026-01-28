"""
Extractor Module — Converts raw OCR text into structured transaction fields.

Strategy:
  1. If an OpenAI API key is configured, use the LLM for extraction.
  2. Otherwise, use regex-based heuristics (works well for the demo).
"""

import json
import re
from datetime import datetime, date
from typing import Optional

from . import config

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def extract_fields(raw_text: str, user_message: str = "") -> dict:
    """
    Extract structured fields from raw OCR text (and optional user message).

    Returns
    -------
    dict with keys:
        - date       : str (YYYY-MM-DD)
        - total      : float
        - items      : list[dict] with {name, qty, unit_price}
        - type       : "sale" | "expense"
        - description: str (short summary)
        - raw_text   : str (original OCR text preserved)
    """
    combined = f"{raw_text}\n{user_message}".strip()

    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        return _extract_with_llm(combined)

    return _extract_with_regex(raw_text, user_message)


# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are a bookkeeping assistant. Extract structured data from this receipt text.

Return ONLY valid JSON with this schema:
{
  "date": "YYYY-MM-DD",
  "total": <float>,
  "items": [{"name": "<item>", "qty": <int>, "unit_price": <float>}],
  "type": "sale" or "expense",
  "description": "<one-line summary in Portuguese>"
}

Rules:
- If the text mentions "venda", "recibo de venda", or "sold", type = "sale".
- Otherwise type = "expense".
- Dates in DD/MM/YYYY should be converted to YYYY-MM-DD.
- Monetary values use Brazilian format: R$1.234,56 → 1234.56
- If you cannot determine a field, use null.

Receipt text:
"""


def _extract_with_llm(text: str) -> dict:
    """Call OpenAI to extract structured fields."""
    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _EXTRACTION_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.0,
        max_tokens=512,
    )
    content = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)

    data = json.loads(content)
    data["raw_text"] = text
    return data


# ---------------------------------------------------------------------------
# Regex-based extraction (no LLM needed)
# ---------------------------------------------------------------------------

def _parse_brazilian_number(s: str) -> Optional[float]:
    """Convert Brazilian currency string to float.  R$1.234,56 → 1234.56"""
    s = s.replace("R$", "").replace(" ", "").strip()
    s = s.replace(".", "")   # remove thousands separator
    s = s.replace(",", ".")  # decimal separator
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(text: str) -> str:
    """Find a DD/MM/YYYY date in text and return YYYY-MM-DD."""
    match = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", text)
    if match:
        day, month, year = match.groups()
        try:
            d = date(int(year), int(month), int(day))
            return d.isoformat()
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def _detect_type(text: str) -> str:
    """Determine if the receipt is a sale or expense."""
    sale_keywords = [
        "venda", "vendas", "recibo de venda", "sold", "sale",
        "pagamento recebido", "pix recebido",
    ]
    text_lower = text.lower()
    for kw in sale_keywords:
        if kw in text_lower:
            return "sale"
    return "expense"


def _extract_items(text: str) -> list:
    """Extract line items from receipt text using regex patterns."""
    items = []
    seen_lines = set()

    # Pattern 1: "Produto: <name>  Qtd: <n>  Valor: R$<price>"
    pattern_produto = re.compile(
        r"Produto:\s*(.+?)\s+Qtd:\s*(\d+)\s+Valor:\s*R?\$?\s*([\d.,]+)",
        re.IGNORECASE,
    )
    for m in pattern_produto.finditer(text):
        name = m.group(1).strip()
        qty = int(m.group(2))
        price = _parse_brazilian_number(m.group(3))
        if price and name not in seen_lines:
            items.append({"name": name, "qty": qty, "unit_price": price})
            seen_lines.add(name)

    # Pattern 2: "<item>  <n>x  R$<price>"  (e.g. "Bolo de cenoura  1x  R$40,00")
    pattern_qty_x = re.compile(
        r"^(.+?)\s+(\d+)\s*[xX]\s+R?\$?\s*([\d.,]+)\s*$",
        re.MULTILINE,
    )
    for m in pattern_qty_x.finditer(text):
        name = m.group(1).strip()
        qty = int(m.group(2))
        price = _parse_brazilian_number(m.group(3))
        if price and name not in seen_lines:
            items.append({"name": name, "qty": qty, "unit_price": price})
            seen_lines.add(name)

    # Pattern 3: "<item>    R$<price>" (single item, no qty — assume qty=1)
    pattern_price_only = re.compile(
        r"^(.+?)\s{2,}R?\$?\s*([\d.,]+)\s*$",
        re.MULTILINE,
    )
    skip_words = ["total", "subtotal", "troco", "forma", "pgto", "pagamento", "data", "nf "]
    for m in pattern_price_only.finditer(text):
        name = m.group(1).strip()
        price = _parse_brazilian_number(m.group(2))
        if not price:
            continue
        # Skip lines that already matched as qty-based items (name contains "Nx" suffix)
        if re.search(r"\d+\s*[xX]\s*$", name):
            continue
        if name in seen_lines or any(w in name.lower() for w in skip_words):
            continue
        items.append({"name": name, "qty": 1, "unit_price": price})
        seen_lines.add(name)

    return items


def _extract_total(text: str) -> Optional[float]:
    """Extract the TOTAL amount from the receipt."""
    # Prefer explicit TOTAL line (case-insensitive)
    match = re.search(
        r"TOTAL\s*:?\s*R?\$?\s*([\d.,]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return _parse_brazilian_number(match.group(1))
    # Fallback: standalone "Valor:" line (for single-amount receipts)
    match = re.search(
        r"^Valor\s*:\s*R?\$?\s*([\d.,]+)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if match:
        return _parse_brazilian_number(match.group(1))
    return None


def _extract_with_regex(raw_text: str, user_message: str = "") -> dict:
    """Regex-based extraction — no LLM required."""
    combined = f"{raw_text}\n{user_message}"
    tx_date = _parse_date(combined)
    tx_type = _detect_type(combined)
    total = _extract_total(raw_text)
    items = _extract_items(raw_text)

    # If we found items but no total, sum them up
    if items and total is None:
        total = sum(i["qty"] * i["unit_price"] for i in items)

    # Build description
    if tx_type == "sale":
        desc = f"Venda de {len(items)} item(s)" if items else "Venda"
    else:
        # Try to grab the store/vendor name (usually first non-empty line)
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        vendor = lines[0] if lines else "Despesa"
        desc = f"Compra em {vendor}"

    return {
        "date": tx_date,
        "total": total or 0.0,
        "items": items,
        "type": tx_type,
        "description": desc,
        "raw_text": raw_text,
    }
