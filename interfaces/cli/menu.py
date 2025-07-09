# interfaces/cli/menu.py
"""
Interfaz de línea de comandos interactiva para OCR-CLI.

Este módulo implementa la interfaz de usuario principal de la aplicación,
proporcionando un menú interactivo elegante para el procesamiento de
documentos PDF en entorno Docker.

Responsabilidades:
- Descubrimiento automático de archivos PDF disponibles
- Presentación de menú interactivo para selección de documentos
- Orquestación del procesamiento usando casos de uso
- Feedback en tiempo real del progreso y resultados
- Manejo graceful de errores y casos límite

Tecnologías utilizadas:
- questionary: Menús interactivos elegantes con navegación por teclado
- pathlib: Manipulación moderna y multiplataforma de rutas
- Docker volumes: Integración con sistema de archivos containerizado
"""

from pathlib import Path
import questionary
from adapters.ocr_tesseract import TesseractAdapter
from adapters.table_pdfplumber import PdfPlumberAdapter
from adapters.storage_filesystem import FileStorage
from application.use_cases import ProcessDocument

# Configuración de directorios Docker
# Estos paths son montados como volúmenes en docker-compose.yml
PDF_DIR = Path("/pdfs")            # ← Directorio de entrada (host: ./pdfs)
OUT_DIR = Path("/app/resultado")   # ← Directorio de salida (host: ./resultado)


def listar_pdfs() -> list[str]:
    """
    Descubre y lista todos los archivos PDF disponibles para procesamiento.
    
    Escanea el directorio de entrada en busca de archivos PDF y los
    ordena alfabéticamente para presentación consistente al usuario.
    
    Returns:
        list[str]: Lista ordenada de nombres de archivos PDF encontrados.
                   Lista vacía si no hay archivos PDF en el directorio.
    
    Example:
        >>> archivos = listar_pdfs()
        >>> print(archivos)
        ['documento1.pdf', 'reporte_financiero.pdf', 'tabla_datos.pdf']
    
    Note:
        - Usa glob pattern "*.pdf" para filtrar solo archivos PDF
        - Retorna solo nombres de archivo, no rutas completas
        - Ordenamiento alfabético garantiza experiencia de usuario consistente
        - Ignora archivos ocultos (que empiecen con .)
    """
    # Path.glob() encuentra archivos que coinciden con el patrón
    # "*.pdf" busca cualquier archivo terminado en .pdf
    # sorted() ordena alfabéticamente para UX consistente
    return sorted([p.name for p in PDF_DIR.glob("*.pdf")])


def procesar_archivo(nombre: str):
    """
    Ejecuta el procesamiento completo de un archivo PDF específico.
    
    Esta función orquesta todo el flujo de procesamiento:
    1. Configura las dependencias necesarias (adaptadores)
    2. Instancia el caso de uso con inyección de dependencias
    3. Ejecuta el procesamiento completo
    4. Proporciona feedback detallado del resultado
    
    Args:
        nombre (str): Nombre del archivo PDF a procesar (debe existir en PDF_DIR)
    
    Proceso de ejecución:
    1. Construcción de ruta completa al archivo PDF
    2. Configuración de adaptadores específicos:
       - TesseractAdapter: OCR con idioma español y DPI 300
       - PdfPlumberAdapter: Extracción de tablas estructuradas
       - FileStorage: Persistencia en sistema de archivos
    3. Ejecución del caso de uso ProcessDocument
    4. Presentación de resultados al usuario
    
    Example:
        >>> procesar_archivo("documento.pdf")
        
        documento.pdf procesado.
           - Texto:     ['/app/resultado/documento.txt']
           - JSON:      /app/resultado/documento.txt
    
    Error Handling:
        - FileNotFoundError: Si el archivo PDF no existe
        - OCRError: Si el proceso de OCR falla
        - StorageError: Si hay problemas al guardar resultados
        
    Performance Notes:
        - El tiempo de procesamiento depende del tamaño y complejidad del PDF
        - OCR es la operación más lenta (puede tomar minutos para documentos grandes)
        - El progreso se muestra en tiempo real
    """
    # Construye la ruta completa al archivo PDF
    pdf_path = PDF_DIR / nombre
    
    # CONFIGURACIÓN DE DEPENDENCIAS
    # Implementa el patrón de Inyección de Dependencias para máxima flexibilidad
    
    # TesseractAdapter: Configuración optimizada para documentos en español
    # - lang="spa": Modelo de idioma español para mejor precisión
    # - dpi=300: Balance óptimo entre calidad y velocidad
    ocr_adapter = TesseractAdapter()
    
    # PdfPlumberAdapter: Extracción de tablas de PDFs nativos
    # Ideal para documentos generados digitalmente (vs escaneados)
    table_adapter = PdfPlumberAdapter()
    
    # FileStorage: Persistencia local con múltiples formatos de salida
    # Genera archivos TXT, JSON, ASCII para diferentes casos de uso
    storage_adapter = FileStorage(OUT_DIR)
    
    # INSTANCIACIÓN DEL CASO DE USO
    # ProcessDocument orquesta todo el flujo de procesamiento
    # Las dependencias se inyectan via constructor (Dependency Injection)
    interactor = ProcessDocument(
        ocr=ocr_adapter,
        table_extractor=table_adapter,
        storage=storage_adapter,
    )
    
    # EJECUCIÓN DEL PROCESAMIENTO
    # El caso de uso es callable (__call__), implementando Command Pattern
    # Retorna rutas de archivos generados para feedback al usuario
    texto_principal, archivos_generados = interactor(pdf_path)
    
    # FEEDBACK AL USUARIO
    # Presenta resultados de forma clara y actionable
    print(f"\n{nombre} procesado.")
    print(f"   - Texto:     {archivos_generados}")
    print(f"   - JSON:      {texto_principal}\n")


