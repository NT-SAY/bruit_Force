"""
Configuration constants for the bruteforcer
"""

# Default attack strategies
DEFAULT_STRATEGIES = {
    'hash': {
        'batch_size': 1000,
        'use_vectorization': True,
        'max_workers': None
    },
    'web': {
        'delay': 0.1,
        'concurrency': 50,
        'max_retries': 3
    }
}

# Benchmark values for performance estimation
BENCHMARK_VALUES = {
    'hash_md5_cpu': 5000000,  # 5M hashes/sec
    'hash_md5_gpu': 10000000000,  # 10B hashes/sec
    'web_request_direct': 10,
    'web_request_proxy': 5
}