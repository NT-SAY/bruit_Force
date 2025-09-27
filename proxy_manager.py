"""
Intelligent proxy management with automatic verification
"""

import asyncio
import random
from typing import List, Optional, Set
from pathlib import Path
import aiohttp
from aiohttp_socks import ProxyConnector
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    """Умный менеджер прокси с автоматической проверкой"""
    
    def __init__(self):
        self.proxies = []
        self.good_proxies = []
        self.bad_proxies = set()
        self.proxy_stats = {}
        self.rotation_count = 0
    
    def load_proxies(self, proxy_file: str = None, proxy_list: List[str] = None):
        """Загрузка прокси из файла или списка"""
        if proxy_file and Path(proxy_file).exists():
            with open(proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
        elif proxy_list:
            self.proxies = proxy_list
        
        self.good_proxies = self.proxies.copy()
        logger.info(f"Loaded {len(self.proxies)} proxies")
    
    async def verify_proxy(self, proxy: str) -> bool:
        """Проверка работоспособности прокси"""
        try:
            connector = ProxyConnector.from_url(proxy)
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                test_urls = [
                    'http://httpbin.org/ip',
                    'http://api.ipify.org',
                    'http://icanhazip.com'
                ]
                
                for url in test_urls:
                    try:
                        async with session.get(url, timeout=10) as response:
                            if response.status == 200:
                                return True
                    except:
                        continue
        except:
            pass
        return False
    
    async def verify_all_proxies(self):
        """Проверка всех прокси"""
        logger.info("Verifying proxies...")
        tasks = [self.verify_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.good_proxies = [
            proxy for proxy, working in zip(self.proxies, results) 
            if working is True
        ]
        
        logger.info(f"Verified: {len(self.good_proxies)} good, {len(self.proxies) - len(self.good_proxies)} bad proxies")
    
    def get_proxy(self) -> Optional[str]:
        """Получение случайного рабочего прокси"""
        if not self.good_proxies:
            return None
        
        self.rotation_count += 1
        if self.rotation_count % 10 == 0:
            random.shuffle(self.good_proxies)
        
        return random.choice(self.good_proxies)
    
    def mark_bad_proxy(self, proxy: str):
        """Пометить прокси как плохой"""
        if proxy in self.good_proxies:
            self.good_proxies.remove(proxy)
        self.bad_proxies.add(proxy)
        logger.warning(f"Marked proxy as bad: {proxy}")