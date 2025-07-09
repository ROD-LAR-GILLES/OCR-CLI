# ocr_cli/menu.py
"""
Menú principal OCR-CLI (Docker)
"""

from pathlib import Path
import questionary
from adapters.ocr_tesseract import TesseractAdapter
from adapters.table_pdfplumber import PdfPlumberAdapter
from adapters.storage_filesystem import FileStorage
from application.use_cases import ProcessDocument

PDF_DIR = Path("/pdfs")            # ← carpeta empaquetada con la imagen
OUT_DIR = Path("/app/resultado")   # ← resultados dentro del contenedor

def listar_pdfs() -> list[str]:
    """Devuelve la lista de archivos .pdf presentes en /pdfs."""
    return sorted([p.name for p in PDF_DIR.glob("*.pdf")])

def procesar_archivo(nombre: str):
    pdf_path = PDF_DIR / nombre
    interactor = ProcessDocument(
        ocr=TesseractAdapter(),
        table_extractor=PdfPlumberAdapter(),
        storage=FileStorage(OUT_DIR),
    )
    j, t = interactor(pdf_path)
    print(f"\n{nombre} procesado.")
    print(f"   - Texto:     {t}")
    print(f"   - JSON:      {j}\n")

def main():
    while True:
        archivos = listar_pdfs()
        if not archivos:
            print("No hay PDFs en /pdfs. Añade archivos y reconstruye la imagen.")
            break

        choice = questionary.select(
            "Selecciona un PDF para procesar (Esc → salir):",
            choices=archivos + ["Salir"],
        ).ask()

        if choice and choice.endswith(".pdf"):
            procesar_archivo(choice)
        else:
            break

if __name__ == "__main__":
    main()