from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class Metrics:
    enabled: bool
    endpoint: str