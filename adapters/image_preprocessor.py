"""
Módulo para preprocesamiento de imágenes utilizando OpenCV.
Este módulo incluye funciones para mejorar la calidad de las imágenes antes de realizar OCR.
"""

import cv2
import numpy as np
from pathlib import Path

def preprocess_image(image_path: Path) -> np.ndarray:
    """
    Preprocesa una imagen para mejorar la precisión del OCR.
    Args:
        image_path (Path): Ruta de la imagen a procesar.

    Returns:
        np.ndarray: Imagen preprocesada lista para OCR.
    """
    # Leer la imagen en escala de grises
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    # Aplicar eliminación de ruido
    denoised = cv2.medianBlur(image, 3)

    # Mejorar el contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Binarización adaptativa
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return binary

if __name__ == "__main__":
    # Ejemplo de uso
    test_image = Path("example.jpg")
    processed_image = preprocess_image(test_image)
    cv2.imwrite("processed_example.jpg", processed_image)
