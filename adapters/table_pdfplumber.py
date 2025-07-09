# adapters/table_pdfplumber.py
"""
Adaptador de extracción de tablas basado en pdfplumber.

Este módulo implementa el puerto TableExtractorPort utilizando pdfplumber,
una librería especializada en análisis estructural de documentos PDF que
puede detectar y extraer tablas manteniendo su formato original.
"""
from pathlib import Path
from typing import List

import pdfplumber
import pandas as pd

from application.ports import TableExtractorPort


class PdfPlumberAdapter(TableExtractorPort):
    """
    Adaptador para extracción de tablas que utiliza pdfplumber.
    
    pdfplumber es una librería que analiza la estructura interna de PDFs
    para detectar elementos como tablas, texto y metadatos sin necesidad
    de OCR, trabajando directamente con el contenido vectorial del PDF.
    
    Ventajas de pdfplumber:
    - Extracción precisa de tablas con bordes definidos
    - Mantiene la estructura original de celdas
    - Rápido (no requiere conversión a imagen ni OCR)
    - Detecta automáticamente límites de tabla
    - Soporta tablas complejas con celdas combinadas
    
    Limitaciones:
    - Solo funciona con PDFs nativos (no escaneados)
    - Requiere que las tablas tengan estructura clara
    - No funciona con tablas en imágenes incrustadas
    - Problemas con tablas sin bordes o con formato irregular
    
    Casos de uso ideales:
    - Reportes financieros generados digitalmente
    - Documentos empresariales con tablas estructuradas
    - PDFs creados desde Excel, Word, o herramientas similares
    """

    def extract_tables(self, pdf_path: Path) -> List[pd.DataFrame]:
        """
        Extrae todas las tablas detectadas en un documento PDF.
        
        Proceso de extracción:
        1. Abre el PDF y analiza su estructura interna
        2. Recorre cada página buscando elementos tabulares
        3. Para cada tabla detectada, extrae contenido celda por celda
        4. Convierte cada tabla a pandas DataFrame para facilitar manipulación
        
        Args:
            pdf_path (Path): Ruta al archivo PDF a procesar
            
        Returns:
            List[pd.DataFrame]: Lista de DataFrames, uno por cada tabla detectada.
                               Lista vacía si no se encuentran tablas.
                               
        Raises:
            FileNotFoundError: Si el archivo PDF no existe
            pdfplumber.pdf.PdfReadError: Si el PDF está corrupto o protegido
            pandas.errors.EmptyDataError: Si una tabla detectada está vacía
            
        Note:
            - pdfplumber.extract_tables() devuelve listas de listas (filas y columnas)
            - pandas.DataFrame convierte estas listas en estructuras de datos manipulables
            - El orden de las tablas en la lista corresponde al orden de aparición en el PDF
            - Las celdas vacías se representan como None en el DataFrame resultante
        """
        dfs: List[pd.DataFrame] = []
        
        # Abre el PDF usando pdfplumber, que analiza la estructura vectorial
        # del documento sin convertirlo a imagen
        with pdfplumber.open(pdf_path) as pdf:
            # Itera sobre cada página del documento
            for page in pdf.pages:
                # page.extract_tables() detecta automáticamente tablas en la página
                # Utiliza algoritmos de análisis de espaciado y líneas para identificar
                # estructuras tabulares basándose en:
                # - Líneas horizontales y verticales
                # - Espaciado consistente entre elementos
                # - Alineación de texto en columnas
                for table in page.extract_tables():
                    # Convierte cada tabla (lista de listas) a pandas DataFrame
                    # pandas permite manipulación avanzada de datos tabulares:
                    # - Indexado y filtrado
                    # - Operaciones estadísticas
                    # - Exportación a múltiples formatos (JSON, CSV, Excel)
                    # - Limpieza y transformación de datos
                    dfs.append(pd.DataFrame(table))
                    
        return dfs