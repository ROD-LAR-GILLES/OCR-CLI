# adapters/storage_filesystem.py
"""
Adaptador de almacenamiento basado en sistema de archivos local.

Este módulo implementa el puerto StoragePort para persistir los resultados
del procesamiento OCR en el sistema de archivos local, generando múltiples
formatos de salida para diferentes casos de uso.
"""
import json
import shutil
from pathlib import Path
from typing import List, Any
import pandas as pd
from tabulate import tabulate

from application.ports import StoragePort


class FileStorage(StoragePort):
    """
    Adaptador de almacenamiento que persiste resultados en el sistema de archivos.
    
    Esta implementación genera múltiples formatos de salida para maximizar
    la utilidad de los datos procesados:
    
    Formatos generados:
    1. .txt - Texto plano extraído por OCR (legible por humanos)
    2. _table_N.json - Cada tabla como JSON estructurado (integración con APIs)
    3. _tables.txt - Todas las tablas en formato ASCII (visualización rápida)
    4. .pdf - Copia del archivo original (trazabilidad)
    
    Ventajas del almacenamiento en archivos:
    - Simple y rápido de implementar
    - No requiere infraestructura adicional (BD, cloud)
    - Fácil integración con herramientas de línea de comandos
    - Formatos estándar legibles por múltiples aplicaciones
    - Backup y versionado simple con herramientas estándar
    
    Limitaciones:
    - No soporta consultas complejas
    - Sin control de concurrencia
    - Escalabilidad limitada para grandes volúmenes
    - Sin índices para búsqueda rápida
    """

    def __init__(self, out_dir: Path) -> None:
        """
        Inicializa el adaptador de almacenamiento con directorio de salida.
        
        Args:
            out_dir (Path): Directorio donde se guardarán los archivos procesados.
                           Se crea automáticamente si no existe.
                           
        Note:
            - parents=True crea directorios padre si no existen
            - exist_ok=True evita errores si el directorio ya existe
        """
        self.out_dir = out_dir
        # Crea la estructura de directorios de forma segura
        # parents=True equivale a 'mkdir -p' en Unix
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, text: str, tables: List[Any], original: Path) -> None:
        """
        Persiste los resultados del procesamiento en múltiples formatos.
        
        Genera una suite completa de archivos de salida para diferentes casos de uso:
        - Análisis manual (TXT legible)
        - Integración programática (JSON estructurado) 
        - Visualización rápida (ASCII tables)
        - Trazabilidad (PDF original)
        
        Args:
            name (str): Nombre base para los archivos generados (sin extensión)
            text (str): Texto completo extraído por OCR
            tables (List[Any]): Lista de DataFrames con las tablas detectadas
            original (Path): Ruta al archivo PDF original
            
        Estructura de archivos generados:
            documento.txt           <- Texto completo OCR
            documento_table_1.json  <- Primera tabla como JSON
            documento_table_2.json  <- Segunda tabla como JSON
            documento_tables.txt    <- Todas las tablas en ASCII
            documento.pdf          <- Copia del PDF original
            
        Raises:
            OSError: Si hay problemas de permisos o espacio en disco
            json.JSONEncodeError: Si las tablas contienen datos no serializables
        """
        # Genera el nombre base para todos los archivos de salida
        # Path.stem extrae el nombre sin extensión (ej: "documento.pdf" -> "documento")
        base = self.out_dir / name.stem

        # 1. TEXTO PLANO - Para lectura humana y análisis manual
        # Guarda el texto completo extraído por OCR en formato UTF-8
        # Útil para: búsquedas de texto, análisis de contenido, revisión manual
        (base.with_suffix(".txt")).write_text(text, encoding="utf-8")

        # 2. TABLAS COMO JSON - Para integración programática
        # Cada tabla se guarda como archivo JSON independiente usando pandas
        # orient="split" genera JSON con estructura: {"index": [...], "columns": [...], "data": [...]}
        # Ventajas: preserva tipos de datos, fácil de cargar en pandas/numpy
        for i, df in enumerate(tables, start=1):
            json_path = base.with_name(f"{base.stem}_table_{i}.json")
            # pandas.to_json() soporta múltiples formatos:
            # - "split": separado en index, columns, data (recomendado para pandas)
            # - "records": lista de objetos {col1: val1, col2: val2}
            # - "index": objeto con index como keys
            # - "values": solo matriz de valores
            df.to_json(json_path, orient="split")
            
        # 3. TABLAS EN ASCII - Para visualización rápida
        # Genera representación textual legible de todas las tablas
        if tables:
            # tabulate genera tablas ASCII con múltiples estilos:
            # - "github": formato Markdown compatible con GitHub
            # - "grid": bordes completos con caracteres Unicode
            # - "simple": formato minimalista
            # - "pipe": formato Markdown estándar
            # - "html": salida HTML para web
            concat_ascii = "\n\n".join(
                tabulate(df, tablefmt="github") for df in tables
            )
            ascii_path = base.with_name(f"{base.stem}_tables.txt")
            ascii_path.write_text(concat_ascii, "utf-8")

        # 4. COPIA DEL PDF ORIGINAL - Para trazabilidad y referencia
        # Mantiene el archivo original junto con los resultados procesados
        # Útil para: auditoría, comparación, reprocesamiento si es necesario
        shutil.copy(original, base.with_suffix(".pdf"))