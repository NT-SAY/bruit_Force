"""
Hash cracking engine with multiple optimization strategies
"""

import asyncio
import hashlib
import logging
from typing import List, Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class HashEngine:
    """Движок для атак на хеши с различными стратегиями оптимизации"""
    
    def __init__(self, cpu_accelerator, vector_hasher):
        self.cpu_accelerator = cpu_accelerator
        self.vector_hasher = vector_hasher
    
    async def sequential_attack(self, target_hash: str, wordlist: List[str], 
                              stats: Dict, strategy: Dict) -> Optional[str]:
        """Стандартная последовательная атака"""
        logger.info("Starting sequential hash attack...")
        
        for password in wordlist:
            if stats.get('found', False):
                break
                
            if await self.try_password_hash(target_hash, password, stats):
                stats['found'] = True
                return password
            
            await asyncio.sleep(strategy.get('delay', 0.1))
        
        return None
    
    async def batch_attack(self, target_hash: str, wordlist: List[str], 
                          stats: Dict) -> Optional[str]:
        """Пакетная атака на хеш с CPU-ускорением"""
        logger.info("Starting batch hash attack with CPU acceleration...")
        
        batch_size = 1000
        chunks = [wordlist[i:i + batch_size] for i in range(0, len(wordlist), batch_size)]
        
        for i, chunk in enumerate(chunks):
            if stats.get('found', False):
                break
            
            logger.info(f"Processing batch {i+1}/{len(chunks)} ({len(chunk)} passwords)")
            
            # Используем CPU-ускорение для пакетной обработки
            result = self.cpu_accelerator.parallel_hash_check(target_hash, [chunk])
            
            if result:
                stats['found'] = True
                stats['attempts'] += (i * batch_size) + chunk.index(result) + 1
                return result
            
            stats['attempts'] += len(chunk)
            # Небольшая задержка между батчами
            await asyncio.sleep(0.01)
        
        return None
    
    async def vectorized_attack(self, target_hash: str, wordlist: List[str], 
                               stats: Dict) -> Optional[str]:
        """Векторизованная атака на хеш"""
        logger.info("Starting vectorized hash attack...")
        
        batch_size = 5000
        passwords_array = np.array(wordlist)
        
        for i in range(0, len(passwords_array), batch_size):
            if stats.get('found', False):
                break
            
            batch = passwords_array[i:i + batch_size]
            logger.info(f"Processing vectorized batch {i//batch_size + 1}/{(len(passwords_array)-1)//batch_size + 1}")
            
            # Векторизованное вычисление хешей
            hashes = self.vector_hasher.vectorized_hash_batch(batch.tolist(), "md5")
            
            # Векторизованный поиск совпадений
            result = self.vector_hasher.find_hash_match_vectorized(target_hash, hashes, batch)
            
            if result:
                stats['found'] = True
                stats['attempts'] += i + np.where(batch == result)[0][0] + 1
                return result
            
            stats['attempts'] += len(batch)
            await asyncio.sleep(0.001)
        
        return None
    
    async def try_password_hash(self, target_hash: str, password: str, stats: Dict) -> bool:
        """Проверка пароля для хеша"""
        password_hash = hashlib.md5(password.encode()).hexdigest()
        stats['attempts'] += 1
        return password_hash == target_hash