# OCR-CLI - Sistema Unificado de Procesamiento de Documentos

## Descripción General

OCR-CLI es una aplicación de línea de comandos diseñada con arquitectura hexagonal para procesar documentos PDF mediante OCR y extracción de tablas. Sistema completamente unificado y simplificado eliminando duplicación de código.

## Características Principales

### Sistema Unificado
- Un solo menú principal sin duplicidad
- Adaptadores OCR unificados en un solo archivo
- Configuración simplificada sin dependencias complejas
- Casos de uso consolidados básicos y avanzados
- Selección inteligente de tipo de PDF con configuración automática

### Arquitectura Limpia
- Arquitectura hexagonal (puertos y adaptadores)
- Principios SOLID aplicados consistentemente
- Dependency Injection para flexibilidad
- Separación clara de responsabilidades
- Testing facilitado con interfaces bien definidas

## Estructura del Sistema

### Estructura Final Limpia
```
├── adapters/
│   ├── ocr_adapters.py          # TesseractAdapter + TesseractOpenCVAdapter  
│   ├── storage_filesystem.py    # Almacenamiento con integración de tablas
│   └── table_pdfplumber.py      # Extracción de tablas estructuradas
├── application/
│   ├── controllers.py           # Controladores de aplicación
│   ├── ports.py                 # Interfaces/contratos
│   └── use_cases.py             # ProcessDocument + EnhancedProcessDocument
├── config/
│   └── system_config.py         # SystemConfig + QUALITY_PROFILES
├── interfaces/cli/
│   ├── main.py                  # Punto de entrada único
│   └── menu.py                  # Menú principal unificado
├── utils/
│   ├── file_utils.py            # Utilidades de archivos
│   └── menu_logic.py            # Lógica de menús
└── domain/
    ├── models.py                # Modelos de dominio
    └── rules.py                 # Reglas de negocio
```

### Archivos Eliminados (Duplicación Removida)
- ~~`enhanced_simple_menu.py`~~ (duplicado con emoticones)
- ~~`enhanced_menu.py`~~ (dependencia questionary innecesaria)
- ~~`main_enhanced.py`~~ (punto de entrada duplicado)
- ~~`ocr_tesseract.py`~~ + ~~`ocr_tesseract_opencv.py`~~ + ~~`ocr_enhanced.py`~~ → **unificados**
- ~~`use_cases.py`~~ + ~~`enhanced_use_cases.py`~~ + ~~`document_use_cases.py`~~ → **unificados**
- ~~`image_processor.py`~~ + ~~`text_validator.py`~~ (no utilizados)
- ~~`enhanced_config.py`~~ → **renombrado y simplificado**

## Adaptadores OCR Unificados

### TesseractAdapter (Básico)
OCR básico y rápido para documentos de buena calidad:

```python
TesseractAdapter(
    lang="spa",          # Idioma para OCR
    dpi=300             # Resolución de conversión
)
```

Ideal para:
- PDFs nativos con texto claro
- Documentos generados digitalmente
- Procesamiento rápido
- Casos donde velocidad > precisión

### TesseractOpenCVAdapter (Avanzado)
OCR con preprocesamiento OpenCV para documentos complejos:

```python
TesseractOpenCVAdapter(
    lang="spa",                         # Idioma para OCR
    dpi=300,                           # Resolución
    enable_deskewing=True,             # Corrección de inclinación
    enable_denoising=True,             # Eliminación de ruido
    enable_contrast_enhancement=True   # Mejora de contraste
)
```

Ideal para:
- Documentos escaneados de baja calidad
- Imágenes con ruido o inclinación
- Formularios con líneas
- Documentos con poco contraste

### Pipeline de Procesamiento OpenCV
```
PDF → Imagen → OpenCV → Tesseract → Texto
           ↓
    1. Escala de grises
    2. Eliminación de ruido (Bilateral, Gaussian, Median)
```
PDF → Imagen → OpenCV → Tesseract → Texto
           ↓
    1. Escala de grises
    2. Eliminación de ruido (Bilateral, Gaussian, Median)
    3. Mejora de contraste (CLAHE)
    4. Binarización adaptativa
    5. Corrección de inclinación (Hough Lines)
    6. Operaciones morfológicas (Opening/Closing)
