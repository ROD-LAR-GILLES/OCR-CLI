# config/system_config.py
"""
Configuraciones del sistema OCR-CLI.

Este módulo centraliza todas las configuraciones del sistema,
incluyendo parámetros de calidad, preprocesamiento y procesamiento.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class SystemConfig:
    """Configuración simplificada del sistema OCR-CLI."""
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
    
    @classmethod
    def create_high_quality_config(cls) -> 'SystemConfig':
        """Configuración para máxima calidad."""
        return cls(
            dpi=600,
            confidence_threshold=80.0,
            enable_deskewing=True,
            enable_denoising=True,
            enable_contrast_enhancement=True,
            enable_auto_retry=True,
            max_processing_time_minutes=60
        )
    
    @classmethod
    def create_fast_config(cls) -> 'SystemConfig':
        """Configuración para procesamiento rápido."""
        return cls(
            dpi=150,
            confidence_threshold=50.0,
            enable_deskewing=False,
            enable_denoising=False,
            enable_contrast_enhancement=True,
            enable_auto_retry=False,
            max_processing_time_minutes=10
        )
    
    @classmethod
    def create_balanced_config(cls) -> 'SystemConfig':
        """Configuración balanceada (por defecto)."""
        return cls()


# Perfiles de calidad simplificados
QUALITY_PROFILES = {
    'maximum_quality': SystemConfig.create_high_quality_config(),
    'fast_processing': SystemConfig.create_fast_config(),
    'balanced': SystemConfig.create_balanced_config()
}
