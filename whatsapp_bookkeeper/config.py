"""
Configuration for the WhatsApp Bookkeeper prototype.

Set OPENAI_API_KEY as an environment variable, or the system falls back
to regex-based extraction (no LLM required for the demo).
"""

import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# Ledger stored as a JSON file
LEDGER_PATH = os.path.join(os.path.dirname(__file__), "ledger.json")

# Default currency
CURRENCY = "R$"

# Categorization rules (keyword → category)
CATEGORY_RULES = {
    # Revenue categories
    "venda": "sales",
    "vendas": "sales",
    "sold": "sales",
    "sale": "sales",
    "receita": "sales",
    "revenue": "sales",
    "pagamento recebido": "sales",
    "payment received": "sales",
    "pix recebido": "sales",

    # Cost of goods
    "fornecedor": "supplies",
    "supplier": "supplies",
    "material": "supplies",
    "matéria": "supplies",
    "insumo": "supplies",
    "ingrediente": "supplies",
    "estoque": "supplies",
    "stock": "supplies",

    # Operating expenses
    "aluguel": "rent",
    "rent": "rent",
    "luz": "utilities",
    "energia": "utilities",
    "água": "utilities",
    "water": "utilities",
    "electricity": "utilities",
    "internet": "internet",
    "telefone": "phone",
    "phone": "phone",

    # Transport
    "transporte": "transport",
    "uber": "transport",
    "gasolina": "transport",
    "gas": "transport",
    "fuel": "transport",
    "combustível": "transport",

    # Food
    "almoço": "food",
    "lanche": "food",
    "comida": "food",
    "restaurante": "food",
    "lunch": "food",
    "food": "food",

    # Maintenance
    "manutenção": "maintenance",
    "conserto": "maintenance",
    "repair": "maintenance",

    # Wages
    "salário": "wages",
    "funcionário": "wages",
    "employee": "wages",
    "salary": "wages",
    "wages": "wages",
}

# Categories that count as revenue (everything else is expense)
REVENUE_CATEGORIES = {"sales"}
