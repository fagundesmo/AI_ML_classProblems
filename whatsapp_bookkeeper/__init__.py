"""
WhatsApp Bookkeeper Prototype
==============================
User sends photos + short messages → system builds ledger → weekly summary.

ML pieces:
  1. OCR on images (receipts)
  2. LLM extraction to structured fields (amount/date/items)
  3. Categorization (rules + LLM)
  4. Weekly summary generator (LLM) in plain language + 1 action
"""
