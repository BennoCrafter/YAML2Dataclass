from dataclasses import dataclass
from config.database import Database
from config.event import Event
from config.server import Server
from config.settings import Settings
from typing import Optional, Any

@dataclass
class Config:
    name: str
    version: str
    description: str
    author: str
    server: Server
    database: Database
    settings: Settings
    events: list[Event]
