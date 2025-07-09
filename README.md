# Documentación del Proyecto OCR-CLI

## 📋 Descripción General

OCR-CLI es una aplicación de línea de comandos diseñada con **arquitectura hexagonal** (puertos y adaptadores) para procesar documentos PDF mediante OCR (Reconocimiento Óptico de Caracteres) y extracción de tablas. El proyecto está preparado para escalar hacia un producto completo con API REST, RAG (Retrieval-Augmented Generation) y múltiples motores de OCR.

## 🏗️ Arquitectura del Proyecto

La aplicación sigue el patrón de **Arquitectura Hexagonal** que separa:
- **Dominio**: Lógica de negocio pura (sin dependencias externas)
- **Aplicación**: Casos de uso y puertos (interfaces)
- **Adaptadores**: Implementaciones concretas de tecnologías específicas
- **Interfaces**: Puntos de entrada (CLI, futuras APIs)

```
OCR-CLI/
├── domain/              # Entidades y reglas de negocio puras
├── application/         # Casos de uso y puertos (interfaces)
├── adapters/           # Implementaciones de tecnologías específicas
├── interfaces/         # Puntos de entrada (CLI)
├── pdfs/              # Archivos PDF de entrada
├── resultado/         # Archivos procesados de salida
└── tests/             # Pruebas unitarias
```

## 📁 Documentación por Archivos

### 🔧 Archivos de Configuración

#### `docker-compose.yml`
**Propósito**: Orquesta la ejecución del contenedor Docker de la aplicación.

**Funcionalidades**:
- **Servicio `ocr-backend`**: Construye y ejecuta la aplicación OCR
- **Volúmenes montados**:
  - `./pdfs:/pdfs`: Mapea la carpeta local de PDFs al contenedor
  - `./resultado:/app/resultado`: Mapea la salida del contenedor al sistema local
- **`tty: true`**: Permite interacción con el menú CLI desde el contenedor

**Tecnologías utilizadas**: Docker Compose v3+

#### `Dockerfile`
**Propósito**: Define el entorno de ejecución containerizado de la aplicación.

**Pasos del build**:
1. **Base**: Python 3.11 slim (imagen ligera)
2. **Dependencias del sistema**:
   - `tesseract-ocr tesseract-ocr-spa`: Motor OCR principal con soporte para español
   - `poppler-utils`: Conversión de PDF a imágenes
   - `ghostscript`: Procesamiento avanzado de PDF
   - `gcc`: Compilador para dependencias de Python
   - Librerías gráficas: `libgl1-mesa-glx`, `libsm6`, etc.
3. **Dependencias Python**: Instala desde `requirements.txt`
4. **Comando por defecto**: Ejecuta el CLI principal

**Tecnologías utilizadas**: Docker, Python 3.11, Tesseract OCR

#### `requirements.txt`
**Propósito**: Define todas las dependencias Python del proyecto.

**Categorías de dependencias**:

**OCR y Procesamiento PDF**:
- `pytesseract==0.3.10`: Wrapper Python para Tesseract OCR
- `pdf2image==1.17.0`: Convierte páginas PDF a imágenes PIL
- `PyMuPDF==1.23.24`: Librería rápida para manipulación de PDF
- `pdfplumber==0.10.3`: Extracción precisa de texto y tablas de PDF
- `Pillow==10.3.0`: Procesamiento de imágenes

**Procesamiento de Datos**:
- `tabulate==0.9.0`: Formato de tablas en texto ASCII
- `pandas==2.2.2`: Análisis y manipulación de datos estructurados

**Interfaz de Usuario**:
- `questionary==2.0.1`: Menús interactivos elegantes para CLI

### 🏛️ Capa de Dominio

#### `domain/models.py`
**Propósito**: Define las entidades principales del dominio sin dependencias externas.

**Entidades**:
```python
@dataclass
class Document:
    name: str          # Nombre del documento
    text: str          # Texto extraído por OCR
    tables: List[Any]  # Tablas extraídas como DataFrames
    source: Path       # Ruta del archivo original
```

**Características**:
- **Inmutable**: Usa `@dataclass` para crear objetos de datos
- **Independiente**: No importa librerías externas
- **Tipado**: Usa type hints para claridad

**Principios aplicados**: Single Responsibility, Domain-Driven Design

#### `domain/rules.py`
**Propósito**: Archivo preparado para reglas de negocio específicas del dominio.

**Estado actual**: Vacío (preparado para futuras reglas como validaciones, transformaciones, etc.)

### 🎯 Capa de Aplicación

#### `application/ports.py`
**Propósito**: Define los contratos (interfaces) que deben implementar los adaptadores externos.