```

## Sistema de Configuración

### SystemConfig - Configuración Unificada
```python
@dataclass
class SystemConfig:
    # OCR Settings
    language: str = "spa"
    dpi: int = 300
    confidence_threshold: float = 60.0
    
    # OpenCV Preprocessing
    enable_deskewing: bool = True
    enable_denoising: bool = True
    enable_contrast_enhancement: bool = True
    
    # Processing Settings
    enable_auto_retry: bool = True
    max_processing_time_minutes: int = 30
    enable_table_extraction: bool = True
```

### Perfiles de Calidad Predefinidos
```python
# Máxima calidad - Para documentos críticos
config = SystemConfig.create_high_quality_config()

# Procesamiento rápido - Para documentos simples
config = SystemConfig.create_fast_config()

# Balanceado - Configuración por defecto
config = SystemConfig.create_balanced_config()
```

## Configuraciones de Bibliotecas

### Tesseract OCR
```python
# Idiomas principales
lang="spa"        # Español
lang="eng"        # Inglés
lang="spa+eng"    # Multiidioma

# Configuraciones de calidad
dpi=150          # Rápido, calidad básica
dpi=300          # Balance óptimo (recomendado)
dpi=600          # Alta calidad, lento

# Modos de segmentación (PSM)
--psm 3          # Página completa (por defecto)
--psm 6          # Bloque uniforme de texto
--psm 8          # Palabra simple
```

### OpenCV
```python
# Filtros de ruido
cv2.GaussianBlur(image, (5, 5), 0)              # Suaviza ruido
cv2.medianBlur(image, 3)                         # Elimina ruido sal/pimienta
cv2.bilateralFilter(image, 9, 75, 75)           # Preserva bordes

# Mejora de contraste
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# Binarización adaptativa
cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                     cv2.THRESH_BINARY, 11, 2)

# Operaciones morfológicas
cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)   # Elimina ruido
cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)  # Conecta fragmentos
```

### pdf2image
```python
convert_from_path(
    pdf_path,
    dpi=300,                    # Resolución óptima
    thread_count=4,             # Paralelización
    fmt='ppm'                   # Formato de salida
)
```


### pdfplumber
```python
# Extracción de tablas
page.extract_tables()

# Configuraciones básicas
table_settings={
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3
}
```

### pandas y tabulate
```python
# Exportación a diferentes formatos
df.to_csv('output.csv', index=False, encoding='utf-8')
tabulate(data, tablefmt="pipe")      # Markdown
tabulate(data, tablefmt="github")    # GitHub Markdown
```

## Uso Básico

### Ejecutar con Docker
```bash
# Construir imagen
docker-compose build

# Ejecutar aplicación
docker-compose up

# Usar volúmenes para archivos
./pdfs → /app/pdfs (entrada)
./resultado → /app/resultado (salida)
```

### Estructura de Archivos de Salida
```
resultado/
├── documento.txt          # Texto extraído
├── documento.md           # Formato Markdown con tablas
└── documento_original.pdf # Copia del original
```

### Configuraciones Rápidas
```python
# Para documentos de alta calidad (PDFs nativos)
config = SystemConfig.create_fast_config()

# Para documentos escaneados o de baja calidad
config = SystemConfig.create_high_quality_config()

# Configuración balanceada (por defecto)
config = SystemConfig.create_balanced_config()
```

## Desarrollo

### Agregar Nuevo Adaptador OCR
```python
class NuevoOCRAdapter(OCRPort):
    def extract_text(self, pdf_path: Path) -> str:
        # Implementación específica
        pass

# Uso en caso de uso
ProcessDocument(
    ocr=NuevoOCRAdapter(),
    table_extractor=PdfPlumberAdapter(),
    storage=FileStorage(out_dir)
)
```

### Testing
```bash
# Ejecutar tests
pytest tests/

# Verificar construcción Docker
docker-compose build
```

## Variables de Entorno

```bash
# Configuraciones básicas
export TESSERACT_CMD=/usr/bin/tesseract
export OCR_DEFAULT_LANG=spa
export OCR_DEFAULT_DPI=300
export OCR_ENABLE_PREPROCESSING=true
```
