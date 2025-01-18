from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Settings:
    enable_logging: bool
    debug_mode: bool
    max_connections: int