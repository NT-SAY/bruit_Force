"""
Intelligent password rule engine for wordlist enhancement
"""

import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

# Глобальные функции для multiprocessing
def process_chunk_global(chunk, common_prefixes, common_suffixes):
    """Глобальная функция для обработки чанка паролей"""
    local_enhanced = set()
    for word in chunk:
        # Оригинальное слово
        local_enhanced.add(word)
        
        # Добавляем суффиксы
        for suffix in common_suffixes:
            local_enhanced.add(word + suffix)
            local_enhanced.add(word + '_' + suffix)
        
        # Добавляем префиксы
        for prefix in common_prefixes:
            local_enhanced.add(prefix + word)
            local_enhanced.add(prefix + '_' + word)
        
        # Применяем трансформации
        transformations = [
            lambda x: x.upper(),
            lambda x: x.capitalize(),
            lambda x: x.lower(),
            lambda x: x + x,
            lambda x: x[::-1],
            lambda x: x.replace('a', '@').replace('e', '3').replace('i', '1'),
        ]
        
        for transform in transformations:
            try:
                transformed = transform(word)
                if transformed:
                    local_enhanced.add(transformed)
            except:
                continue
    
    return local_enhanced

class RuleEngine:
    """Генератор умных правил для паролей"""
    
    def __init__(self):
        self.common_suffixes = [
            '123', '!', '@', '#', '$', '%', '^', '&', '*', '()',
            '2023', '2024', '2025', '01', '02', '1', '2', '00'
        ]
        
        self.common_prefixes = [
            'admin', 'root', 'user', 'test', 'temp', 'super'
        ]
        
    def enhance_wordlist(self, base_words: List[str]) -> List[str]:
        """Улучшение словаря с помощью правил"""
        enhanced = set()
        
        for word in base_words:
            enhanced.add(word)
            
            for suffix in self.common_suffixes:
                enhanced.add(word + suffix)
                enhanced.add(word + '_' + suffix)
            
            for prefix in self.common_prefixes:
                enhanced.add(prefix + word)
                enhanced.add(prefix + '_' + word)
            
            # Применяем трансформации
            transformations = [
                lambda x: x.upper(),
                lambda x: x.capitalize(),
                lambda x: x.lower(),
                lambda x: x + x,
                lambda x: x[::-1],
                lambda x: x.replace('a', '@').replace('e', '3').replace('i', '1'),
            ]
            
            for transform in transformations:
                try:
                    transformed = transform(word)
                    if transformed:
                        enhanced.add(transformed)
                except:
                    continue
        
        return list(enhanced)
    
    def parallel_enhance(self, base_words: List[str], chunk_size: int = 1000) -> List[str]:
        """Параллельное улучшение словаря с использованием глобальной функции"""
        enhanced = set(base_words)
        
        # Разбиваем на чанки для параллельной обработки
        chunks = [base_words[i:i + chunk_size] for i in range(0, len(base_words), chunk_size)]
        
        with ProcessPoolExecutor() as executor:
            # Используем глобальную функцию вместо метода класса
            futures = [
                executor.submit(
                    process_chunk_global, 
                    chunk, 
                    self.common_prefixes, 
                    self.common_suffixes
                )
                for chunk in chunks
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    enhanced.update(future.result())
                except Exception as e:
                    logger.error(f"Error processing chunk: {e}")
        
        return list(enhanced)