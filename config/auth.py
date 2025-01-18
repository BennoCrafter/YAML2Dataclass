from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class Auth:
    secret: str
    expire_time: int
    rate_limit: str