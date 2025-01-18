from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class User:
    name: str
    age: int
    email: str
    roles: list[str]