from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Server:
    host: str
    port: int