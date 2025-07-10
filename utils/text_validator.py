# utils/text_validator.py
"""
Módulo para validación y corrección automática de texto OCR.

Este módulo implementa técnicas de corrección de errores comunes
en el reconocimiento óptico de caracteres y validación de texto.
"""
from typing import Dict, List, Set
import re
import unicodedata


class TextValidator:
    """
    Validador y corrector de texto para resultados de OCR.
    
    Implementa corrección de errores comunes, validación ortográfica
    y limpieza de texto para mejorar la calidad de la salida OCR.
    """
    
    def __init__(self, language: str = 'es'):
        """
        Inicializa el validador de texto.
        
        Args:
            language: Idioma para la corrección ('es', 'en', etc.)
        """
        self.language = language
        
        # Errores comunes de OCR (carácter incorrecto -> carácter correcto)
        self.common_ocr_errors = {
            # Confusiones numéricas/letras
            '0': 'O', 'O': '0',  # Contextual
            '1': 'l', 'l': '1', 'I': '1',  # Contextual
            '5': 'S', 'S': '5',  # Contextual
            '6': 'G', 'G': '6',  # Contextual
            '8': 'B', 'B': '8',  # Contextual
            
            # Confusiones de letras
            'rn': 'm', 'vv': 'w', 'nn': 'ñ',
            'cl': 'd', 'fi': 'ñ', 'li': 'h',
            
            # Caracteres especiales mal reconocidos
            '¢': 'c', '€': 'e', '£': 'E',
            '§': 's', '¿': '?', '¡': '!',
            
            # Espacios y puntuación
            ' ,': ',', ' .': '.', ' ;': ';',
            '( ': '(', ' )': ')', '[ ': '[', ' ]': ']'
        }
        
        # Patrones de palabras comunes en español
        self.spanish_patterns = {
            'articles': {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'},
            'prepositions': {'a', 'ante', 'bajo', 'con', 'contra', 'de', 'desde', 
                           'en', 'entre', 'hacia', 'hasta', 'para', 'por', 'según', 
                           'sin', 'sobre', 'tras'},
            'common_words': {'que', 'de', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 
                           'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 
                           'al', 'la', 'el', 'del', 'los', 'se', 'las', 'y', 'una'}
        }
        
        # Expresiones regulares para detección de patrones
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'url': re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            'phone': re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
            'date': re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
            'number': re.compile(r'\b\d+([.,]\d+)?\b'),
            'word_boundaries': re.compile(r'\b\w+\b')
        }
    
    def auto_correct_ocr_errors(self, text: str) -> str:
        """
        Corrige errores comunes de OCR en el texto.
        
        Args:
            text: Texto con posibles errores de OCR
            
        Returns:
            Texto corregido
        """
        corrected = text
        
        # 1. Normalización Unicode
        corrected = unicodedata.normalize('NFKC', corrected)
        
        # 2. Corrección de patrones conocidos
        for error, correction in self.common_ocr_errors.items():
            corrected = corrected.replace(error, correction)
        
        # 3. Corrección contextual de números/letras
        corrected = self.contextual_number_letter_correction(corrected)
        
        # 4. Limpieza de espacios múltiples
        corrected = re.sub(r'\s+', ' ', corrected)
        
        # 5. Corrección de puntuación
        corrected = self.fix_punctuation(corrected)
        
        # 6. Corrección de capitalización
        corrected = self.fix_capitalization(corrected)
        
        return corrected.strip()
    
    def contextual_number_letter_correction(self, text: str) -> str:
        """
        Corrige confusiones entre números y letras basándose en el contexto.
        """
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            # Obtener contexto
            prev_word = words[i-1].lower() if i > 0 else ""
            next_word = words[i+1].lower() if i < len(words)-1 else ""
            
            corrected_word = word
            
            # Si la palabra anterior/siguiente es un artículo o preposición,
            # es probable que esta palabra sea texto, no números
            if (prev_word in self.spanish_patterns['articles'] or 
                prev_word in self.spanish_patterns['prepositions'] or
                next_word in self.spanish_patterns['articles']):
                
                # Convertir números que parecen letras en contexto de texto
                corrected_word = corrected_word.replace('0', 'O')
                corrected_word = corrected_word.replace('1', 'l')
                corrected_word = corrected_word.replace('5', 'S')
            
            # Si contiene caracteres no numéricos, probablemente es texto
            elif re.search(r'[a-zA-Z]', word):
                # Mantener como texto, corregir números mal reconocidos
                corrected_word = corrected_word.replace('0', 'O')
                corrected_word = corrected_word.replace('1', 'l')
            
            # Si es completamente numérico o contiene puntos/comas, mantener números
            elif re.match(r'^[\d.,]+$', word):
                corrected_word = corrected_word.replace('O', '0')
                corrected_word = corrected_word.replace('l', '1')
                corrected_word = corrected_word.replace('S', '5')
            
            corrected_words.append(corrected_word)
        
        return ' '.join(corrected_words)
    
    def fix_punctuation(self, text: str) -> str:
        """Corrige errores comunes de puntuación."""
        # Espacios antes de puntuación
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        
        # Espacios después de puntuación
        text = re.sub(r'([,.;:!?])([^\s])', r'\1 \2', text)
        
        # Paréntesis y corchetes
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        text = re.sub(r'\[\s+', '[', text)
        text = re.sub(r'\s+\]', ']', text)
        
        # Comillas
        text = re.sub(r'"\s+', '"', text)
        text = re.sub(r'\s+"', '"', text)
        
        return text
    
    def fix_capitalization(self, text: str) -> str:
        """Corrige errores de capitalización."""
        # Dividir en oraciones
        sentences = re.split(r'[.!?]+', text)
        corrected_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Capitalizar primera letra de cada oración
                sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                corrected_sentences.append(sentence)
        
        # Reunir oraciones
        result = '. '.join(corrected_sentences)
        
        # Capitalizar después de otros signos de puntuación
        result = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)
        
        return result
    
    def detect_language_confidence(self, text: str) -> Dict[str, float]:
        """
        Detecta el idioma del texto y devuelve un score de confianza.
        
        Returns:
            Dict con idiomas detectados y sus scores de confianza
        """
        # Contar palabras comunes en español
        words = set(re.findall(r'\b\w+\b', text.lower()))
        spanish_words = words.intersection(self.spanish_patterns['common_words'])
        spanish_ratio = len(spanish_words) / len(words) if words else 0
        
        # Detectar caracteres específicos del español
        spanish_chars = len(re.findall(r'[ñáéíóúü]', text.lower()))
        char_bonus = min(0.2, spanish_chars / len(text)) if text else 0
        
        spanish_confidence = min(1.0, spanish_ratio + char_bonus)
        
        return {
            'spanish': spanish_confidence,
            'english': 1.0 - spanish_confidence,  # Simplificado
            'unknown': max(0, 1.0 - spanish_confidence * 2)
        }
    
    def validate_extracted_data(self, text: str) -> Dict[str, List[str]]:
        """
        Extrae y valida datos estructurados del texto.
        
        Returns:
            Dict con tipos de datos encontrados y sus valores
        """
        extracted = {
            'emails': [],
            'urls': [],
            'phones': [],
            'dates': [],
            'numbers': []
        }
        
        # Extraer emails
        extracted['emails'] = self.patterns['email'].findall(text)
        
        # Extraer URLs
        extracted['urls'] = self.patterns['url'].findall(text)
        
        # Extraer teléfonos
        extracted['phones'] = self.patterns['phone'].findall(text)
        
        # Extraer fechas
        extracted['dates'] = self.patterns['date'].findall(text)
        
        # Extraer números
        extracted['numbers'] = self.patterns['number'].findall(text)
        
        return extracted
    
    def calculate_text_quality_score(self, text: str) -> float:
        """
        Calcula un score de calidad del texto extraído.
        
        Returns:
            Score de 0.0 a 1.0 indicando la calidad del texto
        """
        if not text.strip():
            return 0.0
        
        # Métricas de calidad
        metrics = {
            'word_ratio': self.calculate_word_ratio(text),
            'punctuation_ratio': self.calculate_punctuation_ratio(text),
            'capitalization_score': self.calculate_capitalization_score(text),
            'special_chars_ratio': self.calculate_special_chars_ratio(text),
            'line_consistency': self.calculate_line_consistency(text)
        }
        
        # Combinar métricas con pesos
        quality_score = (
            metrics['word_ratio'] * 0.3 +
            metrics['punctuation_ratio'] * 0.2 +
            metrics['capitalization_score'] * 0.2 +
            (1 - metrics['special_chars_ratio']) * 0.2 +
            metrics['line_consistency'] * 0.1
        )
        
        return min(1.0, max(0.0, quality_score))
    
    def calculate_word_ratio(self, text: str) -> float:
        """Calcula la proporción de palabras válidas."""
        words = re.findall(r'\b\w+\b', text)
        if not words:
            return 0.0
        
        valid_words = sum(1 for word in words if len(word) > 1 and word.isalpha())
        return valid_words / len(words)
    
    def calculate_punctuation_ratio(self, text: str) -> float:
        """Calcula si la puntuación está bien distribuida."""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 2:
            return 0.5  # Texto muy corto
        
        avg_sentence_length = sum(len(s.strip().split()) for s in sentences) / len(sentences)
        # Longitud ideal entre 10-25 palabras por oración
        if 10 <= avg_sentence_length <= 25:
            return 1.0
        elif 5 <= avg_sentence_length <= 35:
            return 0.7
        else:
            return 0.3
    
    def calculate_capitalization_score(self, text: str) -> float:
        """Evalúa si la capitalización es apropiada."""
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.0
        
        properly_capitalized = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence[0].isupper():
                properly_capitalized += 1
        
        return properly_capitalized / len(sentences) if sentences else 0.0
    
    def calculate_special_chars_ratio(self, text: str) -> float:
        """Calcula la proporción de caracteres especiales problemáticos."""
        if not text:
            return 0.0
        
        # Caracteres que suelen indicar errores de OCR
        problematic_chars = re.findall(r'[~`@#$%^&*+={}|\[\]\\:";\'<>?/]', text)
        return len(problematic_chars) / len(text)
    
    def calculate_line_consistency(self, text: str) -> float:
        """Evalúa la consistencia entre líneas del texto."""
        lines = text.split('\n')
        if len(lines) < 2:
            return 1.0
        
        # Evaluar si las líneas tienen longitudes similares (para texto en columnas)
        line_lengths = [len(line.strip()) for line in lines if line.strip()]
        if not line_lengths:
            return 0.0
        
        avg_length = sum(line_lengths) / len(line_lengths)
        variance = sum((length - avg_length) ** 2 for length in line_lengths) / len(line_lengths)
        
        # Normalizar varianza (menor varianza = mayor consistencia)
        consistency = 1.0 / (1.0 + variance / 100)
        return min(1.0, consistency)
