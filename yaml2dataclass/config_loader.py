import os

from dataclasses import fields
from pathlib import Path
from typing import Any, Optional
from ruamel.yaml import YAML


class ConfigLoader:
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[Any] = None

    def __new__(cls, *args, **kwargs) -> 'ConfigLoader':
        """Ensures only one instance of ConfigLoader exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_class: Optional[Any] = None):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config_class = config_class

    def load_config(self, file_path: Path) -> Any:
        """
        Loads configuration from a YAML file.
        If config is already loaded, returns cached version.
        """
        if self._config is None:
            with file_path.open("r") as file:
                yaml_data = YAML().load(file)
                self._config = self._from_dict(data_class=self._config_class, data=yaml_data)

        if self._config is None:
            raise RuntimeError("Failed to load configuration.")
        return self._config

    def get_config(self) -> Any:
        """
        Returns the loaded configuration.
        Raises an exception if config hasn't been loaded yet.
        """
        if self._config is None:
            raise RuntimeError("Configuration hasn't been loaded yet. Call load_config first.")
        return self._config

    @staticmethod
    def _from_dict(data_class, data: dict) -> Any:
        """
        Converts a dictionary to an instance of a data class.
        Supports nested data classes.
        """
        fieldtypes = {field.name: field.type for field in fields(data_class)}
        field_values = {}

        for field_name, field_type in fieldtypes.items():
            if field_name in data:
                field_value = data[field_name]

                if hasattr(field_type, "__dataclass_fields__"):
                    field_value = ConfigLoader._from_dict(field_type, field_value)

                if not isinstance(field_type, str) and isinstance(field_value, str):
                    field_value = field_type(field_value)
                else:
                    field_value = field_value

                field_values[field_name] = field_value
            else:
                raise ValueError(f"Missing required field: {field_name}")

        return data_class(**field_values)

    def reset_config(self):
        """
        Resets the loaded configuration.
        Useful for testing or reloading config.
        """
        self._config = None

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config = config_loader.load_config(Path("config.yaml"))
    print(config)
