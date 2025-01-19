# yaml2dataclass

Convert YAML to dataclass

## Installation

```bash
pip install git+https://github.com/bennocrafter/yaml2dataclass.git
```

### Local
```bash
pip install -e .
```


## Usage

Look at the [example](example/)

```python
from yaml2dataclass import ConfigLoader
from config.config import Config
from pathlib import Path


if __name__ == '__main__':
    config: Config = ConfigLoader(Config).load_config(Path('config.yaml'))

    print(config.author)
    print(config.server.host)
    print(config.events[0].name)
```

Run the dataclasses generator in the working directory
```bash
yaml2dataclass yaml_src_file.yaml dest_folder
```
