from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Database:
    username: str
    password: str
    host: str