def main():
    """
    Función principal que ejecuta el bucle interactivo de la aplicación.
    
    Implementa el bucle principal de la interfaz de usuario:
    1. Descubrimiento de archivos PDF disponibles
    2. Presentación de menú interactivo
    3. Procesamiento de selección del usuario
    4. Repetición hasta que el usuario elija salir
    
    Características de UX:
    - Menú elegante con navegación por flechas del teclado
    - Opción de salida clara (Esc o seleccionar "Salir")
    - Validación automática de archivos disponibles
    - Feedback inmediato cuando no hay archivos
    - Loop continuo para procesar múltiples archivos
    
    Flow de la aplicación:
    ```
    Inicio -> Escanear PDFs -> ¿Hay archivos? 
                                    |
                                   No -> Mensaje de error -> Salir
                                    |
                                   Sí -> Mostrar menú -> Selección usuario
                                                              |
                                                         Procesar -> Loop
                                                              |
                                                           Salir -> Fin
    ```
    
    Error Handling:
    - Directorio PDF_DIR no existe: Mensaje informativo
    - Sin archivos PDF: Instrucciones para agregar archivos
    - Errores de procesamiento: Capturados y mostrados al usuario
    - Interrupciones de teclado (Ctrl+C): Salida graceful
    
    Docker Integration:
    - PDF_DIR (/pdfs) mapeado como volumen desde host
    - Cambios en directorio host se reflejan inmediatamente
    - No requiere reconstruir imagen para agregar archivos
    """
    # Bucle principal de la aplicación
    while True:
        # DESCUBRIMIENTO DE ARCHIVOS
        # Escanea el directorio montado en busca de PDFs disponibles
        archivos = listar_pdfs()
        
        # VALIDACIÓN DE DISPONIBILIDAD
        # Si no hay archivos, informa al usuario y termina gracefully
        if not archivos:
            print("No hay PDFs en /pdfs. Añade archivos y reconstruye la imagen.")
            break

        # PRESENTACIÓN DEL MENÚ INTERACTIVO
        # questionary.select() crea un menú elegante con:
        # - Navegación con flechas ↑↓
        # - Selección con Enter
        # - Salida con Esc
        # - Búsqueda incremental por tipeo
        choice = questionary.select(
            "Selecciona un PDF para procesar (Esc → salir):",
            choices=archivos + ["Salir"],  # Agrega opción de salida explícita
        ).ask()

        # PROCESAMIENTO DE SELECCIÓN
        # Verifica que el usuario seleccionó un archivo válido
        if choice and choice.endswith(".pdf"):
            # Ejecuta procesamiento completo del archivo seleccionado
            procesar_archivo(choice)
        else:
            # Usuario seleccionó "Salir" o presionó Esc
            break


if __name__ == "__main__":
    """
    Punto de entrada cuando el módulo se ejecuta directamente.
    
    Permite ejecutar la aplicación con:
    python interfaces/cli/menu.py
    
    En el contexto Docker, este es el comando por defecto definido
    en el Dockerfile, ejecutándose automáticamente al iniciar el contenedor.
    """
    main()