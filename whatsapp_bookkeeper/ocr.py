"""
OCR Module — Extracts raw text from receipt images.

Uses pytesseract (Tesseract OCR) with Portuguese + English language support.
Falls back to a simulated OCR output when Tesseract is not installed,
so the demo can run anywhere.
"""

import os

try:
    from PIL import Image
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def extract_text_from_image(image_path: str) -> str:
    """
    Run OCR on a receipt image and return the raw text.

    Parameters
    ----------
    image_path : str
        Path to the image file (jpg, png, etc.).

    Returns
    -------
    str
        Extracted text from the image.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if TESSERACT_AVAILABLE:
        img = Image.open(image_path)
        # Use Portuguese + English for Brazilian receipts
        text = pytesseract.image_to_string(img, lang="por+eng")
        return text.strip()

    # Fallback: return placeholder so the rest of the pipeline works
    return _simulated_ocr(image_path)


def _simulated_ocr(image_path: str) -> str:
    """
    Return simulated OCR output based on the filename.
    Useful for demo / testing without Tesseract installed.
    """
    filename = os.path.basename(image_path).lower()

    samples = {
        "receipt_sale_01.png": (
            "RECIBO DE VENDA\n"
            "Data: 20/01/2026\n"
            "Cliente: Maria Silva\n"
            "Produto: Bolo de chocolate  Qtd: 2  Valor: R$35,00\n"
            "Produto: Brigadeiro (cento)  Qtd: 1  Valor: R$80,00\n"
            "TOTAL: R$150,00\n"
            "Pagamento: PIX"
        ),
        "receipt_expense_01.png": (
            "NOTA FISCAL\n"
            "SUPERMERCADO BOA COMPRA\n"
            "Data: 18/01/2026\n"
            "Farinha de trigo 5kg    R$22,50\n"
            "Chocolate em pó 1kg     R$18,90\n"
            "Leite condensado 6un    R$35,40\n"
            "Manteiga 500g           R$12,00\n"
            "Ovos 30un               R$21,00\n"
            "TOTAL: R$109,80\n"
            "Forma Pgto: Débito"
        ),
        "receipt_sale_02.png": (
            "VENDA #0047\n"
            "Data: 22/01/2026\n"
            "Bolo de cenoura     1x  R$40,00\n"
            "Torta de limão      1x  R$45,00\n"
            "Salgados (cento)    2x  R$60,00\n"
            "TOTAL: R$205,00\n"
            "Pago em dinheiro"
        ),
        "receipt_expense_02.png": (
            "GÁS EXPRESS LTDA\n"
            "NF 9921  Data: 19/01/2026\n"
            "Botijão gás 13kg  2x  R$110,00\n"
            "Entrega                R$10,00\n"
            "TOTAL: R$120,00"
        ),
        "receipt_expense_03.png": (
            "RECIBO\n"
            "Aluguel cozinha compartilhada\n"
            "Mês: Janeiro/2026\n"
            "Valor: R$800,00\n"
            "Data: 05/01/2026"
        ),
    }

    return samples.get(filename, f"[Simulated OCR — no sample for {filename}]")
