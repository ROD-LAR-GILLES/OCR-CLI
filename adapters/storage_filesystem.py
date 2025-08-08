# adapters/storage_filesystem.py
"""
Adaptador de almacenamiento basado en sistema de archivos local.

Este módulo implementa el puerto StoragePort para persistir los resultados
del procesamiento OCR en el sistema de archivos local, generando múltiples
formatos de salida para diferentes casos de uso.
"""
import shutil
from pathlib import Path
from typing import List, Any, Tuple
from datetime import datetime

from application.ports import StoragePort


class FileStorage(StoragePort):
    """
    Adaptador de almacenamiento que persiste resultados en el sistema de archivos.
    
    NUEVA FUNCIONALIDAD: Crea una carpeta dedicada por cada documento procesado
    para mejor organización y evitar conflictos de archivos.
    
    Esta implementación genera múltiples formatos de salida organizados por documento:
    
    Estructura de directorios:
    resultado/
    ├── documento1/
    │   ├── texto_completo.txt           <- Texto plano extraído por OCR
    │   ├── documento1.md                <- Documento Markdown con texto y tablas
    │   └── documento1_original.pdf      <- Copia del archivo original
    └── documento2/
        ├── texto_completo.txt
        ├── documento2.md
        └── documento2_original.pdf
    
    Ventajas de la organización por carpetas:
    - Evita conflictos de nombres entre documentos
    - Facilita el backup y archivado por documento
    - Permite procesamiento de múltiples archivos con el mismo nombre
    - Estructura más clara para herramientas de automatización
    - Mejor integración con sistemas de versionado
    
    Formatos generados por documento:
    1. texto_completo.txt - Texto plano extraído por OCR (legible por humanos)
    2. [nombre].md - Documento Markdown estructurado con texto y tablas (documentación)
    3. [nombre]_original.pdf - Copia del archivo original (trazabilidad)
    
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

    def _table_to_markdown(self, table: Any) -> str:
        """Convierte una estructura tipo tabla a Markdown, con fallback sin tabulate."""
        # Intentar usar tabulate si está disponible
        try:
            from tabulate import tabulate  # type: ignore
        except Exception:
            tabulate = None  # type: ignore
        
        if tabulate is not None:
            try:
                rows = getattr(table, 'values', None)
                headers = getattr(table, 'columns', None)
                if rows is not None and headers is not None:
                    return tabulate(rows, headers=headers, tablefmt="pipe")
                return tabulate(table, tablefmt="pipe", headers="keys")
            except Exception:
                pass
        
        # Fallback: construir Markdown simple
        try:
            # Si parece una lista de listas
            if isinstance(table, list):
                rows = table
                if not rows:
                    return ""
                # Encabezados básicos de columnas enumeradas
                cols = max(len(r) for r in rows)
                header = [f"Col{i+1}" for i in range(cols)]
                sep = ["---" for _ in range(cols)]
                lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
                for r in rows:
                    padded = list(r) + [""] * (cols - len(r))
                    lines.append("| " + " | ".join(map(str, padded)) + " |")
                return "\n".join(lines)
        except Exception:
            pass
        
        # Último recurso
        return str(table)

    def save(self, name: str, text: str, tables: List[Any], original: Path) -> List[str]:
        """
        Persiste los resultados del procesamiento en múltiples formatos dentro de una carpeta específica.
        
        NUEVA LÓGICA: Crea una carpeta por documento procesado y organiza todos
        los archivos resultantes dentro de esa carpeta para mejor organización.
        
        Genera una suite completa de archivos de salida para diferentes casos de uso:
        - Análisis manual (TXT legible)
        - Documentación estructurada (Markdown formateado) 
        - Trazabilidad (PDF original)
        
        Args:
            name (str): Nombre base para los archivos generados (sin extensión)
            text (str): Texto completo extraído por OCR
            tables (List[Any]): Lista de estructuras tipo tabla detectadas
            original (Path): Ruta al archivo PDF original
            
        Returns:
            List[str]: Lista de rutas de todos los archivos generados
            
        Estructura de archivos generados:
            resultado/
            └── documento/
                ├── texto_completo.txt          <- Texto completo OCR
                ├── documento.md                <- Documento Markdown estructurado
                └── documento_original.pdf      <- Copia del PDF original
            
        Raises:
            OSError: Si hay problemas de permisos o espacio en disco
        """
        # Crear carpeta específica para este documento
        document_folder = self.out_dir / name
        document_folder.mkdir(parents=True, exist_ok=True)
        
        archivos_generados: List[str] = []

        # 1. TEXTO PLANO
        texto_path = document_folder / "texto_completo.txt"
        texto_path.write_text(text, encoding="utf-8")
        archivos_generados.append(str(texto_path))

        # 2. ARCHIVO MARKDOWN
        markdown_content = f"# Documento Procesado: {name}\n\n"
        markdown_content += "## Texto Extraído\n\n"
        markdown_content += (text or "") + "\n\n"
        
        if tables:
            markdown_content += "## Tablas Extraídas\n\n"
            for i, table in enumerate(tables, start=1):
                try:
                    # Omitir tablas vacías si el objeto lo expone
                    if getattr(table, 'empty', False):
                        continue
                    table_md = self._table_to_markdown(table)
                    if table_md.strip():
                        markdown_content += f"### Tabla {i}\n\n{table_md}\n\n"
                except Exception:
                    markdown_content += f"### Tabla {i}\n\n(No se pudo renderizar la tabla)\n\n"
        
        markdown_path = document_folder / f"{name}.md"
        markdown_path.write_text(markdown_content, encoding="utf-8")
        archivos_generados.append(str(markdown_path))

        # 3. COPIA DEL PDF ORIGINAL
        pdf_copy_path = document_folder / f"{name}_original.pdf"
        import shutil as _sh
        _sh.copy(original, pdf_copy_path)
        archivos_generados.append(str(pdf_copy_path))
        
        return archivos_generados
    
    def save_document(self, document) -> Tuple[str, List[str]]:
        """
        Guarda un documento completo con todas sus métricas y metadatos.
        
        Args:
            document: Instancia de Document con OCRResult y métricas
            
        Returns:
            Tuple[str, List[str]]: Directorio de salida y lista de archivos generados
        """
        archivos_generados = self.save(
            document.name,
            document.extracted_text,
            document.tables,
            document.source_path
        )
        
        # Métricas opcionales
        try:
            if getattr(document, 'ocr_result', None):
                import json
                document_folder = self.out_dir / document.name
                metrics_path = document_folder / f"{document.name}_metrics.json"
                metrics_data = {
                    'processing_summary': getattr(document, 'processing_summary', {}),
                }
                with open(metrics_path, 'w', encoding='utf-8') as f:
                    json.dump(metrics_data, f, indent=2, ensure_ascii=False)
                archivos_generados.append(str(metrics_path))
        except Exception:
            pass
        
        return str(self.out_dir / document.name), archivos_generados