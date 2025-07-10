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
import pandas as pd
from tabulate import tabulate
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
            tables (List[Any]): Lista de DataFrames con las tablas detectadas
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
        
        archivos_generados = []

        # 1. TEXTO PLANO - Para lectura humana y análisis manual
        # Guarda el texto completo extraído por OCR en formato UTF-8
        # Útil para: búsquedas de texto, análisis de contenido, revisión manual
        texto_path = document_folder / "texto_completo.txt"
        texto_path.write_text(text, encoding="utf-8")
        archivos_generados.append(str(texto_path))

        # 2. ARCHIVO MARKDOWN - Para documentación estructurada
        # Genera un archivo Markdown que replica la estructura original del documento
        # Las tablas se integran en su posición original dentro del texto
        markdown_content = f"# Documento Procesado: {name}\n\n"
        
        if tables:
            # Integrar tablas en su posición original dentro del texto
            integrated_text = self._integrate_tables_in_text_simple(text, tables)
            markdown_content += integrated_text
        else:
            markdown_content += text
        
        markdown_path = document_folder / f"{name}.md"
        markdown_path.write_text(markdown_content, encoding="utf-8")
        archivos_generados.append(str(markdown_path))

        # 3. COPIA DEL PDF ORIGINAL - Para trazabilidad y referencia
        # Mantiene el archivo original junto con los resultados procesados
        # Útil para: auditoría, comparación, reprocesamiento si es necesario
        pdf_copy_path = document_folder / f"{name}_original.pdf"
        shutil.copy(original, pdf_copy_path)
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
        # Usar el método save existente
        archivos_generados = self.save(
            document.name,
            document.extracted_text,
            document.tables,
            document.source_path
        )
        
        # Generar archivo de métricas adicional si está disponible
        if document.ocr_result:
            document_folder = self.out_dir / document.name
            metrics_path = document_folder / f"{document.name}_metrics.json"
            
            try:
                import json
                metrics_data = {
                    'processing_summary': document.processing_summary,
                    'ocr_metrics': {
                        'quality_score': document.ocr_result.quality_score,
                        'processing_time': document.ocr_result.processing_time,
                        'page_count': document.ocr_result.page_count,
                        'confidence': document.ocr_result.metrics.average_confidence
                    },
                    'document_metadata': document.processing_metadata
                }
                
                with open(metrics_path, 'w', encoding='utf-8') as f:
                    json.dump(metrics_data, f, indent=2, ensure_ascii=False)
                
                archivos_generados.append(str(metrics_path))
            except Exception as e:
                # Si falla, continuar sin el archivo de métricas
                pass
        
        return str(self.out_dir / document.name), archivos_generados

    def _integrate_tables_in_text(self, text: str, tables: List[Any]) -> str:
        """
        Integra las tablas extraídas en su posición original dentro del texto.
        
        Este método busca patrones en el texto OCR que correspondan a datos tabulares
        y los reemplaza con versiones formateadas en markdown, creando una 
        representación fiel del documento original.
        
        Args:
            text (str): Texto completo extraído por OCR
            tables (List[Any]): Lista de DataFrames con las tablas detectadas
            
        Returns:
            str: Texto con tablas integradas en formato markdown
        """
        if not tables:
            return text
            
        # Dividir el texto en líneas para análisis
        lines = text.split('\n')
        result_lines = []
        table_index = 0
        i = 0
        
        while i < len(lines) and table_index < len(tables):
            line = lines[i].strip()
            
            # Detectar inicio de una tabla buscando patrones característicos
            if self._is_table_start_line(line):
                # Encontrar el rango de líneas que corresponden a esta tabla
                table_end = self._find_table_end(lines, i)
                
                # Extraer los datos de la tabla del texto OCR
                table_text_lines = lines[i:table_end+1]
                
                # Verificar si esta sección coincide con alguna tabla extraída
                matching_table_idx = self._find_matching_table(table_text_lines, tables[table_index:])
                
                if matching_table_idx >= 0:
                    # Reemplazar el texto de la tabla con la versión formateada
                    actual_table_idx = table_index + matching_table_idx
                    table_markdown = self._format_table_for_integration(tables[actual_table_idx])
                    result_lines.append(table_markdown)
                    
                    # Saltar las líneas que formaban parte de la tabla original
                    i = table_end + 1
                    table_index = actual_table_idx + 1
                else:
                    # No se encontró coincidencia, mantener el texto original
                    result_lines.append(line)
                    i += 1
            else:
                # Línea normal, mantener tal como está
                result_lines.append(line)
                i += 1
        
        # Agregar líneas restantes si las hay
        while i < len(lines):
            result_lines.append(lines[i])
            i += 1
            
        return '\n'.join(result_lines)
    
    def _is_table_start_line(self, line: str) -> bool:
        """
        Detecta si una línea marca el inicio de una tabla.
        
        Args:
            line (str): Línea de texto a evaluar
            
        Returns:
            bool: True si la línea parece iniciar una tabla
        """
        line = line.strip().upper()
        
        # Patrones que suelen indicar el inicio de una tabla
        table_indicators = [
            'ITEM',
            'DETALLE', 
            'UNIDAD',
            'VALOR',
            'CÓDIGO',
            'DESCRIPCIÓN',
            'PRECIO',
            'CANTIDAD'
        ]
        
        # La línea debe contener al menos 2 indicadores de tabla
        indicators_found = sum(1 for indicator in table_indicators if indicator in line)
        
        # También verificar si hay múltiples elementos separados por espacios
        words = line.split()
        has_multiple_columns = len(words) >= 3
        
        return indicators_found >= 2 or (indicators_found >= 1 and has_multiple_columns)
    
    def _find_table_end(self, lines: List[str], start_idx: int) -> int:
        """
        Encuentra el índice de la última línea que pertenece a la tabla.
        
        Args:
            lines (List[str]): Todas las líneas del texto
            start_idx (int): Índice donde inicia la tabla
            
        Returns:
            int: Índice de la última línea de la tabla
        """
        i = start_idx + 1
        consecutive_empty_lines = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                consecutive_empty_lines += 1
                # Si hay 2 líneas vacías consecutivas, probablemente terminó la tabla
                if consecutive_empty_lines >= 2:
                    return i - 2
            else:
                consecutive_empty_lines = 0
                
                # Si la línea parece ser el inicio de otra sección (notas, etc.)
                if self._is_section_start(line):
                    return i - 1
                    
                # Si la línea no tiene estructura tabular, podría ser el final
                if not self._has_tabular_structure(line):
                    # Buscar un poco más para confirmar
                    if i + 1 < len(lines) and not self._has_tabular_structure(lines[i + 1].strip()):
                        return i - 1
            
            i += 1
        
        return min(i - 1, len(lines) - 1)
    
    def _is_section_start(self, line: str) -> bool:
        """
        Detecta si una línea marca el inicio de una nueva sección.
        
        Args:
            line (str): Línea a evaluar
            
        Returns:
            bool: True si parece iniciar una nueva sección
        """
        line_lower = line.lower()
        section_indicators = [
            'notas:',
            'fuentes:',
            'observaciones:',
            'metodología:',
            'nota:',
            'fuente:'
        ]
        
        return any(indicator in line_lower for indicator in section_indicators)
    
    def _has_tabular_structure(self, line: str) -> bool:
        """
        Evalúa si una línea tiene estructura tabular (múltiples elementos separados).
        
        Args:
            line (str): Línea a evaluar
            
        Returns:
            bool: True si la línea parece tener estructura tabular
        """
        if not line.strip():
            return False
            
        # Contar elementos que parecen ser columnas
        words = line.split()
        
        # Buscar patrones numéricos o códigos que sugieran datos tabulares
        numeric_pattern = any(word.replace('.', '').replace(',', '').replace('-', '').isdigit() 
                            for word in words)
        
        # Si tiene al menos 2 elementos y al menos uno es numérico
        return len(words) >= 2 and numeric_pattern
    
    def _find_matching_table(self, table_text_lines: List[str], available_tables: List[Any]) -> int:
        """
        Encuentra qué tabla extraída corresponde mejor al texto dado.
        
        Args:
            table_text_lines (List[str]): Líneas de texto que forman la tabla
            available_tables (List[Any]): Tablas disponibles para comparar
            
        Returns:
            int: Índice de la tabla que mejor coincide, -1 si no hay coincidencia
        """
        if not available_tables:
            return -1
            
        # Extraer palabras clave del texto de la tabla
        table_text = ' '.join(table_text_lines).lower()
        table_words = set(table_text.split())
        
        best_match_idx = -1
        best_score = 0
        
        for idx, df in enumerate(available_tables):
            # Extraer texto de la tabla DataFrame
            df_text = ' '.join(df.astype(str).values.flatten()).lower()
            df_words = set(df_text.split())
            
            # Calcular similaridad (intersección de palabras)
            common_words = table_words.intersection(df_words)
            if len(table_words) > 0:
                similarity = len(common_words) / len(table_words)
                
                if similarity > best_score and similarity > 0.3:  # Al menos 30% de similitud
                    best_score = similarity
                    best_match_idx = idx
        
        return best_match_idx
    
    def _format_table_for_integration(self, df: Any) -> str:
        """
        Formatea una tabla para integración en el texto markdown.
        
        Args:
            df: DataFrame de la tabla
            
        Returns:
            str: Tabla formateada en markdown
        """
        # Formatear la tabla con un estilo limpio
        table_markdown = tabulate(df, tablefmt="pipe", headers="keys", showindex=False)
        
        # Agregar líneas en blanco para separación visual
        return f"\n{table_markdown}\n"
    
    def _integrate_tables_in_text_simple(self, text: str, tables: List[Any]) -> str:
        """
        Integra las tablas en el texto de forma más directa y simple.
        
        Busca patrones de texto que correspondan a datos tabulares
        y los reemplaza con tablas formateadas en markdown.
        
        Args:
            text (str): Texto completo extraído por OCR
            tables (List[Any]): Lista de DataFrames con las tablas detectadas
            
        Returns:
            str: Texto con tablas integradas en formato markdown
        """
        if not tables:
            return text
        
        # Dividir el texto en líneas
        lines = text.split('\n')
        result_lines = []
        table_inserted = [False] * len(tables)  # Track which tables have been inserted
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Buscar la primera tabla: líneas que empiecen con "ITEM DETALLE UNIDAD VALOR"
            if "ITEM" in line.upper() and "DETALLE" in line.upper() and "UNIDAD" in line.upper() and "VALOR" in line.upper():
                # Encontrar qué tabla corresponde a esta sección
                table_idx = self._find_best_table_match(lines, i, tables, table_inserted)
                
                if table_idx >= 0 and not table_inserted[table_idx]:
                    # Formatear la tabla
                    table_markdown = self._format_table_clean(tables[table_idx])
                    result_lines.append(table_markdown)
                    table_inserted[table_idx] = True
                    
                    # Saltar las líneas de datos que ahora están en la tabla
                    i = self._skip_table_data_lines(lines, i)
                else:
                    result_lines.append(line)
                    i += 1
            else:
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
    
    def _find_best_table_match(self, lines: List[str], start_idx: int, tables: List[Any], table_inserted: List[bool]) -> int:
        """
        Encuentra la tabla que mejor corresponde a la sección de texto.
        
        Args:
            lines (List[str]): Líneas del texto
            start_idx (int): Índice donde inicia la sección tabular
            tables (List[Any]): Tablas disponibles
            table_inserted (List[bool]): Tablas ya insertadas
            
        Returns:
            int: Índice de la tabla que mejor coincide, -1 si no hay coincidencia
        """
        # Extraer las siguientes 10-15 líneas para analizar
        section_lines = lines[start_idx:start_idx + 15]
        section_text = ' '.join(section_lines).lower()
        
        best_match = -1
        best_score = 0
        
        for idx, table in enumerate(tables):
            if table_inserted[idx]:
                continue
                
            # Convertir la tabla a texto para comparar
            table_text = ' '.join(table.astype(str).values.flatten()).lower()
            
            # Buscar palabras clave comunes
            table_words = set(table_text.split())
            section_words = set(section_text.split())
            common_words = table_words.intersection(section_words)
            
            if len(section_words) > 0:
                score = len(common_words) / len(section_words)
                if score > best_score and score > 0.2:  # Al menos 20% de similitud
                    best_score = score
                    best_match = idx
        
        return best_match
    
    def _skip_table_data_lines(self, lines: List[str], start_idx: int) -> int:
        """
        Salta las líneas que contienen datos tabulares.
        
        Args:
            lines (List[str]): Todas las líneas del texto
            start_idx (int): Índice donde inicia la tabla
            
        Returns:
            int: Índice de la siguiente línea después de la tabla
        """
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Si la línea está vacía o es muy corta, continuar
            if not line or len(line) < 5:
                i += 1
                continue
            
            # Si la línea empieza a ser texto narrativo (notas, etc.), parar
            if any(keyword in line.lower() for keyword in ['notas:', 'nota:', 'fuentes:', 'fuente:', 'observaciones:']):
                break
                
            # Si la línea no parece tener estructura tabular, parar
            words = line.split()
            has_numbers = any(word.replace('.', '').replace(',', '').replace('-', '').isdigit() for word in words)
            
            if len(words) < 2 or not has_numbers:
                # Buscar un poco más para confirmar
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    next_words = next_line.split()
                    next_has_numbers = any(word.replace('.', '').replace(',', '').replace('-', '').isdigit() for word in next_words)
                    
                    if len(next_words) < 2 or not next_has_numbers:
                        break
            
            i += 1
        
        return i
    
    def _format_table_clean(self, df: Any) -> str:
        """
        Formatea una tabla de forma limpia para integración en el texto.
        
        Args:
            df: DataFrame de la tabla
            
        Returns:
            str: Tabla formateada en markdown
        """
        # Crear tabla limpia sin índices numéricos
        clean_df = df.copy()
        
        # Si la primera columna son solo números secuenciales (0,1,2,3...), usar como headers
        if len(clean_df) > 0:
            first_row = clean_df.iloc[0]
            if all(str(val).strip() for val in first_row):
                # Usar primera fila como headers
                headers = [str(val).strip() for val in first_row]
                clean_df = clean_df.iloc[1:].reset_index(drop=True)
                clean_df.columns = headers
        
        # Formatear con estilo pipe markdown sin índices de fila
        table_markdown = tabulate(clean_df, tablefmt="pipe", headers="keys", showindex=False)
        
        return f"\n{table_markdown}\n"