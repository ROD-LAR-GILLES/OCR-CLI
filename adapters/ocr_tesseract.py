# adapters/ocr_tesseract.py
from pathlib import Path
from typing import List

import pytesseract
from pdf2image import convert_from_path

from application.ports import OCRPort


class TesseractAdapter(OCRPort):
    """Extrae TODO el texto (OCR) usando Tesseract."""

    def __init__(self, lang: str = "spa", dpi: int = 300) -> None:
        self.lang = lang
        self.dpi = dpi

    def extract_text(self, pdf_path: Path) -> str:
        images: List = convert_from_path(pdf_path, dpi=self.dpi)
        chunks = [
            pytesseract.image_to_string(img, lang=self.lang)
            for img in images
        ]
        return "\n\n".join(chunks)