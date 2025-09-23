"""
Data models and enumerations
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class AttackType(Enum):
    HASH = "hash"
    WEB = "web"
    SSH = "ssh"
    API = "api"

class ProtectionLevel(Enum):
    NONE = 0
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    VERY_STRONG = 4

@dataclass
class AttackResult:
    success: bool
    password: Optional[str] = None
    attempts: int = 0
    time_taken: float = 0.0
    strategy_used: str = "direct"