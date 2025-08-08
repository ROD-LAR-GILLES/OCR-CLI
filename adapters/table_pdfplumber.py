# adapters/table_pdfplumber.py
"""
Adaptador de extracción de tablas basado en pdfplumber.

Este módulo implementa el puerto TableExtractorPort utilizando pdfplumber,
una librería especializada en análisis estructural de documentos PDF que
puede detectar y extraer tablas manteniendo su formato original.
"""
from pathlib import Path
from typing import List, Any
import importlib

from application.ports import TableExtractorPort


class PdfPlumberAdapter(TableExtractorPort):
    """
    Adaptador para extracción de tablas que utiliza pdfplumber.
    
    Implementación con imports perezosos (lazy) para no requerir
    dependencias pesadas durante importación del módulo ni en tests.
    """

    def extract_tables(self, pdf_path: Path) -> List[Any]:
        """
        Extrae todas las tablas detectadas en un documento PDF.
        
        Si pdfplumber o pandas no están disponibles, retorna una lista vacía
        sin fallar.
        """
        # Verificar disponibilidad de dependencias
        if importlib.util.find_spec('pdfplumber') is None or importlib.util.find_spec('pandas') is None:
            return []
        
        pdfplumber = importlib.import_module('pdfplumber')
        pd = importlib.import_module('pandas')

        dfs: List[Any] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables() or []
                    for table in tables:
                        try:
                            df = pd.DataFrame(table)
                            if self._is_valid_table(df):
                                dfs.append(df)
                        except Exception:
                            # Si una tabla falla al convertir, continuar con el resto
                            continue
        except Exception:
            # Si el PDF está corrupto o no se puede abrir, retornar vacío
            return []
        return dfs
    
    def _is_valid_table(self, df: Any) -> bool:
        """Heurísticas simples para descartar tablas triviales."""
        try:
            # Debe comportarse como DataFrame
            shape = getattr(df, 'shape', None)
            if not shape or shape[0] < 2 or shape[1] < 2:
                return False
            rows, cols = shape
            total_cells = rows * cols
            if total_cells < 8:
                return False
            # Conteo de vacíos (duck-typing compatible)
            isnull = getattr(df, 'isnull', None)
            empty_cells = 0
            if callable(isnull):
                nulls = isnull()
                empty_cells_val = getattr(nulls, 'sum', lambda: 0)()
                try:
                    # pandas devuelve Series/DataFrame; sumar dos veces si aplica
                    empty_cells = int(getattr(empty_cells_val, 'sum', lambda: empty_cells_val)())
                except Exception:
                    empty_cells = 0
            eq_empty = getattr(df, '__eq__', lambda *_: None)('')
            if hasattr(eq_empty, 'sum'):
                try:
                    empty_cells += int(eq_empty.sum())
                except Exception:
                    pass
            if total_cells > 0 and empty_cells / total_cells > 0.6:
                return False
            return True
        except Exception:
            return False