"""
Fast protection pattern detection and analysis
"""

import re
from typing import Optional, Dict

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