# domain/models.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Any


@dataclass
class Document:
    name: str
    text: str
    tables: List[Any]
    source: Path