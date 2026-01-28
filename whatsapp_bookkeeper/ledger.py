"""
Ledger Module — Simple JSON-based transaction store.

Each entry has:
  - id          : auto-incremented
  - timestamp   : when the entry was recorded
  - date        : transaction date (from receipt)
  - total       : float
  - type        : "sale" | "expense"
  - category    : str
  - description : str
  - items       : list[dict]
"""

import json
import os
import uuid
from datetime import datetime, date, timedelta
from typing import Optional

from . import config


def _load() -> list:
    """Load ledger from JSON file."""
    if os.path.isfile(config.LEDGER_PATH):
        with open(config.LEDGER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(entries: list) -> None:
    """Save ledger to JSON file."""
    with open(config.LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, default=str)


def add_entry(transaction: dict, category: str) -> dict:
    """
    Add a transaction to the ledger.

    Parameters
    ----------
    transaction : dict
        Output from extractor.extract_fields().
    category : str
        Output from categorizer.categorize().

    Returns
    -------
    dict
        The saved ledger entry (with id and timestamp).
    """
    entries = _load()

    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now().isoformat(),
        "date": transaction.get("date", datetime.now().strftime("%Y-%m-%d")),
        "total": transaction.get("total", 0.0),
        "type": transaction.get("type", "expense"),
        "category": category,
        "description": transaction.get("description", ""),
        "items": transaction.get("items", []),
    }

    entries.append(entry)
    _save(entries)
    return entry


def get_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list:
    """
    Retrieve ledger entries, optionally filtered by date range.

    Parameters
    ----------
    start_date, end_date : str (YYYY-MM-DD), optional
    """
    entries = _load()
    if start_date:
        entries = [e for e in entries if e["date"] >= start_date]
    if end_date:
        entries = [e for e in entries if e["date"] <= end_date]
    return entries


def get_week_entries(reference_date: Optional[str] = None) -> list:
    """
    Get entries for the week containing the reference date.
    Week runs Monday–Sunday.
    """
    if reference_date:
        ref = date.fromisoformat(reference_date)
    else:
        ref = date.today()

    # Monday of the current week
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)

    return get_entries(
        start_date=monday.isoformat(),
        end_date=sunday.isoformat(),
    )


def clear_ledger() -> None:
    """Remove all entries (useful for demo resets)."""
    _save([])


def summary_stats(entries: list) -> dict:
    """
    Compute summary statistics for a list of entries.

    Returns
    -------
    dict with keys:
        - total_sales     : float
        - total_expenses  : float
        - profit          : float
        - num_sales       : int
        - num_expenses    : int
        - by_category     : dict[str, float]
        - top_items       : list[dict]  (top 5 items by total revenue/cost)
    """
    total_sales = 0.0
    total_expenses = 0.0
    num_sales = 0
    num_expenses = 0
    by_category = {}
    item_totals = {}

    for entry in entries:
        amount = entry.get("total", 0.0)
        cat = entry.get("category", "other")
        by_category[cat] = by_category.get(cat, 0.0) + amount

        if entry.get("type") == "sale":
            total_sales += amount
            num_sales += 1
        else:
            total_expenses += amount
            num_expenses += 1

        for item in entry.get("items", []):
            name = item.get("name", "unknown")
            item_total = item.get("qty", 1) * item.get("unit_price", 0)
            item_totals[name] = item_totals.get(name, 0.0) + item_total

    # Top items by total value
    sorted_items = sorted(item_totals.items(), key=lambda x: x[1], reverse=True)
    top_items = [{"name": n, "total": t} for n, t in sorted_items[:5]]

    return {
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "profit": total_sales - total_expenses,
        "num_sales": num_sales,
        "num_expenses": num_expenses,
        "by_category": by_category,
        "top_items": top_items,
    }
