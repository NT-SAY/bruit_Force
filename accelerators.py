"""
CPU acceleration and vectorized computation utilities
"""

import hashlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import concurrent.futures
from multiprocessing import cpu_count
from typing import List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class CPUAccelerator:
    """Ускоритель вычислений на CPU с многопроцессорностью"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or (cpu_count() - 1 or 1)
        logger.info(f"CPU Accelerator initialized with {self.max_workers} workers")
    
    def parallel_hash_check(self, target_hash: str, password_chunks: List[List[str]]) -> Optional[str]:
        """Параллельная проверка хешей с использованием глобальной функции"""
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Используем starmap для передачи нескольких аргументов
            futures = [
                executor.submit(hash_chunk_global, chunk, target_hash)
                for chunk in password_chunks
            ]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    # Останавливаем другие процессы если нашли пароль
                    for f in futures:
                        f.cancel()
                    return result
        
        return None

class VectorizedHasher:
    """Векторизованные вычисления хешей с NumPy"""
    
    def __init__(self):
        self.hash_functions = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256
        }
    
    def vectorized_hash_batch(self, passwords: List[str], hash_type: str = "md5") -> np.ndarray:
        """Векторизованное вычисление хешей для батча"""
        hash_func = self.hash_functions.get(hash_type, hashlib.md5)
        results = []
        
        for password in passwords:
            results.append(hash_func(password.encode()).hexdigest())
        
        return np.array(results)
    
    def find_hash_match_vectorized(self, target_hash: str, hashes: np.ndarray, passwords: np.ndarray) -> Optional[str]:
        """Векторизованный поиск совпадения"""
        matches = np.where(hashes == target_hash)[0]
        if len(matches) > 0:
            return passwords[matches[0]]
        return None