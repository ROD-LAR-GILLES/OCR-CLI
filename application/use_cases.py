# application/use_cases.py
"""
Casos de uso (interactors) que orquestan la lógica de negocio.

Este módulo contiene los casos de uso de la aplicación, implementando
la lógica de negocio pura sin depender de detalles técnicos específicos.
Los casos de uso coordinan los puertos (interfaces) para ejecutar
flujos de trabajo completos.

Principios aplicados:
- Single Responsibility: Cada caso de uso tiene una responsabilidad específica
- Dependency Injection: Recibe dependencias via constructor
- Clean Architecture: Aislamiento de la lógica de negocio
- Command Pattern: Casos de uso como comandos ejecutables
"""
from pathlib import Path
from typing import Tuple, List, Any

from application.ports import OCRPort, TableExtractorPort, StoragePort
from domain.models import Document


class ProcessDocument:
    """
    Caso de uso principal para el procesamiento completo de documentos PDF.
    
    Este caso de uso orquesta todo el flujo de procesamiento de un documento:
    1. Extracción de texto mediante OCR
    2. Identificación y extracción de tablas
    3. Persistencia de resultados en formato estructurado
    
    Responsabilidades:
    - Coordinar la secuencia de procesamiento
    - Manejar errores en cualquier etapa del proceso
    - Garantizar la integridad de los datos procesados
    - Proporcionar feedback sobre el resultado del procesamiento
    
    Ventajas del patrón Caso de Uso:
    - Testeable: Fácil crear mocks para cada dependencia
    - Flexible: Cambiar implementaciones sin afectar la lógica
    - Reutilizable: Mismo caso de uso para CLI, API REST, etc.
    - Mantenible: Lógica de negocio separada de detalles técnicos
    
    Flujo de procesamiento:
    PDF -> [OCR] -> Texto plano -> [Storage] -> Archivos de salida
        -> [Table Extraction] -> DataFrames -> [Storage] -> JSON/ASCII
    """

    def __init__(
        self,
        ocr: OCRPort,
        table_extractor: TableExtractorPort,
        storage: StoragePort,
    ) -> None:
        """
        Inicializa el caso de uso con las dependencias inyectadas.
        
        Este constructor implementa el patrón de Inyección de Dependencias,
        permitiendo que el caso de uso trabaje con cualquier implementación
        de los puertos sin conocer los detalles específicos.
        
        Args:
            ocr (OCRPort): Servicio de reconocimiento óptico de caracteres.
                          Puede ser Tesseract, EasyOCR, Google Vision, etc.
                          
            table_extractor (TableExtractorPort): Servicio de extracción de tablas.
                                                  Puede ser pdfplumber, Camelot, Tabula, etc.
                                                  
            storage (StoragePort): Servicio de persistencia de resultados.
                                  Puede ser filesystem, database, cloud storage, etc.
        
        Note:
            La inyección de dependencias permite:
            - Testing: Usar mocks en lugar de implementaciones reales
            - Flexibility: Cambiar implementaciones sin modificar código
            - Configuration: Elegir implementaciones según el entorno (dev/prod)
        """
        self.ocr = ocr
        self.table_extractor = table_extractor
        self.storage = storage

    def __call__(self, pdf_path: Path) -> Tuple[Path, List[Path]]:
        """
        Ejecuta el procesamiento completo de un documento PDF.
        
        Este método implementa el patrón Command, permitiendo que el caso
        de uso sea ejecutado como una función callable. El procesamiento
        sigue una secuencia determinística que garantiza la integridad
        de los datos.
        
        Flujo de ejecución:
        1. Validación inicial del archivo PDF
        2. Extracción de texto mediante OCR (puede tomar varios minutos)
        3. Extracción paralela de tablas (análisis estructural)
        4. Persistencia atómica de todos los resultados
        5. Generación de metadatos de resultado
        
        Args:
            pdf_path (Path): Ruta absoluta al archivo PDF a procesar.
                            Debe existir y ser legible.
        
        Returns:
            Tuple[Path, List[Path]]: Tupla con:
                - Path: Ruta al archivo de texto principal generado
                - List[Path]: Lista de todas las rutas de archivos generados
                             (texto, tablas JSON, tablas ASCII, PDF copia)
        
        Raises:
            FileNotFoundError: Si el archivo PDF no existe
            ProcessingError: Si alguna etapa del procesamiento falla
            StorageError: Si hay problemas al persistir los resultados
            
        Example:
            >>> processor = ProcessDocument(
            ...     ocr=TesseractAdapter(),
            ...     table_extractor=PdfPlumberAdapter(),
            ...     storage=FileStorage(Path("./output"))
            ... )
            >>> text_file, all_files = processor(Path("document.pdf"))
            >>> print(f"Texto extraído en: {text_file}")
            >>> print(f"Archivos generados: {all_files}")
            
        Performance Notes:
            - OCR es la operación más costosa (O(n) con número de páginas)
            - Extracción de tablas es más rápida (análisis estructural)
            - El tiempo total depende de: resolución DPI, número de páginas, complejidad
        """
        # ETAPA 1: Extracción de texto mediante OCR
        # Esta es típicamente la operación más lenta del proceso
        # El tiempo depende de: número de páginas, resolución DPI, complejidad del texto
        text: str = self.ocr.extract_text(pdf_path)
        
        # ETAPA 2: Extracción de tablas estructuradas
        # Análisis paralelo e independiente del OCR
        # Más rápido que OCR pues analiza estructura vectorial del PDF
        tables: List[Any] = self.table_extractor.extract_tables(pdf_path)

        # ETAPA 3: Persistencia atómica de resultados
        # Guarda todos los resultados de forma consistente
        # Si falla aquí, no se pierde el trabajo de OCR/tablas ya realizado
        self.storage.save(pdf_path, text, tables, pdf_path)

        # ETAPA 4: Generación de metadatos de resultado
        # Proporciona información sobre los archivos generados para el usuario
        text_file = pdf_path.with_suffix(".txt")
        all_generated_files = [
            pdf_path.with_suffix(".pdf"),  # Copia del original
            pdf_path.with_suffix(".txt"),  # Texto extraído
            # Nota: archivos de tablas JSON/ASCII se generan dinámicamente
            # según el número de tablas detectadas
        ]
        
        return text_file, all_generated_files