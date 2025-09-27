"""
Adaptive attack strategy management
"""

import time
from typing import List, Dict
from ..core.models import ProtectionLevel

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