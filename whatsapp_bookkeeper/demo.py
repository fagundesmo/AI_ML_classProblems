"""
Demo Script — Runs through a full week of simulated WhatsApp interactions.

This demonstrates the complete pipeline:
  1. Receipt images processed via OCR → extraction → categorization
  2. Quick text entries
  3. Weekly summary generation

No API keys or Tesseract required — uses simulated OCR and template summaries.

Usage:
    python -m whatsapp_bookkeeper.demo
"""

import os
import sys

# Ensure package is importable when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whatsapp_bookkeeper.whatsapp_sim import process_receipt, process_text_message
from whatsapp_bookkeeper.ledger import clear_ledger

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_receipts")


def print_separator():
    print("\n" + "─" * 55 + "\n")


def simulate_message(sender: str, message: str, is_photo: bool = False):
    """Pretty-print a simulated WhatsApp message."""
    icon = "📷" if is_photo else "💬"
    print(f"  {icon} {sender}: {message}")


def run_demo():
    """Run the full demo scenario."""
    print()
    print("=" * 55)
    print("  📱  WhatsApp Bookkeeper — Demo Completa")
    print("=" * 55)
    print()
    print("  Simulando uma semana de interações de uma")
    print("  confeiteira que vende bolos e doces.")
    print()

    # Start fresh
    clear_ledger()
    print("  🗑️  Livro-caixa limpo para começar.\n")

    # --- Day 1: Monday - Rent payment ---
    print_separator()
    print("  📅 Segunda-feira — Pagamento de aluguel")
    simulate_message("Ana", "foto receipt_expense_03.png", is_photo=True)
    reply = process_receipt(
        os.path.join(SAMPLE_DIR, "receipt_expense_03.png"),
        "paguei o aluguel da cozinha"
    )
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Day 2: Tuesday - Bought supplies ---
    print_separator()
    print("  📅 Terça-feira — Compra de ingredientes")
    simulate_message("Ana", "foto receipt_expense_01.png | comprei ingredientes", is_photo=True)
    reply = process_receipt(
        os.path.join(SAMPLE_DIR, "receipt_expense_01.png"),
        "comprei ingredientes no supermercado"
    )
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Day 3: Wednesday - Gas delivery ---
    print_separator()
    print("  📅 Quarta-feira — Entrega de gás")
    simulate_message("Ana", "foto receipt_expense_02.png", is_photo=True)
    reply = process_receipt(
        os.path.join(SAMPLE_DIR, "receipt_expense_02.png"),
        ""
    )
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Day 4: Thursday - Sales! ---
    print_separator()
    print("  📅 Quinta-feira — Vendas do dia")
    simulate_message("Ana", "foto receipt_sale_01.png | venda da Maria", is_photo=True)
    reply = process_receipt(
        os.path.join(SAMPLE_DIR, "receipt_sale_01.png"),
        "venda da Maria"
    )
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Day 5: Friday - More sales ---
    print_separator()
    print("  📅 Sexta-feira — Mais vendas")
    simulate_message("Ana", "foto receipt_sale_02.png", is_photo=True)
    reply = process_receipt(
        os.path.join(SAMPLE_DIR, "receipt_sale_02.png"),
        ""
    )
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Quick text entries ---
    print_separator()
    print("  📅 Sexta-feira — Entradas rápidas por texto")

    simulate_message("Ana", "venda 85 encomenda de brigadeiro")
    reply = process_text_message("venda 85 encomenda de brigadeiro")
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")
    print()

    simulate_message("Ana", "gasto 35 uber entrega")
    reply = process_text_message("gasto 35 uber entrega")
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Weekly Summary ---
    print_separator()
    print("  📅 Domingo — Pedindo resumo semanal")
    simulate_message("Ana", "resumo")
    reply = process_text_message("resumo")
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    # --- Help ---
    print_separator()
    print("  📅 Bônus — Menu de ajuda")
    simulate_message("Ana", "ajuda")
    reply = process_text_message("ajuda")
    print(f"\n  🤖 Bookkeeper:\n")
    for line in reply.splitlines():
        print(f"    {line}")

    print_separator()
    print("  ✅ Demo completa!")
    print("  O livro-caixa foi populado com 7 transações.")
    print("  O resumo semanal mostra vendas, despesas e lucro.")
    print()


if __name__ == "__main__":
    run_demo()
