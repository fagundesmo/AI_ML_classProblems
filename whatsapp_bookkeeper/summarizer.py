"""
Summarizer Module — Generates a weekly WhatsApp-style summary.

Produces plain-language text + 1 actionable recommendation.

If OpenAI is available, uses the LLM for natural language generation.
Otherwise, uses a template-based approach (still clear and useful).
"""

import json
from . import config
from .ledger import summary_stats

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def generate_weekly_summary(entries: list, label: str = "Semanal") -> str:
    """
    Generate a WhatsApp-ready summary message.

    Parameters
    ----------
    entries : list
        Ledger entries for the period.
    label : str
        Header label (e.g. "Semanal", "Semana Passada", "Geral").

    Returns
    -------
    str
        Plain-text summary message.
    """
    if not entries:
        return (
            f"📊 *Resumo {label}*\n\n"
            "Nenhuma transação registrada neste período.\n"
            "Envie fotos de recibos ou mensagens para começar!"
        )

    stats = summary_stats(entries)

    if config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        return _summarize_with_llm(entries, stats, label)

    return _summarize_with_template(stats, label)


# ---------------------------------------------------------------------------
# Template-based summary (no LLM needed)
# ---------------------------------------------------------------------------

def _format_brl(value: float) -> str:
    """Format a float as Brazilian Real currency."""
    return f"R${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _summarize_with_template(stats: dict, label: str = "Semanal") -> str:
    """Build a summary using string templates."""
    sales = _format_brl(stats["total_sales"])
    expenses = _format_brl(stats["total_expenses"])
    profit = _format_brl(stats["profit"])

    # Determine profit/loss emoji
    if stats["profit"] > 0:
        status = "✅ Lucro"
    elif stats["profit"] < 0:
        status = "⚠️ Prejuízo"
    else:
        status = "➖ Empate"

    lines = [
        f"📊 *Resumo {label}*\n",
        f"💰 Vendas: {sales} ({stats['num_sales']} transação(ões))",
        f"💸 Despesas: {expenses} ({stats['num_expenses']} transação(ões))",
        f"{status}: {profit}\n",
    ]

    # Category breakdown
    if stats["by_category"]:
        lines.append("📂 *Por categoria:*")
        for cat, amount in sorted(
            stats["by_category"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"  • {cat}: {_format_brl(amount)}")
        lines.append("")

    # Actionable recommendation
    action = _generate_action(stats)
    lines.append(f"💡 *Ação:* {action}")

    return "\n".join(lines)


def _generate_action(stats: dict) -> str:
    """Generate one actionable recommendation based on the numbers."""
    # If expenses exceed sales
    if stats["total_expenses"] > stats["total_sales"] > 0:
        ratio = stats["total_expenses"] / stats["total_sales"]
        if ratio > 1.5:
            return (
                "Suas despesas são muito maiores que suas vendas. "
                "Revise os gastos com fornecedores e procure alternativas mais baratas."
            )
        return (
            "Despesas próximas do valor de vendas. "
            "Considere aumentar os preços em 10-15% ou reduzir custos de insumos."
        )

    # If profitable, suggest optimizing top expense
    if stats["profit"] > 0 and stats["by_category"]:
        expense_cats = {
            k: v for k, v in stats["by_category"].items()
            if k not in config.REVENUE_CATEGORIES
        }
        if expense_cats:
            top_expense = max(expense_cats, key=expense_cats.get)
            top_amount = _format_brl(expense_cats[top_expense])
            return (
                f"Seu maior gasto é '{top_expense}' ({top_amount}). "
                f"Negocie com fornecedores ou busque alternativas para reduzir esse custo."
            )

    # If there are popular items, suggest pricing
    if stats["top_items"]:
        top = stats["top_items"][0]
        return (
            f"'{top['name']}' é seu item mais movimentado "
            f"({_format_brl(top['total'])}). "
            f"Considere aumentar o preço em R$1-2 — pequenos ajustes somam no fim do mês."
        )

    # Generic
    return "Continue registrando todas as transações para insights mais precisos!"


# ---------------------------------------------------------------------------
# LLM-based summary
# ---------------------------------------------------------------------------

_SUMMARY_PROMPT = """\
You are a friendly bookkeeping assistant for a small Brazilian business owner.
They communicate via WhatsApp. Write a weekly financial summary in Portuguese.

Requirements:
1. Start with "📊 *Resumo Semanal*"
2. Show total sales, expenses, and profit in R$ (Brazilian Real).
3. Brief category breakdown.
4. End with exactly ONE specific, actionable recommendation.
5. Keep it under 200 words. Use WhatsApp-friendly formatting (*bold*, emojis).
6. Be warm but professional. Use "você" (informal).

Here is the data:
"""


def _summarize_with_llm(entries: list, stats: dict, label: str = "Semanal") -> str:
    """Use OpenAI to generate a natural-language summary."""
    data_payload = {
        "stats": stats,
        "entries_summary": [
            {
                "date": e["date"],
                "type": e["type"],
                "category": e["category"],
                "total": e["total"],
                "description": e["description"],
            }
            for e in entries
        ],
    }

    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _SUMMARY_PROMPT},
            {"role": "user", "content": json.dumps(data_payload, ensure_ascii=False)},
        ],
        temperature=0.7,
        max_tokens=400,
    )

    return response.choices[0].message.content.strip()
