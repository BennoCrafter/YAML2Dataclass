from yaml2dataclass import ConfigLoader
from config.config import Config
from pathlib import Path


if __name__ == '__main__':
    config: Config = ConfigLoader(Config).load_config(Path('config.yaml'))

    print(config.author)
    print(config.server.host)
    print(config.events)
    print(config.events[0].name)
    print(config.events[0].description)
