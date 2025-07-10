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
from adapters.ocr_tesseract_opencv import TesseractOpenCVAdapter
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
    
    Esta función permite al usuario elegir entre diferentes motores de OCR:
    - TesseractAdapter: OCR básico y rápido
    - TesseractOpenCVAdapter: OCR avanzado con preprocesamiento OpenCV
    
    El usuario puede configurar las opciones de preprocesamiento según
    la calidad del documento a procesar.
    
    Args:
        nombre (str): Nombre del archivo PDF a procesar (debe existir en PDF_DIR)
    """
    # Construye la ruta completa al archivo PDF
    pdf_path = PDF_DIR / nombre
    
    # SELECCIÓN DEL MOTOR OCR
    # Permite al usuario elegir entre adaptadores disponibles
    ocr_choice = questionary.select(
        "Selecciona el motor de OCR:",
        choices=[
            "Tesseract básico (rápido)",
            "Tesseract + OpenCV (alta calidad)",
            "Volver al menú principal"
        ]
    ).ask()
    
    if not ocr_choice or ocr_choice == "Volver al menú principal":
        return
    
    # CONFIGURACIÓN DEL ADAPTADOR OCR
    if ocr_choice == "Tesseract básico (rápido)":
        # TesseractAdapter: Configuración básica optimizada para velocidad
        ocr_adapter = TesseractAdapter()
        print(f"\n🔤 Usando Tesseract básico...")
        
    elif ocr_choice == "Tesseract + OpenCV (alta calidad)":
        # TesseractOpenCVAdapter: Configuración avanzada con preprocesamiento
        print(f"\n🔧 Configurando preprocesamiento OpenCV...")
        
        # Permitir al usuario personalizar el preprocesamiento
        advanced_config = questionary.confirm(
            "¿Configurar opciones avanzadas de preprocesamiento?"
        ).ask()
        
        if advanced_config:
            # Configuración granular de OpenCV
            enable_deskewing = questionary.confirm(
                "¿Corregir inclinación del documento? (recomendado para escaneos)"
            ).ask()
            
            enable_denoising = questionary.confirm(
                "¿Aplicar eliminación de ruido? (recomendado para imágenes de baja calidad)"
            ).ask()
            
            enable_contrast = questionary.confirm(
                "¿Mejorar contraste automáticamente? (recomendado para documentos con poca iluminación)"
            ).ask()
            
            ocr_adapter = TesseractOpenCVAdapter(
                enable_deskewing=enable_deskewing,
                enable_denoising=enable_denoising,
                enable_contrast_enhancement=enable_contrast,
            )
        else:
            # Configuración por defecto: todas las mejoras activadas
            ocr_adapter = TesseractOpenCVAdapter()
            
        print(f"🎯 Usando Tesseract + OpenCV con preprocesamiento avanzado...")
        
        # Mostrar configuración aplicada
        config_info = ocr_adapter.get_preprocessing_info()
        print(f"   - Corrección de inclinación: {'✅' if config_info['deskewing_enabled'] else '❌'}")
        print(f"   - Eliminación de ruido: {'✅' if config_info['denoising_enabled'] else '❌'}")
        print(f"   - Mejora de contraste: {'✅' if config_info['contrast_enhancement_enabled'] else '❌'}")
        print(f"   - OpenCV versión: {config_info['opencv_version']}")
    
    # CONFIGURACIÓN DE ADAPTADORES AUXILIARES
    # PdfPlumberAdapter: Extracción de tablas de PDFs nativos
    table_adapter = PdfPlumberAdapter()
    
    # FileStorage: Persistencia local con múltiples formatos de salida
    storage_adapter = FileStorage(OUT_DIR)
    
    # INSTANCIACIÓN DEL CASO DE USO
    # ProcessDocument orquesta todo el flujo de procesamiento
    interactor = ProcessDocument(
        ocr=ocr_adapter,
        table_extractor=table_adapter,
        storage=storage_adapter,
    )
    
    # EJECUCIÓN DEL PROCESAMIENTO CON MEDICIÓN DE TIEMPO
    print(f"\n🚀 Iniciando procesamiento de {nombre}...")
    import time
    start_time = time.time()
    
    try:
        # Ejecutar procesamiento completo
        texto_principal, archivos_generados = interactor(pdf_path)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        # FEEDBACK DETALLADO AL USUARIO
        print(f"\n✅ {nombre} procesado exitosamente!")
        print(f"⏱️  Tiempo de procesamiento: {processing_time:.2f} segundos")
        print(f"📁 Archivos generados: {len(archivos_generados)}")
        print(f"   - Texto principal: {texto_principal}")
        print(f"   - Todos los archivos: {archivos_generados}")
        
        # Mostrar estadísticas si usamos OpenCV
        if isinstance(ocr_adapter, TesseractOpenCVAdapter):
            print(f"🔬 Preprocesamiento OpenCV aplicado con éxito")
            
    except Exception as e:
        # Manejo de errores con información detallada
        processing_time = time.time() - start_time
        print(f"\n❌ Error procesando {nombre}:")
        print(f"   💥 Error: {str(e)}")
        print(f"   ⏱️  Tiempo hasta error: {processing_time:.2f} segundos")
        print(f"   💡 Sugerencia: Prueba con el motor básico si el documento es de alta calidad")
    
    print()  # Línea en blanco para separación visual


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