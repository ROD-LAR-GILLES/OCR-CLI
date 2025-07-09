# application/use_cases.py
from pathlib import Path
from typing import Tuple, List, Any

from application.ports import OCRPort, TableExtractorPort, StoragePort
from domain.models import Document


class ProcessDocument:
    """Caso de uso orquestador."""

    def __init__(
        self,
        ocr: OCRPort,
        table_extractor: TableExtractorPort,
        storage: StoragePort,
    ) -> None:
        self.ocr = ocr
        self.table_extractor = table_extractor
        self.storage = storage

    def __call__(self, pdf_path: Path) -> Tuple[Path, List[Path]]:
        text: str = self.ocr.extract_text(pdf_path)
        tables: List[Any] = self.table_extractor.extract_tables(pdf_path)

        self.storage.save(pdf_path, text, tables, pdf_path)

        return pdf_path.with_suffix(".txt"), [
            pdf_path.with_suffix(".pdf"),
            pdf_path.with_suffix(".txt"),
        ]