from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class Credentials:
    user: str
    password: str