from yaml2dataclass import ConfigLoader
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    tools_path: str
    tools: list[dict[str, str]]

config_loader = ConfigLoader(config_class=Config)
config = config_loader.load_config(Path("config.yaml"))
print(config)
