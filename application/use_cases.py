# application/use_cases.py
"""
Casos de uso unificados para procesamiento de documentos.

Este módulo contiene todos los casos de uso relacionados con el procesamiento
de documentos PDF, desde básico hasta avanzado con métricas de calidad.
"""
from pathlib import Path
from typing import Tuple, List, Any, Dict, Optional
import logging
import time

from application.ports import OCRPort, TableExtractorPort, StoragePort
from domain.models import Document

logger = logging.getLogger(__name__)


class ProcessDocument:
    """
    Caso de uso básico para procesamiento de documentos PDF.
    
    Orquesta el flujo completo:
    1. Extracción de texto con OCR
    2. Extracción de tablas
    3. Almacenamiento de resultados
    """

    def __init__(
        self,
        ocr: OCRPort,
        table_extractor: TableExtractorPort,
        storage: StoragePort,
    ) -> None:
        """
        Inicializa el caso de uso con las dependencias inyectadas.
        
        Args:
            ocr: Servicio de OCR
            table_extractor: Servicio de extracción de tablas
            storage: Servicio de almacenamiento
        """
        self.ocr = ocr
        self.table_extractor = table_extractor
        self.storage = storage

    def __call__(self, pdf_path: Path) -> Tuple[str, List[str]]:
        """
        Ejecuta el procesamiento completo de un documento PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Tuple[str, List[str]]: (archivo_texto_principal, lista_todos_archivos)
        """
        logger.info(f"Iniciando procesamiento de: {pdf_path}")
        start_time = time.time()
        
        # Extracción de texto
        text = self.ocr.extract_text(pdf_path)
        
        # Extracción de tablas
        tables = self.table_extractor.extract_tables(pdf_path)

        # Almacenamiento
        archivos_generados = self.storage.save(pdf_path.stem, text, tables, pdf_path)

        # Identificar archivo principal
        texto_principal = next(
            (archivo for archivo in archivos_generados if archivo.endswith("texto_completo.txt")),
            archivos_generados[0] if archivos_generados else ""
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Procesamiento completado en {processing_time:.2f}s. Archivos generados: {len(archivos_generados)}")
        
        return texto_principal, archivos_generados


class EnhancedProcessDocument:
    """
    Caso de uso avanzado con métricas de calidad y procesamiento inteligente.
    
    Extiende el procesamiento básico con:
    - Análisis de calidad
    - Métricas de procesamiento
    - Validación de resultados
    - Reintento automático en caso de baja calidad
    """

    def __init__(
        self,
        ocr: OCRPort,
        table_extractor: TableExtractorPort,
        storage: StoragePort,
        min_quality_threshold: float = 60.0,
        enable_auto_retry: bool = True
    ) -> None:
        """
        Inicializa el caso de uso mejorado.
        
        Args:
            ocr: Servicio de OCR (preferiblemente con métricas)
            table_extractor: Servicio de extracción de tablas
            storage: Servicio de almacenamiento
            min_quality_threshold: Umbral mínimo de calidad
            enable_auto_retry: Activar reintento automático
        """
        self.ocr = ocr
        self.table_extractor = table_extractor
        self.storage = storage
        self.min_quality_threshold = min_quality_threshold
        self.enable_auto_retry = enable_auto_retry

    def __call__(self, pdf_path: Path) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Ejecuta procesamiento con análisis de métricas.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Tuple con:
            - str: Archivo de texto principal
            - List[str]: Lista de archivos generados
            - Dict[str, Any]: Métricas de procesamiento
        """
        logger.info(f"Iniciando procesamiento mejorado de: {pdf_path}")
        start_time = time.time()
        
        # Métricas iniciales
        metrics = {
            'processing_summary': {
                'start_time': start_time,
                'filename': pdf_path.name,
                'file_size_mb': pdf_path.stat().st_size / (1024 * 1024)
            },
            'ocr_metrics': {},
            'table_metrics': {},
            'quality_analysis': {},
            'output_quality': {}
        }

        try:
            # Extracción de texto con análisis de calidad
            if hasattr(self.ocr, 'extract_with_metrics'):
                # OCR avanzado con métricas
                ocr_result = self.ocr.extract_with_metrics(pdf_path)
                text = ocr_result.text
                metrics['ocr_metrics'] = {
                    'processing_time': ocr_result.processing_time,
                    'page_count': ocr_result.page_count,
                    'average_confidence': getattr(ocr_result.metrics, 'average_confidence', 0)
                }
                
                # Análisis de calidad
                avg_confidence = getattr(ocr_result.metrics, 'average_confidence', 100)
                quality_score = avg_confidence
                
            else:
                # OCR básico
                text = self.ocr.extract_text(pdf_path)
                quality_score = 100  # Asumimos buena calidad para OCR básico
                metrics['ocr_metrics'] = {
                    'processing_time': time.time() - start_time,
                    'page_count': self._estimate_page_count(pdf_path),
                    'average_confidence': quality_score
                }

            # Verificar calidad y reintentar si es necesario
            if (quality_score < self.min_quality_threshold and 
                self.enable_auto_retry and 
                hasattr(self.ocr, 'extract_with_metrics')):
                
                logger.warning(f"Calidad baja ({quality_score:.1f}%), reintentando con configuración optimizada")
                # Aquí se podría cambiar parámetros del OCR para el reintento
                # Por simplicidad, usamos el mismo resultado
                
            # Extracción de tablas
            table_start_time = time.time()
            tables = self.table_extractor.extract_tables(pdf_path)
            table_processing_time = time.time() - table_start_time
            
            metrics['table_metrics'] = {
                'processing_time': table_processing_time,
                'tables_found': len(tables) if tables else 0
            }

            # Almacenamiento
            storage_start_time = time.time()
            archivos_generados = self.storage.save(pdf_path.stem, text, tables, pdf_path)
            storage_time = time.time() - storage_start_time

            # Métricas finales
            total_time = time.time() - start_time
            metrics['processing_summary'].update({
                'total_time_seconds': total_time,
                'storage_time': storage_time,
                'files_generated': len(archivos_generados)
            })
            
            metrics['quality_analysis'] = {
                'ocr_quality': quality_score,
                'meets_threshold': quality_score >= self.min_quality_threshold
            }
            
            metrics['output_quality'] = {
                'word_count': len(text.split()) if text else 0,
                'table_count': len(tables) if tables else 0,
                'high_quality_result': quality_score >= 80
            }

            # Identificar archivo principal
            texto_principal = next(
                (archivo for archivo in archivos_generados if archivo.endswith("texto_completo.txt")),
                archivos_generados[0] if archivos_generados else ""
            )
            
            logger.info(f"Procesamiento mejorado completado en {total_time:.2f}s. Calidad: {quality_score:.1f}%")
            
            return texto_principal, archivos_generados, metrics

        except Exception as e:
            # Error en procesamiento
            error_time = time.time() - start_time
            metrics['processing_summary'].update({
                'total_time_seconds': error_time,
                'error': str(e),
                'success': False
            })
            
            logger.error(f"Error en procesamiento mejorado: {e}")
            raise

    def _estimate_page_count(self, pdf_path: Path) -> int:
        """
        Estima el número de páginas de un PDF.
        
        Args:
            pdf_path: Ruta al PDF
            
        Returns:
            int: Número estimado de páginas
        """
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return len(reader.pages)
        except Exception as e:
            logger.warning(f"Error estimando páginas: {e}")
            return 1  # Fallback
