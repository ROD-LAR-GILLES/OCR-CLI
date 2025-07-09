# adapters/ocr_tesseract.py
"""
Adaptador de OCR basado en Tesseract.

Este módulo implementa el puerto OCRPort utilizando Tesseract OCR de Google,
una de las librerías de reconocimiento óptico de caracteres más robustas
y ampliamente utilizadas en el ecosistema open source.
"""
from pathlib import Path
from typing import List

import pytesseract
from pdf2image import convert_from_path

from application.ports import OCRPort


class TesseractAdapter(OCRPort):
    """
    Adaptador de OCR que utiliza Tesseract para extraer texto de documentos PDF.
    
    Tesseract es un motor de OCR desarrollado por Google que soporta más de 100 idiomas
    y proporciona alta precisión en documentos con texto claro y bien estructurado.
    
    Proceso de extracción:
    1. Convierte cada página del PDF a imagen usando pdf2image
    2. Aplica OCR a cada imagen usando pytesseract
    3. Concatena el texto de todas las páginas
    
    Configuraciones disponibles:
    - lang: Idioma para el reconocimiento (spa, eng, fra, etc.)
    - dpi: Resolución de las imágenes generadas (mayor DPI = mejor calidad pero más lento)
    
    Limitaciones:
    - Requiere texto impreso legible
    - Sensible a la calidad de imagen
    - Lento en documentos grandes
    - Problemas con texto manuscrito o en ángulos
    """

    def __init__(self, lang: str = "spa", dpi: int = 300) -> None:
        """
        Inicializa el adaptador de Tesseract con configuraciones específicas.
        
        Args:
            lang (str): Código de idioma para Tesseract. Opciones comunes:
                - 'spa': Español (Spanish)
                - 'eng': Inglés (English) 
                - 'fra': Francés (French)
                - 'deu': Alemán (German)
                - 'ita': Italiano (Italian)
                - Se pueden combinar: 'spa+eng' para documentos multiidioma
                
            dpi (int): Resolución en puntos por pulgada para la conversión PDF->imagen.
                - 150: Rápido, calidad básica (documentos muy claros)
                - 300: Balance óptimo calidad/velocidad (recomendado)
                - 600: Alta calidad (documentos con texto pequeño o borroso)
                - 1200: Máxima calidad (muy lento, solo para casos especiales)
        
        Note:
            El idioma debe estar instalado en el sistema. En Docker se instala
            tesseract-ocr-spa para español. Para otros idiomas, modificar Dockerfile.
        """
        self.lang = lang
        self.dpi = dpi

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extrae todo el texto de un documento PDF usando OCR.
        
        Proceso detallado:
        1. pdf2image convierte cada página PDF a imagen PIL usando Poppler
        2. pytesseract procesa cada imagen aplicando algoritmos de OCR
        3. Los resultados se concatenan con separadores de página
        
        Args:
            pdf_path (Path): Ruta al archivo PDF a procesar
            
        Returns:
            str: Texto completo extraído, con páginas separadas por doble salto de línea
            
        Raises:
            FileNotFoundError: Si el archivo PDF no existe
            pytesseract.TesseractError: Si Tesseract falla en el procesamiento
            pdf2image.exceptions.PDFInfoNotInstalledError: Si poppler no está instalado
            
        Note:
            - pdf2image requiere poppler-utils instalado en el sistema
            - El tiempo de procesamiento aumenta linealmente con el número de páginas
            - Páginas con imágenes complejas pueden ralentizar significativamente el proceso
        """
        # Convierte cada página del PDF a imagen PIL usando poppler-utils
        # dpi controla la resolución: mayor DPI = mejor calidad pero archivos más grandes
        images: List = convert_from_path(pdf_path, dpi=self.dpi)
        
        # Aplica OCR a cada imagen individualmente
        # pytesseract.image_to_string() es la función principal de reconocimiento
        # lang= especifica el modelo de idioma entrenado a usar
        chunks = [
            pytesseract.image_to_string(img, lang=self.lang)
            for img in images
        ]
        
        # Concatena el texto de todas las páginas
        # Usa "\n\n" como separador para distinguir visualmente las páginas
        return "\n\n".join(chunks)