from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Optional, Type, TypeVar, Union
import logging
from ruamel.yaml import YAML

T = TypeVar("T")


class ConfigLoader:
    _instance: Optional["ConfigLoader"] = None
    _config: Optional[Any] = None
    _logger = logging.getLogger(__name__)

    def __new__(cls, *args, **kwargs) -> "ConfigLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_class: Type[T]):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            if not is_dataclass(config_class):
                raise TypeError("config_class must be a dataclass.")
            self._config_class = config_class
            # Set up logging handler if none exists
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self._logger.addHandler(handler)

    def load_config(self, file_path: Union[Path, str]) -> T: # type: ignore
        if self._config is None:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path

            if not file_path.exists() or not file_path.is_file():
                raise FileNotFoundError(f"Configuration file not found: {file_path}")

            with file_path.open("r") as file:
                yaml_data = YAML(typ="safe").load(file)
                self._config = self._from_dict(self._config_class, yaml_data)

        return self._config

    def get_config(self) -> T: # type: ignore
        if self._config is None:
            raise RuntimeError("Configuration hasn't been loaded yet. Call load_config first.")
        return self._config

    def reset_config(self):
        self._config = None

    @staticmethod
    def _from_dict(data_class: Type[T], data: dict) -> T:
        if not is_dataclass(data_class):
            raise TypeError(f"Expected a dataclass type, got {type(data_class)}.")

        fieldtypes = {field.name: field.type for field in fields(data_class)}
        field_values = {}

        for field_name, field_type in fieldtypes.items():
            if field_name not in data:
                raise ValueError(f"Missing field {field_name} in config.")

            if is_dataclass(field_type):
                ConfigLoader._logger.debug(f"{data_class}:  {field_name}, {field_type} is dataclass")
                field_value = ConfigLoader._from_dict(field_type, data[field_name]) # type: ignore

            elif hasattr(field_type, "__origin__") and field_type.__origin__ is list: # type: ignore
                type_arg = field_type.__args__[0] # type: ignore
                ConfigLoader._logger.debug(f"{data_class}:  {field_name}, {field_type} is list with type arg {type_arg}")
                if is_dataclass(type_arg):
                    ConfigLoader._logger.debug(f"{data_class}:  {field_name}, {field_type} is list of dataclasses")
                    field_value = [ConfigLoader._from_dict(type_arg, item) for item in data[field_name]] # type: ignore
                else:
                    field_value = data[field_name]
            else:
                ConfigLoader._logger.debug(f"{data_class}:  {field_name}, {field_type} is simple")
                field_value = data[field_name]

            field_values[field_name] = field_value

        ConfigLoader._logger.debug(f"Field values for {data_class}:  {field_values}")
        return data_class(**field_values)

if __name__ == "__main__":
    from dataclasses import dataclass
    from pathlib import Path
    from typing import List

    @dataclass
    class User:
        name: str
        age: int
        friends: list["User"]

    @dataclass
    class Config:
        myself: User

    config_loader = ConfigLoader(Config)
    config_loader._logger.setLevel(logging.DEBUG)
    config = config_loader.load_config(Path("/Users/benno/coding/YAML2Dataclass/example/config2.yaml"))
    print(config)
