# adapters/ocr_adapters.py
"""
Adaptadores de OCR unificados para el sistema OCR-CLI.

Este módulo contiene todos los adaptadores OCR disponibles:
- TesseractAdapter: OCR básico con Tesseract
- TesseractOpenCVAdapter: OCR con preprocesamiento OpenCV
"""
from pathlib import Path
from typing import List, Tuple
import logging

import pytesseract
from pdf2image import convert_from_path
import numpy as np
import cv2

from application.ports import OCRPort

logger = logging.getLogger(__name__)


class TesseractAdapter(OCRPort):
    """
    Adaptador básico de OCR usando Tesseract.
    
    Ideal para:
    - Documentos con buena calidad de imagen
    - Procesamiento rápido
    - PDFs nativos con texto claro
    """

    def __init__(self, lang: str = "spa", dpi: int = 300) -> None:
        """
        Inicializa el adaptador básico de Tesseract.
        
        Args:
            lang: Idioma para OCR (spa, eng, etc.)
            dpi: Resolución para conversión PDF->imagen
        """
        self.lang = lang
        self.dpi = dpi
        logger.info(f"TesseractAdapter inicializado: lang={lang}, dpi={dpi}")

    @classmethod
    def from_config(cls, config):
        """
        Crea un adaptador desde una configuración del sistema.
        
        Args:
            config: SystemConfig con los parámetros
            
        Returns:
            TesseractAdapter: Adaptador configurado
        """
        return cls(lang=config.language, dpi=config.dpi)

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extrae texto usando OCR básico de Tesseract.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            str: Texto extraído
        """
        logger.info(f"Iniciando extracción básica de: {pdf_path}")
        
        # Convertir PDF a imágenes
        images = convert_from_path(pdf_path, dpi=self.dpi)
        
        # Extraer texto de cada página
        extracted_text = []
        for page_num, image in enumerate(images, 1):
            logger.debug(f"Procesando página {page_num}/{len(images)}")
            
            # OCR directo
            text = pytesseract.image_to_string(image, lang=self.lang)
            extracted_text.append(text)
        
        final_text = "\n\n".join(extracted_text)
        logger.info(f"Extracción completada. Páginas procesadas: {len(images)}")
        
        return final_text


class TesseractOpenCVAdapter(OCRPort):
    """
    Adaptador avanzado de OCR con preprocesamiento OpenCV.
    
    Ideal para:
    - Documentos escaneados de baja calidad
    - Imágenes con ruido o inclinación
    - Procesamiento de alta precisión
    """

    def __init__(
        self, 
        lang: str = "spa", 
        dpi: int = 300,
        enable_deskewing: bool = True,
        enable_denoising: bool = True,
        enable_contrast_enhancement: bool = True
    ) -> None:
        """
        Inicializa el adaptador con preprocesamiento OpenCV.
        
        Args:
            lang: Idioma para OCR
            dpi: Resolución para conversión
            enable_deskewing: Activar corrección de inclinación
            enable_denoising: Activar eliminación de ruido
            enable_contrast_enhancement: Activar mejora de contraste
        """
        self.lang = lang
        self.dpi = dpi
        self.enable_deskewing = enable_deskewing
        self.enable_denoising = enable_denoising
        self.enable_contrast_enhancement = enable_contrast_enhancement
        
        logger.info(f"TesseractOpenCVAdapter inicializado: lang={lang}, dpi={dpi}")
        logger.info(f"Preprocesamiento: deskew={enable_deskewing}, denoise={enable_denoising}, contrast={enable_contrast_enhancement}")

    @classmethod
    def from_config(cls, config):
        """
        Crea un adaptador desde una configuración del sistema.
        
        Args:
            config: SystemConfig con los parámetros
            
        Returns:
            TesseractOpenCVAdapter: Adaptador configurado
        """
        return cls(
            lang=config.language,
            dpi=config.dpi,
            enable_deskewing=config.enable_deskewing,
            enable_denoising=config.enable_denoising,
            enable_contrast_enhancement=config.enable_contrast_enhancement
        )

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extrae texto con preprocesamiento OpenCV.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            str: Texto extraído optimizado
        """
        logger.info(f"Iniciando extracción con OpenCV de: {pdf_path}")
        
        # Convertir PDF a imágenes
        images = convert_from_path(pdf_path, dpi=self.dpi)
        
        # Procesar cada página con OpenCV
        extracted_text = []
        for page_num, image in enumerate(images, 1):
            logger.debug(f"Procesando página {page_num}/{len(images)} con OpenCV")
            
            # Convertir PIL a numpy array
            image_array = np.array(image)
            
            # Aplicar preprocesamiento
            processed_image = self._preprocess_image(image_array)
            
            # Convertir de vuelta a PIL para Tesseract
            from PIL import Image
            processed_pil = Image.fromarray(processed_image)
            
            # OCR en imagen procesada
            text = pytesseract.image_to_string(processed_pil, lang=self.lang)
            extracted_text.append(text)
        
        final_text = "\n\n".join(extracted_text)
        logger.info(f"Extracción con OpenCV completada. Páginas procesadas: {len(images)}")
        
        return final_text

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica preprocesamiento OpenCV a una imagen.
        
        Args:
            image: Imagen como array numpy
            
        Returns:
            np.ndarray: Imagen procesada
        """
        # Convertir a escala de grises
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # 1. Eliminación de ruido
        if self.enable_denoising:
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 2. Mejora de contraste
        if self.enable_contrast_enhancement:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
        
        # 3. Corrección de inclinación
        if self.enable_deskewing:
            gray = self._correct_skew(gray)
        
        # 4. Binarización adaptativa
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # 5. Operaciones morfológicas para limpiar
        kernel = np.ones((1,1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return binary

    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige la inclinación de la imagen.
        
        Args:
            image: Imagen en escala de grises
            
        Returns:
            np.ndarray: Imagen corregida
        """
        try:
            # Detectar bordes
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detectar líneas con transformada de Hough
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Calcular ángulo promedio
                angles = []
                for rho, theta in lines[:min(10, len(lines))]:
                    angle = theta * 180 / np.pi - 90
                    if abs(angle) < 45:  # Solo ángulos razonables
                        angles.append(angle)
                
                if angles:
                    # Usar mediana para robustez
                    rotation_angle = np.median(angles)
                    
                    # Rotar imagen si el ángulo es significativo
                    if abs(rotation_angle) > 0.5:
                        h, w = image.shape
                        center = (w // 2, h // 2)
                        matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
                        image = cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                        logger.debug(f"Corregida inclinación: {rotation_angle:.2f} grados")
                        
        except Exception as e:
            logger.warning(f"Error en corrección de inclinación: {e}")
        
        return image
