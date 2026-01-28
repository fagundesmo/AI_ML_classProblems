"""
Generate sample receipt images for demo purposes.

Uses PIL (Pillow) to create realistic-looking receipt images.
Run this once to populate sample_receipts/.

Usage:
    python -m whatsapp_bookkeeper.generate_sample_receipts
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_receipts")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


RECEIPTS = {
    "receipt_sale_01.png": [
        "RECIBO DE VENDA",
        "",
        "Data: 20/01/2026",
        "Cliente: Maria Silva",
        "",
        "Produto: Bolo de chocolate",
        "  Qtd: 2  Valor: R$35,00",
        "Produto: Brigadeiro (cento)",
        "  Qtd: 1  Valor: R$80,00",
        "",
        "TOTAL: R$150,00",
        "Pagamento: PIX",
    ],
    "receipt_expense_01.png": [
        "NOTA FISCAL",
        "SUPERMERCADO BOA COMPRA",
        "",
        "Data: 18/01/2026",
        "",
        "Farinha de trigo 5kg    R$22,50",
        "Chocolate em pó 1kg     R$18,90",
        "Leite condensado 6un    R$35,40",
        "Manteiga 500g           R$12,00",
        "Ovos 30un               R$21,00",
        "",
        "TOTAL: R$109,80",
        "Forma Pgto: Débito",
    ],
    "receipt_sale_02.png": [
        "VENDA #0047",
        "",
        "Data: 22/01/2026",
        "",
        "Bolo de cenoura     1x  R$40,00",
        "Torta de limão      1x  R$45,00",
        "Salgados (cento)    2x  R$60,00",
        "",
        "TOTAL: R$205,00",
        "Pago em dinheiro",
    ],
    "receipt_expense_02.png": [
        "GÁS EXPRESS LTDA",
        "",
        "NF 9921  Data: 19/01/2026",
        "",
        "Botijão gás 13kg  2x  R$110,00",
        "Entrega                R$10,00",
        "",
        "TOTAL: R$120,00",
    ],
    "receipt_expense_03.png": [
        "RECIBO",
        "",
        "Aluguel cozinha compartilhada",
        "Mês: Janeiro/2026",
        "",
        "Valor: R$800,00",
        "Data: 05/01/2026",
    ],
}


def generate_receipt_image(filename: str, lines: list[str]) -> str:
    """Generate a receipt-style PNG image."""
    if not PIL_AVAILABLE:
        print(f"  ⚠️  Pillow not installed. Skipping image generation for {filename}.")
        print("     Install with: pip install Pillow")
        # Create a placeholder text file instead
        path = os.path.join(SAMPLE_DIR, filename)
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return path

    # Receipt styling
    width = 400
    margin = 20
    line_height = 22
    height = margin * 2 + line_height * (len(lines) + 2)

    # Create image with paper-like background
    img = Image.new("RGB", (width, height), color=(255, 252, 245))
    draw = ImageDraw.Draw(img)

    # Try to use a monospace font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 14)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 14)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", 14)
        except (IOError, OSError):
            font = ImageFont.load_default()
            font_bold = font

    # Draw a subtle border
    draw.rectangle(
        [(5, 5), (width - 5, height - 5)],
        outline=(200, 195, 185),
        width=1,
    )

    # Draw dashed line at top and bottom
    y_top = margin
    y_bottom = height - margin
    for x in range(margin, width - margin, 8):
        draw.line([(x, y_top - 5), (x + 4, y_top - 5)], fill=(180, 175, 165), width=1)
        draw.line([(x, y_bottom + 5), (x + 4, y_bottom + 5)], fill=(180, 175, 165), width=1)

    # Draw text lines
    y = margin + 5
    for line in lines:
        if line.startswith(("TOTAL", "RECIBO DE VENDA", "NOTA FISCAL", "VENDA #")):
            draw.text((margin, y), line, fill=(30, 30, 30), font=font_bold)
        elif line.startswith(("R$", "Valor")):
            draw.text((margin, y), line, fill=(0, 100, 0), font=font)
        else:
            draw.text((margin, y), line, fill=(60, 60, 60), font=font)
        y += line_height

    # Save
    path = os.path.join(SAMPLE_DIR, filename)
    img.save(path)
    return path


def main():
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    print("\n🧾 Generating sample receipt images...\n")

    for filename, lines in RECEIPTS.items():
        path = generate_receipt_image(filename, lines)
        print(f"  ✅ {filename}")

    print(f"\n  📁 Saved to: {SAMPLE_DIR}/")
    print("  Done!\n")


if __name__ == "__main__":
    main()
