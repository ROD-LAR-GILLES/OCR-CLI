# domain/models.py
"""
Modelos de dominio que representan las entidades principales del negocio.

Este módulo contiene las entidades puras del dominio, libres de dependencias
externas y frameworks específicos. Los modelos definen la estructura y
comportamiento esencial de los conceptos del negocio.

Principios aplicados:
- Domain-Driven Design: Modelos que reflejan el lenguaje del negocio
- Single Responsibility: Cada modelo tiene una responsabilidad clara
- Immutability: Modelos inmutables para garantizar consistencia
- Type Safety: Uso de type hints para claridad y validación
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Any


@dataclass
class Document:
    """
    Entidad que representa un documento procesado en el sistema.
    
    Esta entidad encapsula toda la información extraída de un documento PDF
    después del procesamiento completo, incluyendo tanto texto como datos
    estructurados (tablas).
    
    Responsabilidades:
    - Mantener la integridad de los datos extraídos
    - Proporcionar una representación unificada del documento
    - Servir como modelo de datos para persistencia y transferencia
    - Mantener la trazabilidad hacia el archivo original
    
    Casos de uso:
    - Transferencia de datos entre capas de la aplicación
    - Serialización/deserialización para APIs REST
    - Persistencia en bases de datos
    - Análisis y transformación de contenido
    
    Future Extensions:
    - metadata: Dict con información adicional (fecha procesamiento, versión OCR, etc.)
    - pages: List[Page] para análisis granular por página
    - confidence_scores: Métricas de confianza del OCR
    - language: Idioma detectado del documento
    """
    
    name: str
    """
    Nombre identificador del documento.
    
    Típicamente el nombre del archivo original sin extensión.
    Usado para generar nombres de archivos de salida y como
    clave de identificación en el sistema.
    
    Example: "reporte_financiero_2024"
    """
    
    text: str
    """
    Texto completo extraído del documento mediante OCR.
    
    Contiene todo el contenido textual del PDF, con páginas
    separadas por saltos de línea. Preserva el formato original
    en la medida de lo posible.
    
    Características:
    - Codificación UTF-8
    - Separadores de página consistentes
    - Espacios en blanco preservados para mantener estructura
    - Caracteres especiales manejados correctamente
    
    Example: "TÍTULO DEL DOCUMENTO\n\nPrimera página...\n\n\nSegunda página..."
    """
    
    tables: List[Any]
    """
    Lista de tablas extraídas del documento.
    
    Cada elemento representa una tabla detectada, típicamente
    como pandas.DataFrame pero el tipo Any permite flexibilidad
    para diferentes implementaciones de extracción.
    
    Características:
    - Orden corresponde a aparición en el documento
    - Estructura tabular preservada (filas/columnas)
    - Metadatos de posición cuando estén disponibles
    - Lista vacía si no se detectan tablas
    
    Formatos soportados:
    - pandas.DataFrame: Para análisis estadístico y manipulación
    - List[List[str]]: Para casos simples de tabla
    - Dict structures: Para tablas con metadatos complejos
    
    Example: [DataFrame(...), DataFrame(...)] para documento con 2 tablas
    """
    
    source: Path
    """
    Ruta al archivo PDF original que generó este documento.
    
    Mantiene la trazabilidad hacia el archivo fuente para:
    - Auditoría y verificación
    - Reprocesamiento si es necesario
    - Referencia para análisis manual
    - Backup y archivado
    
    Debe ser una ruta absoluta válida y accesible en el momento
    de creación del modelo.
    
    Example: Path("/data/inputs/reporte_financiero_2024.pdf")
    """
    
    def __post_init__(self) -> None:
        """
        Validaciones post-inicialización del modelo.
        
        Ejecuta validaciones de integridad después de la creación
        del objeto para garantizar que los datos son consistentes
        y válidos.
        
        Validaciones aplicadas:
        - Nombre no vacío y válido para nombres de archivo
        - Texto no nulo (puede estar vacío si OCR falló)
        - Lista de tablas inicializada (aunque esté vacía)
        - Archivo fuente existe y es accesible
        
        Raises:
            ValueError: Si alguna validación falla
            FileNotFoundError: Si el archivo fuente no existe
        """
        # Validación: nombre debe ser válido para crear archivos
        if not self.name or not self.name.strip():
            raise ValueError("Document name cannot be empty")
            
        # Validación: texto debe estar inicializado (aunque esté vacío)
        if self.text is None:
            raise ValueError("Document text cannot be None")
            
        # Validación: lista de tablas debe estar inicializada
        if self.tables is None:
            self.tables = []
            
        # Validación: archivo fuente debe existir
        if not self.source.exists():
            raise FileNotFoundError(f"Source file not found: {self.source}")
    
    @property
    def has_tables(self) -> bool:
        """
        Indica si el documento contiene tablas extraídas.
        
        Returns:
            bool: True si se detectaron y extrajeron tablas, False en caso contrario
        """
        return len(self.tables) > 0
    
    @property
    def table_count(self) -> int:
        """
        Número de tablas extraídas del documento.
        
        Returns:
            int: Cantidad de tablas detectadas en el documento
        """
        return len(self.tables)
    
    @property
    def word_count(self) -> int:
        """
        Aproximación del número de palabras en el texto extraído.
        
        Útil para:
        - Métricas de procesamiento
        - Estimación de tiempo de lectura
        - Validación de calidad de OCR
        
        Returns:
            int: Número aproximado de palabras en el texto
        """
        return len(self.text.split()) if self.text else 0