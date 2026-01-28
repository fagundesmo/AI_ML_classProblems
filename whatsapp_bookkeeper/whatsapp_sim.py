"""
WhatsApp Simulator — Main entry point for the bookkeeper prototype.

Simulates the WhatsApp interaction loop:
  1. User sends a photo (receipt image) and/or text message
  2. System processes with OCR → Extraction → Categorization → Ledger
  3. System replies with a confirmation
  4. On demand, system generates a weekly summary

Usage (command line):
    python -m whatsapp_bookkeeper.whatsapp_sim
"""

import os
import sys

from .ocr import extract_text_from_image
from .extractor import extract_fields
from .categorizer import categorize
from .ledger import add_entry, get_week_entries, clear_ledger
from .summarizer import generate_weekly_summary, _format_brl


# ---------------------------------------------------------------------------
# Message processing pipeline
# ---------------------------------------------------------------------------

def process_receipt(image_path: str, user_message: str = "") -> str:
    """
    Full pipeline: image → OCR → extract → categorize → ledger → reply.

    Parameters
    ----------
    image_path : str
        Path to the receipt image.
    user_message : str
        Optional accompanying text from the user.

    Returns
    -------
    str
        WhatsApp reply message confirming the entry.
    """
    # Step 1: OCR
    raw_text = extract_text_from_image(image_path)

    # Step 2: Extract structured fields
    transaction = extract_fields(raw_text, user_message)

    # Step 3: Categorize
    category = categorize(transaction)

    # Step 4: Save to ledger
    entry = add_entry(transaction, category)

    # Step 5: Generate confirmation reply
    return _confirmation_reply(entry)


def process_text_message(user_message: str) -> str:
    """
    Process a text-only message (no image).

    Handles commands like "resumo" (summary) or quick expense/sale entries.
    """
    msg_lower = user_message.strip().lower()

    # Command: weekly summary
    if msg_lower in ("resumo", "resumo semanal", "summary", "weekly"):
        entries = get_week_entries()
        return generate_weekly_summary(entries)

    # Command: clear/reset
    if msg_lower in ("limpar", "reset", "clear"):
        clear_ledger()
        return "🗑️ Livro-caixa limpo. Todas as transações foram removidas."

    # Command: help
    if msg_lower in ("ajuda", "help", "?"):
        return _help_message()

    # Try to parse as a quick entry: "venda 150" or "despesa 50 fornecedor"
    quick = _parse_quick_entry(user_message)
    if quick:
        category = categorize(quick)
        entry = add_entry(quick, category)
        return _confirmation_reply(entry)

    return (
        "🤔 Não entendi. Envie:\n"
        "• 📷 Foto de recibo\n"
        "• \"venda 150\" ou \"despesa 50\"\n"
        "• \"resumo\" para ver o resumo semanal\n"
        "• \"ajuda\" para mais opções"
    )


def _parse_quick_entry(text: str) -> dict | None:
    """Parse quick text entries like 'venda 150' or 'gasto 80 fornecedor'."""
    import re
    from datetime import datetime

    # Pattern: type + amount + optional description
    match = re.match(
        r"(venda|vendas|sale|receita|despesa|gasto|expense|compra)\s+"
        r"R?\$?\s*([\d.,]+)\s*(.*)",
        text.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None

    type_word = match.group(1).lower()
    amount_str = match.group(2).replace(".", "").replace(",", ".")
    description = match.group(3).strip() or type_word.capitalize()

    try:
        amount = float(amount_str)
    except ValueError:
        return None

    tx_type = "sale" if type_word in ("venda", "vendas", "sale", "receita") else "expense"

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total": amount,
        "items": [],
        "type": tx_type,
        "description": description,
        "raw_text": text,
    }


def _confirmation_reply(entry: dict) -> str:
    """Build a WhatsApp confirmation reply for a recorded entry."""
    emoji = "💰" if entry["type"] == "sale" else "💸"
    type_label = "Venda" if entry["type"] == "sale" else "Despesa"

    lines = [
        f"{emoji} *{type_label} registrada!*",
        f"📅 Data: {entry['date']}",
        f"💵 Valor: {_format_brl(entry['total'])}",
        f"📂 Categoria: {entry['category']}",
    ]

    if entry.get("items"):
        lines.append(f"📝 Itens: {len(entry['items'])}")

    lines.append(f"\n_ID: {entry['id']}_")
    return "\n".join(lines)


def _help_message() -> str:
    """Return the help text."""
    return (
        "📖 *WhatsApp Bookkeeper — Ajuda*\n\n"
        "📷 *Foto de recibo* → Registro automático\n"
        "💬 *Texto rápido:*\n"
        "  • \"venda 150\" → registra venda de R$150\n"
        "  • \"despesa 80 fornecedor\" → registra despesa\n"
        "  • \"gasto 50 transporte\" → registra despesa\n\n"
        "📊 *Comandos:*\n"
        "  • \"resumo\" → resumo semanal\n"
        "  • \"limpar\" → apaga todas as transações\n"
        "  • \"ajuda\" → esta mensagem"
    )


# ---------------------------------------------------------------------------
# Interactive CLI simulator
# ---------------------------------------------------------------------------

def _run_interactive():
    """Run an interactive WhatsApp simulation in the terminal."""
    print("=" * 60)
    print("  📱 WhatsApp Bookkeeper — Simulador")
    print("  Envie mensagens como se fosse WhatsApp.")
    print("  Use 'foto <caminho>' para simular envio de imagem.")
    print("  Digite 'sair' para encerrar.")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("👤 Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Até logo!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("sair", "exit", "quit"):
            print("👋 Até logo!")
            break

        # Simulate image sending
        if user_input.lower().startswith("foto "):
            image_path = user_input[5:].strip()
            # Check if additional message follows
            parts = image_path.split("|", 1)
            image_path = parts[0].strip()
            msg = parts[1].strip() if len(parts) > 1 else ""

            # Resolve bare filenames from the sample_receipts folder
            if not os.path.isfile(image_path):
                sample_dir = os.path.join(os.path.dirname(__file__), "sample_receipts")
                candidate = os.path.join(sample_dir, os.path.basename(image_path))
                if os.path.isfile(candidate):
                    image_path = candidate

            print(f"📷 [Processando imagem: {os.path.basename(image_path)}...]")
            reply = process_receipt(image_path, msg)
        else:
            reply = process_text_message(user_input)

        print(f"\n🤖 Bookkeeper:\n{reply}\n")


if __name__ == "__main__":
    _run_interactive()
