# adapters/ocr_tesseract_opencv.py
"""
Adaptador de OCR mejorado con OpenCV para preprocesamiento de imágenes.

Este módulo implementa una versión avanzada del adaptador de Tesseract que utiliza
OpenCV para aplicar técnicas de preprocesamiento de imágenes que mejoran
significativamente la precisión del OCR.

OpenCV (Computer Vision Library) proporciona:
- Filtros de ruido y mejora de contraste
- Binarización adaptativa para diferentes condiciones de iluminación
- Detección y corrección de inclinación (deskewing)
- Eliminación de artefactos y mejora de bordes
- Redimensionamiento inteligente para optimizar OCR
"""
from pathlib import Path
from typing import List, Tuple
import numpy as np
import cv2

import pytesseract
from pdf2image import convert_from_path

from application.ports import OCRPort


class TesseractOpenCVAdapter(OCRPort):
    """
    Adaptador de OCR que combina Tesseract con preprocesamiento OpenCV.
    
    Esta implementación aplica una serie de técnicas de Computer Vision
    para mejorar la calidad de las imágenes antes del reconocimiento OCR:
    
    Pipeline de procesamiento:
    1. Conversión PDF a imágenes (pdf2image)
    2. Preprocesamiento con OpenCV:
       - Conversión a escala de grises
       - Reducción de ruido (Gaussian blur, morphological operations)
       - Mejora de contraste (CLAHE - Contrast Limited Adaptive Histogram Equalization)
       - Binarización adaptativa
       - Detección y corrección de inclinación
       - Eliminación de líneas y artefactos
    3. OCR con Tesseract en imagen optimizada
    
    Ventajas sobre TesseractAdapter básico:
    - Mejora significativa en documentos de baja calidad
    - Manejo automático de diferentes condiciones de iluminación
    - Corrección de inclinación para documentos escaneados mal alineados
    - Eliminación de ruido y artefactos que confunden al OCR
    - Optimización automática de contraste y nitidez
    
    Casos de uso ideales:
    - Documentos escaneados de baja calidad
    - PDFs con texto borroso o con ruido
    - Documentos con iluminación desigual
    - Texto en ángulo o ligeramente inclinado
    - Formularios con líneas que interfieren con el texto
    
    Limitaciones:
    - Procesamiento más lento debido al preprocesamiento
    - Consumo adicional de memoria para operaciones de imagen
    - Puede sobre-procesar documentos ya de alta calidad
    """

    def __init__(self, 
                 lang: str = "spa", 
                 dpi: int = 300,
                 enable_preprocessing: bool = True,
                 enable_deskewing: bool = True,
                 enable_denoising: bool = True,
                 enable_contrast_enhancement: bool = True) -> None:
        """
        Inicializa el adaptador con configuraciones de OCR y preprocesamiento.
        
        Args:
            lang (str): Código de idioma para Tesseract (spa, eng, fra, etc.)
            dpi (int): Resolución para conversión PDF a imagen
            enable_preprocessing (bool): Activa/desactiva todo el preprocesamiento OpenCV
            enable_deskewing (bool): Activa corrección de inclinación
            enable_denoising (bool): Activa eliminación de ruido
            enable_contrast_enhancement (bool): Activa mejora de contraste
            
        Note:
            - Todas las opciones de preprocesamiento pueden desactivarse individualmente
            - Para documentos de alta calidad, considerar desactivar preprocesamiento
            - enable_preprocessing=False hace que funcione como TesseractAdapter básico
        """
        self.lang = lang
        self.dpi = dpi
        self.enable_preprocessing = enable_preprocessing
        self.enable_deskewing = enable_deskewing
        self.enable_denoising = enable_denoising
        self.enable_contrast_enhancement = enable_contrast_enhancement

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extrae texto aplicando preprocesamiento OpenCV antes del OCR.
        
        Args:
            pdf_path (Path): Ruta al archivo PDF a procesar
            
        Returns:
            str: Texto extraído con técnicas avanzadas de Computer Vision
            
        Raises:
            FileNotFoundError: Si el archivo PDF no existe
            cv2.error: Si hay errores en el procesamiento OpenCV
            pytesseract.TesseractError: Si Tesseract falla
        """
        # Conversión PDF a imágenes usando pdf2image
        images: List = convert_from_path(pdf_path, dpi=self.dpi)
        
        chunks = []
        for img in images:
            # Conversión de PIL Image a formato OpenCV (numpy array)
            opencv_image = self._pil_to_opencv(img)
            
            # Aplicar preprocesamiento si está habilitado
            if self.enable_preprocessing:
                processed_image = self._preprocess_image(opencv_image)
            else:
                processed_image = opencv_image
            
            # Conversión de vuelta a PIL para Tesseract
            pil_image = self._opencv_to_pil(processed_image)
            
            # OCR con Tesseract en imagen procesada
            text = pytesseract.image_to_string(pil_image, lang=self.lang)
            chunks.append(text)
        
        return "\n\n".join(chunks)

    def _pil_to_opencv(self, pil_image) -> np.ndarray:
        """
        Convierte imagen PIL a formato OpenCV (numpy array).
        
        Args:
            pil_image: Imagen en formato PIL
            
        Returns:
            np.ndarray: Imagen en formato OpenCV (BGR)
        """
        # Convierte PIL a numpy array
        numpy_image = np.array(pil_image)
        
        # PIL usa RGB, OpenCV usa BGR - convertir si es necesario
        if len(numpy_image.shape) == 3:
            opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        else:
            opencv_image = numpy_image
            
        return opencv_image

    def _opencv_to_pil(self, opencv_image: np.ndarray):
        """
        Convierte imagen OpenCV de vuelta a formato PIL.
        
        Args:
            opencv_image (np.ndarray): Imagen en formato OpenCV
            
        Returns:
            PIL.Image: Imagen convertida a PIL
        """
        from PIL import Image
        
        # Si es escala de grises, convertir a RGB para PIL
        if len(opencv_image.shape) == 2:
            pil_image = Image.fromarray(opencv_image, mode='L')
        else:
            # Convertir de BGR (OpenCV) a RGB (PIL)
            rgb_image = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
        return pil_image

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica pipeline completo de preprocesamiento OpenCV.
        
        Pipeline de optimización:
        1. Conversión a escala de grises
        2. Eliminación de ruido (si está habilitada)
        3. Mejora de contraste (si está habilitada)
        4. Binarización adaptativa
        5. Corrección de inclinación (si está habilitada)
        6. Operaciones morfológicas finales
        
        Args:
            image (np.ndarray): Imagen original en formato OpenCV
            
        Returns:
            np.ndarray: Imagen optimizada para OCR
        """
        # PASO 1: Conversión a escala de grises
        # Reduce dimensionalidad y enfoca en estructura de texto
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # PASO 2: Eliminación de ruido (opcional)
        if self.enable_denoising:
            gray = self._remove_noise(gray)

        # PASO 3: Mejora de contraste (opcional)
        if self.enable_contrast_enhancement:
            gray = self._enhance_contrast(gray)

        # PASO 4: Binarización adaptativa
        # Convierte a imagen binaria (blanco/negro) de forma inteligente
        binary = self._adaptive_binarization(gray)

        # PASO 5: Corrección de inclinación (opcional)
        if self.enable_deskewing:
            binary = self._correct_skew(binary)

        # PASO 6: Operaciones morfológicas finales
        # Limpia caracteres fragmentados y conecta letras rotas
        final_image = self._morphological_operations(binary)

        return final_image

    def _remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Elimina ruido de la imagen usando filtros OpenCV.
        
        Técnicas aplicadas:
        - Gaussian Blur: Suaviza ruido de alta frecuencia
        - Median Blur: Elimina ruido sal y pimienta
        - Bilateral Filter: Preserva bordes mientras elimina ruido
        
        Args:
            image (np.ndarray): Imagen en escala de grises
            
        Returns:
            np.ndarray: Imagen con ruido reducido
        """
        # Gaussian Blur para suavizar ruido general
        # kernel_size=(5,5) es un balance entre suavizado y preservación de detalles
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        
        # Median Blur para eliminar ruido sal y pimienta
        # kernel_size=3 es conservador para no eliminar detalles de texto
        median_filtered = cv2.medianBlur(blurred, 3)
        
        # Bilateral Filter: preserva bordes mientras suaviza áreas uniformes
        # d=9: tamaño del vecindario
        # sigmaColor=75: mayor valor = colores más lejanos se mezclan
        # sigmaSpace=75: mayor valor = píxeles más lejanos se influyen mutuamente
        bilateral = cv2.bilateralFilter(median_filtered, 9, 75, 75)
        
        return bilateral

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste usando CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        CLAHE es superior a ecualización de histograma simple porque:
        - Aplica ecualización localmente (adaptativo)
        - Limita amplificación para evitar sobre-realce
        - Preserva detalles en diferentes regiones de iluminación
        
        Args:
            image (np.ndarray): Imagen en escala de grises
            
        Returns:
            np.ndarray: Imagen con contraste mejorado
        """
        # Crear objeto CLAHE con configuración optimizada para texto
        # clipLimit=2.0: limita amplificación para evitar artefactos
        # tileGridSize=(8,8): tamaño de regiones para análisis local
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Aplicar CLAHE a la imagen
        enhanced = clahe.apply(image)
        
        return enhanced

    def _adaptive_binarization(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica binarización adaptativa para convertir a imagen binaria.
        
        La binarización adaptativa es superior a umbralización fija porque:
        - Se adapta a condiciones locales de iluminación
        - Maneja sombras y variaciones de brillo
        - Preserva texto en diferentes regiones de la imagen
        
        Args:
            image (np.ndarray): Imagen en escala de grises
            
        Returns:
            np.ndarray: Imagen binaria (blanco y negro)
        """
        # Método Gaussiano: calcula umbral usando promedio ponderado Gaussiano
        # ADAPTIVE_THRESH_GAUSSIAN_C: usa promedio ponderado de vecindario
        # THRESH_BINARY: píxeles por encima del umbral = 255 (blanco)
        # blockSize=11: tamaño del área para calcular umbral (debe ser impar)
        # C=2: constante sustraída del promedio (ajuste fino)
        binary = cv2.adaptiveThreshold(
            image, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 
            2
        )
        
        return binary

    def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """
        Detecta y corrige la inclinación del texto usando análisis de líneas.
        
        Algoritmo de corrección:
        1. Detecta líneas usando Transformada de Hough
        2. Calcula ángulo predominante de las líneas de texto
        3. Rota la imagen para corregir inclinación
        
        Args:
            image (np.ndarray): Imagen binaria
            
        Returns:
            np.ndarray: Imagen con inclinación corregida
        """
        # Detección de bordes para encontrar líneas de texto
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Transformada de Hough para detectar líneas
        # rho=1: resolución en píxeles
        # theta=np.pi/180: resolución en radianes (1 grado)
        # threshold=100: mínimo número de intersecciones para detectar línea
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        if lines is not None:
            # Calcular ángulo promedio de las líneas detectadas
            angles = []
            for rho, theta in lines[:10]:  # Usar solo las 10 líneas más fuertes
                angle = theta - np.pi / 2  # Convertir a ángulo de rotación
                angles.append(angle)
            
            if angles:
                # Usar mediana para ser robusto a outliers
                skew_angle = np.median(angles) * 180 / np.pi
                
                # Solo corregir si la inclinación es significativa (> 0.5 grados)
                if abs(skew_angle) > 0.5:
                    corrected = self._rotate_image(image, skew_angle)
                    return corrected
        
        return image

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rota imagen por el ángulo especificado.
        
        Args:
            image (np.ndarray): Imagen a rotar
            angle (float): Ángulo en grados (positivo = antihorario)
            
        Returns:
            np.ndarray: Imagen rotada
        """
        # Obtener dimensiones de la imagen
        height, width = image.shape[:2]
        
        # Calcular centro de rotación
        center = (width // 2, height // 2)
        
        # Crear matriz de rotación
        # angle: ángulo de rotación
        # scale=1.0: no cambiar tamaño
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Aplicar rotación
        # borderMode=cv2.BORDER_REPLICATE: rellena bordes replicando píxeles
        # borderValue=255: usar blanco para relleno (mejor para texto)
        rotated = cv2.warpAffine(
            image, 
            rotation_matrix, 
            (width, height),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255
        )
        
        return rotated

    def _morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica operaciones morfológicas para limpiar y mejorar texto.
        
        Operaciones aplicadas:
        1. Opening: elimina ruido pequeño y conecta fragmentos
        2. Closing: cierra huecos en caracteres
        3. Erosion/Dilation: ajusta grosor de líneas
        
        Args:
            image (np.ndarray): Imagen binaria
            
        Returns:
            np.ndarray: Imagen con texto limpio y mejorado
        """
        # Crear kernels morfológicos
        # MORPH_RECT: kernel rectangular para operaciones horizontales/verticales
        # (3,3): tamaño pequeño para preservar detalles de texto
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        # Opening: erosión seguida de dilatación
        # Elimina ruido pequeño y separa objetos conectados incorrectamente
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        
        # Closing: dilatación seguida de erosión
        # Cierra huecos pequeños en caracteres y conecta fragmentos
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        
        return closed

    def get_preprocessing_info(self) -> dict:
        """
        Retorna información sobre las configuraciones de preprocesamiento activas.
        
        Returns:
            dict: Configuraciones actuales del adaptador
        """
        return {
            "language": self.lang,
            "dpi": self.dpi,
            "preprocessing_enabled": self.enable_preprocessing,
            "deskewing_enabled": self.enable_deskewing,
            "denoising_enabled": self.enable_denoising,
            "contrast_enhancement_enabled": self.enable_contrast_enhancement,
            "opencv_version": cv2.__version__
        }
