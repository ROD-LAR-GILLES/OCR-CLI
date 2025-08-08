"""
Adaptador de Tesseract + OpenCV para OCR con preprocesamiento opcional.

Implementación con imports perezosos y fallbacks seguros para ejecución en entornos
sin dependencias completas (tests). Cuando las librerías están disponibles, aplica
un pipeline mínimo de mejora.
"""
from pathlib import Path
from application.ports import OCRPort


class TesseractOpenCVAdapter(OCRPort):
    """Adaptador OpenCV con flags de preprocesamiento."""

    def __init__(self, *, enable_deskewing: bool, enable_denoising: bool, enable_contrast_enhancement: bool) -> None:
        self.enable_deskewing = enable_deskewing
        self.enable_denoising = enable_denoising
        self.enable_contrast_enhancement = enable_contrast_enhancement

    def extract_text(self, pdf_path: Path) -> str:
        if not pdf_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")
        
        # Imports perezosos
        try:
            from pdf2image import convert_from_path  # type: ignore
            import pytesseract  # type: ignore
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception:
            return ""
        
        try:
            images = convert_from_path(str(pdf_path), dpi=300)
        except Exception:
            return ""
        
        textos = []
        for pil_img in images:
            try:
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
                # Denoising
                if self.enable_denoising:
                    img = cv2.medianBlur(img, 3)
                # Contraste
                if self.enable_contrast_enhancement:
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    img = clahe.apply(img)
                # Binarización
                img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5)
                # Deskew básico
                if self.enable_deskewing:
                    coords = cv2.findNonZero(255 - img)
                    if coords is not None:
                        rect = cv2.minAreaRect(coords)
                        angle = rect[-1]
                        if angle < -45:
                            angle = -(90 + angle)
                        else:
                            angle = -angle
                        (h, w) = img.shape[:2]
                        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                        img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                
                texto = pytesseract.image_to_string(img, lang="spa")
            except Exception:
                texto = ""
            textos.append(texto.strip())
        
        return "\n\n".join(filter(None, textos))
