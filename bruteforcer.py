"""
Main bruteforcer class with intelligent attack coordination
"""

import asyncio
import time
import random
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any
import aiohttp
from aiohttp_socks import ProxyConnector
import logging
from fake_useragent import UserAgent

from .models import AttackType, ProtectionLevel, AttackResult
from ..engines.hash_engine import HashEngine
from ..engines.web_engine import WebEngine
from ..engines.rule_engine import RuleEngine
from ..engines.pattern_matcher import FastPatternMatcher
from ..managers.proxy_manager import ProxyManager
from ..managers.strategy_manager import AdaptiveStrategyManager
from ..managers.rate_limiter import RateLimiter
from ..utils.accelerators import CPUAccelerator, VectorizedHasher
from .estimators import TimeEstimator, IntelligentAdvisor

logger = logging.getLogger(__name__)

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
        
        # Движки атак
        self.hash_engine = HashEngine(self.cpu_accelerator, self.vector_hasher)
        self.web_engine = WebEngine(self.proxy_manager, self.pattern_matcher, self.rate_limiter, self.ua)
        
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
    
    async def hash_attack(self) -> Optional[str]:
        """Атака на хеш с выбором стратегии"""
        if self.current_strategy.get('use_cpu_acceleration', True):
            if len(self.wordlist) > 10000:
                # Для больших словарей используем векторизованный подход
                return await self.hash_engine.vectorized_attack(self.target, self.wordlist, self.stats)
            else:
                # Для средних словарей используем пакетную обработку
                return await self.hash_engine.batch_attack(self.target, self.wordlist, self.stats)
        else:
            # Стандартный последовательный подход
            return await self.hash_engine.sequential_attack(self.target, self.wordlist, self.stats, self.current_strategy)
    
    async def web_attack(self) -> Optional[str]:
        """Атака на веб-форму"""
        return await self.web_engine.attack(
            self.target, 
            self.wordlist, 
            self.stats, 
            self.current_strategy,
            self.adapt_to_protection,
            self.save_progress,
            self.adapt_based_on_stats
        )
    
    def adapt_to_protection(self, protection_strategy: Dict):
        """Адаптация к обнаруженной защите"""
        logger.warning(f"Adapting to protection: {protection_strategy}")
        self.current_strategy.update(protection_strategy)
    
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