**Puertos definidos**:

**OCRPort**:
```python
class OCRPort(ABC):
    @abstractmethod
    def extract_text(self, pdf_path: Path) -> str: ...
```
- **Responsabilidad**: Extraer texto de PDFs mediante OCR
- **Implementaciones actuales**: TesseractAdapter
- **Futuras implementaciones**: EasyOCR, Google Vision API, Amazon Textract

**TableExtractorPort**:
```python
class TableExtractorPort(ABC):
    @abstractmethod
    def extract_tables(self, pdf_path: Path) -> List[Any]: ...
```
- **Responsabilidad**: Extraer tablas estructuradas de PDFs
- **Implementaciones actuales**: PdfPlumberAdapter
- **Futuras implementaciones**: Camelot, Tabula

**StoragePort**:
```python
class StoragePort(ABC):
    @abstractmethod
    def save(self, name: str, text: str, tables: List[Any], original: Path) -> None: ...
```
- **Responsabilidad**: Persistir resultados procesados
- **Implementaciones actuales**: FileStorage (filesystem)
- **Futuras implementaciones**: DatabaseStorage, CloudStorage

**Principios aplicados**: Dependency Inversion, Interface Segregation

#### `application/use_cases.py`
**Propósito**: Orquesta la lógica de negocio utilizando inyección de dependencias.

**Caso de Uso Principal**: `ProcessDocument`

**Flujo de ejecución**:
1. **Inicialización**: Recibe implementaciones de los puertos via constructor
2. **Extracción OCR**: Utiliza `OCRPort` para extraer texto
3. **Extracción de tablas**: Utiliza `TableExtractorPort` para obtener datos estructurados
4. **Persistencia**: Utiliza `StoragePort` para guardar resultados
5. **Retorno**: Devuelve rutas de archivos generados

**Ventajas**:
- **Testeable**: Fácil mockear dependencias en tests
- **Flexible**: Cambiar implementaciones sin modificar lógica
- **Escalable**: Agregar nuevos pasos sin romper código existente

**Principios aplicados**: Single Responsibility, Dependency Injection, Open/Closed

### ⚙️ Capa de Adaptadores

#### `adapters/ocr_tesseract.py`
**Propósito**: Implementación concreta del puerto OCR usando Tesseract.

**Funcionalidad**:
- **Motor**: Tesseract OCR (Google)
- **Proceso**:
  1. Convierte PDF a imágenes con `pdf2image`
  2. Aplica OCR a cada imagen con `pytesseract`
  3. Concatena resultados de todas las páginas
- **Configuración**:
  - `lang="spa"`: Idioma español por defecto
  - `dpi=300`: Resolución alta para mejor precisión

**Ventajas de Tesseract**:
- ✅ Gratuito y open source
- ✅ Soporte para 100+ idiomas
- ✅ Alta precisión en textos claros
- ✅ Configurable (whitelist, blacklist caracteres)

**Limitaciones**:
- ❌ Lento en documentos grandes
- ❌ Menor precisión en texto manuscrito
- ❌ No maneja texto en ángulos complejos

#### `adapters/table_pdfplumber.py`
**Propósito**: Implementación del puerto de extracción de tablas usando pdfplumber.

**Funcionalidad**:
- **Motor**: pdfplumber (análisis de estructura PDF)
- **Proceso**:
  1. Abre PDF y recorre cada página
  2. Detecta tablas mediante análisis de líneas y espacios
  3. Convierte tablas a pandas DataFrames
- **Formato de salida**: Lista de DataFrames de pandas

**Ventajas de pdfplumber**:
- ✅ Muy preciso en PDFs con estructura clara
- ✅ Mantiene formato original de celdas
- ✅ Rápido (no requiere OCR para tablas)
- ✅ Detecta automáticamente bordes de tabla

**Limitaciones**:
- ❌ Solo funciona con PDFs nativos (no escaneados)
- ❌ Problemas con tablas sin bordes claros
- ❌ No funciona con texto en imágenes

#### `adapters/storage_filesystem.py`
**Propósito**: Implementación del puerto de almacenamiento en sistema de archivos local.

**Funcionalidad**:
- **Crea estructura** de directorio de salida
- **Formatos de salida múltiples**:
  1. **`.txt`**: Texto plano extraído por OCR
  2. **`_table_N.json`**: Cada tabla como JSON estructurado
  3. **`_tables.txt`**: Todas las tablas en formato ASCII legible
  4. **`.pdf`**: Copia del archivo original

**Ventajas**:
- ✅ Simple y rápido
- ✅ Múltiples formatos para diferentes usos
- ✅ Preserva archivo original
- ✅ Estructura organizada

