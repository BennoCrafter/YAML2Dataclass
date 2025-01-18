from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class Logging:
    level: str
    format: str
    outputs: list[str]