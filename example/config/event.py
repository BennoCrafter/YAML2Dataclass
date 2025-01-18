from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Event:
    name: str
    description: str
    enabled: bool