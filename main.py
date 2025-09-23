#!/usr/bin/env python3
"""
Главный файл запуска интеллектуального брутфорсера
"""

import asyncio
import argparse
import logging
from core.bruteforcer import UltimateBruteForcer
from core.models import AttackType

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

async def main():
    print("=== INTELLIGENT BRUTEFORCER WITH TIME ESTIMATION ===")
    
    # Парсинг аргументов командной строки
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
    asyncio.run(main())