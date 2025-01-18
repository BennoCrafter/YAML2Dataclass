from config.credentials import Credentials
from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class Database:
    host: str
    port: int
    credentials: Credentials