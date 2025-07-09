# application/ports.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any


class OCRPort(ABC):
    @abstractmethod
    def extract_text(self, pdf_path: Path) -> str: ...


class TableExtractorPort(ABC):
    @abstractmethod
    def extract_tables(self, pdf_path: Path) -> List[Any]: ...


class StoragePort(ABC):
    @abstractmethod
    def save(self, name: str, text: str, tables: List[Any], original: Path) -> None: ...