**Casos de uso**:
- **JSON**: Integración con otras aplicaciones
- **TXT**: Lectura humana y análisis
- **ASCII**: Visualización rápida de tablas

### 🖥️ Capa de Interfaces

#### `interfaces/cli/main.py`
**Propósito**: Punto de entrada principal de la aplicación CLI.

**Funcionalidad**:
- **Entry point**: Importa y ejecuta el menú principal
- **Patrón**: Separación entre bootstrap y lógica de interfaz

#### `interfaces/cli/menu.py`
**Propósito**: Interfaz de usuario interactiva para la aplicación CLI.

**Funcionalidades**:

**1. Descubrimiento de archivos**:
```python
def listar_pdfs() -> list[str]:
```
- Escanea directorio `/pdfs` en busca de archivos PDF
- Ordena alfabéticamente para presentación consistente

**2. Procesamiento interactivo**:
```python
def procesar_archivo(nombre: str):
```
- **Inyección de dependencias**: Configura adaptadores concretos
- **Orquestación**: Ejecuta el caso de uso `ProcessDocument`
- **Feedback**: Muestra rutas de archivos generados

**3. Menú principal**:
```python
def main():
```
- **Interfaz elegante**: Usa `questionary` para menú seleccionable
- **Manejo de errores**: Valida existencia de archivos
- **Loop continuo**: Permite procesar múltiples archivos
- **Salida graceful**: Opción de salir del programa

**Tecnología utilizada**:
- **questionary**: Menús interactivos con navegación por teclado
- **Pathlib**: Manipulación moderna de rutas de archivos

**Características UX**:
- ✅ Navegación intuitiva con flechas
- ✅ Escape para salir
- ✅ Feedback inmediato de progreso
- ✅ Manejo de casos de error

### 🧪 Capa de Testing

#### `tests/test_dummy.py`
**Propósito**: Archivo de prueba básico (placeholder para futuras pruebas).

**Estado actual**: Contiene solo un test dummy para verificar la configuración de testing.

**Futuras pruebas sugeridas**:
- **Tests unitarios** para cada adaptador con mocks
- **Tests de integración** para casos de uso completos
- **Tests de comportamiento** para validar flujos CLI

## 🚀 Roadmap y Extensibilidad

### Próximas Funcionalidades Planificadas:

#### 1. **Multi-OCR Support**
- EasyOCR adapter para mejor precisión
- Google Vision API para documentos complejos
- Amazon Textract para formularios

#### 2. **RAG (Retrieval-Augmented Generation)**
- Embeddings con OpenAI/Sentence Transformers
- Vector database (Chroma/FAISS)
- Consultas semánticas sobre documentos

#### 3. **API REST**
- FastAPI para endpoints HTTP
- Upload asíncrono de documentos
- Cola de tareas con Celery/RQ

#### 4. **Observabilidad**
- Logging estructurado
- Métricas de performance
- Tracing distribuido

## 🛡️ Principios de Diseño Aplicados

### **SOLID Principles**:
- **S**: Cada clase tiene una responsabilidad específica
- **O**: Extensible sin modificar código existente (nuevos adaptadores)
- **L**: Los adaptadores son intercambiables
- **I**: Interfaces pequeñas y específicas (puertos)
- **D**: Dependencias invertidas (aplicación depende de abstracciones)

### **Clean Architecture**:
- **Independencia de frameworks**: Dominio no conoce Tesseract/pdfplumber
- **Testabilidad**: Fácil mockear dependencias externas
- **Flexibilidad**: Cambiar tecnologías sin afectar lógica de negocio

### **Domain-Driven Design**:
- **Ubiquitous Language**: Terminología consistente (Document, OCR, Table)
- **Bounded Context**: Separación clara de responsabilidades
- **Entities**: Modelos de dominio bien definidos

## 🔧 Guía de Desarrollo

### **Agregar nuevo adaptador OCR**:
1. Implementar `OCRPort` en `adapters/ocr_nuevo.py`
2. Inyectar en `ProcessDocument`
3. ¡Sin cambios en dominio/aplicación!

### **Agregar nueva interfaz**:
1. Crear módulo en `interfaces/api/`
2. Importar casos de uso de `application/`
3. Mantener separación de capas

### **Ejecutar aplicación**:
```bash
# Desarrollo local
python interfaces/cli/main.py

# Con Docker
docker-compose up --build
```

Esta arquitectura garantiza que el proyecto pueda evolucionar desde un CLI simple hasta un SaaS completo manteniendo la calidad del código y la facilidad de mantenimiento.
