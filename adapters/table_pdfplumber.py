# adapters/table_pdfplumber.py
from pathlib import Path
from typing import List

import pdfplumber
import pandas as pd

from application.ports import TableExtractorPort


class PdfPlumberAdapter(TableExtractorPort):
    """Extrae tablas como DataFrames list."""

    def extract_tables(self, pdf_path: Path) -> List[pd.DataFrame]:
        dfs: List[pd.DataFrame] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    dfs.append(pd.DataFrame(table))
        return dfs