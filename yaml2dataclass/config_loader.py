from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Optional, Type, TypeVar, Union
from ruamel.yaml import YAML

T = TypeVar("T")


class ConfigLoader:
    _instance: Optional["ConfigLoader"] = None
    _config: Optional[Any] = None

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
            if field_name in data:
                value = data[field_name]

                if is_dataclass(field_type):
                    value = ConfigLoader._from_dict(field_type, value) # type: ignore
                elif (
                    hasattr(field_type, "__origin__")
                    and field_type.__origin__ == list # type: ignore
                    and is_dataclass(field_type.__args__[0]) # type: ignore
                ):
                    # Handle list of dataclasses
                    value = [ConfigLoader._from_dict(field_type.__args__[0], v) for v in value] # type: ignore

                field_values[field_name] = value
            else:
                raise ValueError(f"Missing required field: {field_name}")

        return data_class(**field_values)
