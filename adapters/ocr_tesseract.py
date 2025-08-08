"""
Adaptador de Tesseract OCR.

Implementación con imports perezosos para minimizar dependencias en tiempo de import.
Usa pdf2image para rasterizar el PDF y pytesseract para extraer texto.
"""
from pathlib import Path
from application.ports import OCRPort


class TesseractAdapter(OCRPort):
    """Adaptador Tesseract con configuración simple de idioma y DPI."""

    def __init__(self, lang: str = "spa", dpi: int = 300) -> None:
        self.lang = lang
        self.dpi = dpi

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extrae texto de un PDF página por página y lo concatena.

        Usa imports perezosos para no requerir dependencias durante testing
        cuando se usan mocks.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")

        # Imports perezosos
        try:
            from pdf2image import convert_from_path  # type: ignore
            import pytesseract  # type: ignore
        except Exception:
            # Si no están disponibles, retornar texto vacío en lugar de fallar
            return ""

        try:
            images = convert_from_path(str(pdf_path), dpi=self.dpi)
        except Exception:
            # Si la rasterización falla, retornar vacío para no detener el flujo
            return ""

        textos = []
        for img in images:
            try:
                texto = pytesseract.image_to_string(img, lang=self.lang)
            except Exception:
                texto = ""
            textos.append(texto.strip())

        return "\n\n".join(filter(None, textos))
