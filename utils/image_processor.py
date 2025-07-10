# utils/image_processor.py
"""
Módulo para procesamiento avanzado de imágenes con OpenCV.

Este módulo implementa técnicas avanzadas de procesamiento de imagen
para mejorar la calidad del OCR y la extracción de texto.
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Any
import pytesseract
from PIL import Image


class AdvancedImageProcessor:
    """
    Procesador avanzado de imágenes para OCR optimizado.
    
    Implementa técnicas de preprocesamiento adaptativo para mejorar
    significativamente la precisión del reconocimiento óptico de caracteres.
    """
    
    def __init__(self):
        """Inicializa el procesador con configuraciones optimizadas."""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Mejora el contraste local sin amplificar el ruido
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Kernels para operaciones morfológicas
        self.kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        self.kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    
    def advanced_preprocessing(self, image: np.ndarray) -> np.ndarray:
        """
        Pipeline completo de preprocesamiento avanzado.
        
        Args:
            image: Imagen de entrada en formato numpy array
            
        Returns:
            Imagen procesada optimizada para OCR
        """
        # 1. Conversión a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 2. Reducción de ruido adaptativa
        # fastNlMeansDenoising es más efectivo que filtros gaussianos
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # 3. Corrección de perspectiva si es necesario
        corrected = self.auto_perspective_correction(denoised)
        
        # 4. Ecualización adaptativa del histograma
        enhanced = self.clahe.apply(corrected)
        
        # 5. Detección y corrección de inclinación de texto
        deskewed = self.auto_deskew(enhanced)
        
        # 6. Binarización adaptativa mejorada
        binary = cv2.adaptiveThreshold(
            deskewed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 7. Limpieza morfológica final
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, self.kernel_rect)
        
        return cleaned
    
    def auto_perspective_correction(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige automáticamente la perspectiva del documento.
        
        Detecta los bordes del documento y aplica transformación de perspectiva
        para enderezar la imagen.
        """
        # Detección de bordes
        edges = cv2.Canny(image, 50, 150)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return image
        
        # Encontrar el contorno más grande (probablemente el documento)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Aproximar el contorno a un rectángulo
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # Si tenemos 4 puntos, aplicar corrección de perspectiva
        if len(approx) == 4:
            return self.four_point_transform(image, approx.reshape(4, 2))
        
        return image
    
    def four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Aplica transformación de perspectiva de 4 puntos."""
        # Ordenar puntos: top-left, top-right, bottom-right, bottom-left
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect
        
        # Calcular dimensiones del rectángulo de destino
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Puntos de destino
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # Calcular matriz de transformación
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def order_points(self, pts: np.ndarray) -> np.ndarray:
        """Ordena puntos en orden: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype="float32")
        
        # Top-left: suma mínima, bottom-right: suma máxima
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right: diferencia mínima, bottom-left: diferencia máxima
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def auto_deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige automáticamente la inclinación del texto.
        
        Utiliza la transformada de Hough para detectar líneas de texto
        y calcular el ángulo de inclinación.
        """
        # Detectar bordes
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        
        # Detectar líneas usando transformada de Hough
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is None:
            return image
        
        # Calcular ángulos de las líneas
        angles = []
        for rho, theta in lines[:, 0]:
            angle = theta * 180 / np.pi - 90
            angles.append(angle)
        
        # Encontrar el ángulo mediano (más robusto que la media)
        median_angle = np.median(angles)
        
        # Si el ángulo es significativo, rotar la imagen
        if abs(median_angle) > 0.5:  # Umbral de 0.5 grados
            return self.rotate_image(image, median_angle)
        
        return image
    
    def rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Rota la imagen por el ángulo especificado."""
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Crear matriz de rotación
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calcular nuevas dimensiones
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))
        
        # Ajustar matriz de rotación
        M[0, 2] += (nW / 2) - center[0]
        M[1, 2] += (nH / 2) - center[1]
        
        # Aplicar rotación
        rotated = cv2.warpAffine(image, M, (nW, nH), 
                                flags=cv2.INTER_CUBIC, 
                                borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
    def assess_image_quality(self, image: np.ndarray) -> float:
        """
        Evalúa la calidad de la imagen para OCR.
        
        Returns:
            Score de calidad de 0.0 a 1.0
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Métricas de calidad
        sharpness = self.calculate_sharpness(gray)
        contrast = self.calculate_contrast(gray)
        brightness = self.calculate_brightness(gray)
        noise_level = self.calculate_noise(gray)
        
        # Combinar métricas (pesos basados en importancia para OCR)
        quality_score = (
            sharpness * 0.4 +      # Nitidez es crucial para OCR
            contrast * 0.3 +       # Contraste ayuda a separar texto del fondo
            brightness * 0.2 +     # Brillo adecuado mejora legibilidad
            (1 - noise_level) * 0.1  # Menos ruido es mejor
        )
        
        return min(1.0, max(0.0, quality_score))
    
    def calculate_sharpness(self, image: np.ndarray) -> float:
        """Calcula la nitidez usando la varianza del Laplaciano."""
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        # Normalizar a rango 0-1 (valor empírico)
        return min(1.0, laplacian_var / 1000.0)
    
    def calculate_contrast(self, image: np.ndarray) -> float:
        """Calcula el contraste como la desviación estándar normalizada."""
        contrast = image.std() / 255.0
        return min(1.0, contrast * 4)  # Factor de escala empírico
    
    def calculate_brightness(self, image: np.ndarray) -> float:
        """Calcula el brillo óptimo (penaliza imágenes muy oscuras o claras)."""
        mean_brightness = image.mean() / 255.0
        # Brillo óptimo alrededor de 0.5, penalizar extremos
        optimal_distance = abs(mean_brightness - 0.5)
        return 1.0 - (optimal_distance * 2)
    
    def calculate_noise(self, image: np.ndarray) -> float:
        """Estima el nivel de ruido usando filtro de mediana."""
        median_filtered = cv2.medianBlur(image, 5)
        noise = np.mean(np.abs(image.astype(float) - median_filtered.astype(float)))
        # Normalizar (valor empírico)
        return min(1.0, noise / 50.0)
