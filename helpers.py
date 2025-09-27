"""
Global helper functions for multiprocessing
"""

import hashlib
from typing import List, Optional

def hash_chunk_global(chunk: List[str], target_hash: str) -> Optional[str]:
    """Глобальная функция для проверки хешей в чанке"""
    for password in chunk:
        if hashlib.md5(password.encode()).hexdigest() == target_hash:
            return password
    return None