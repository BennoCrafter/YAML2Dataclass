from config.auth import Auth
from config.database import Database
from config.logging import Logging
from config.metrics import Metrics
from dataclasses import dataclass
from typing import Optional, List, Any, Union

@dataclass
class Config:
    auth: Auth
    database: Database
    logging: Logging
    metrics: Metrics