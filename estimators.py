"""
Intelligent time estimation and advisory system
"""

import time
from typing import Dict, Any, List
from .models import ProtectionLevel

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