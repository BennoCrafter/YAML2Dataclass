from pathlib import Path
from dataclasses import dataclass
from typing import Any, Union, Optional, List, Dict
from yaml2dataclass.yaml_reader import YAMLReader
import re
from abc import ABC, abstractmethod


class TypeParserInterface(ABC):
    @abstractmethod
    def parse(self, value: Any) -> 'TypeAnnotation':
        pass


class CommentTypeParser(TypeParserInterface):
    def parse(self, value: Optional[str]) -> 'TypeAnnotation':
        if not value:
            return TypeAnnotation("", None)

        paramterized_type = value.strip('# ').strip()
        pattern = r"(\w+)\[([^\]]+)\]|\b(\w+)\b"
        matches = re.findall(pattern, paramterized_type)

        for match in matches:
            if match[0] and match[1]:
                generic_type = match[0]
                type_params = [param.strip() for param in match[1].split(',')]
                return TypeAnnotation(generic_type, type_params)
            elif match[2]:
                return TypeAnnotation(match[2], None)

        raise ValueError(f"Failed to parse type annotation: {paramterized_type}")


class ValueTypeParser(TypeParserInterface):
    def parse(self, value: Any) -> 'TypeAnnotation':
        return TypeAnnotation(type(value).__name__, None)


@dataclass
class TypeAnnotation:
    generic_type: str
    type_params: Optional[List[str]]

    def to_paramterized_type(self) -> str:
        if self.type_params:
            return f"{self.generic_type}[{', '.join(self.type_params)}]"
        return self.generic_type


@dataclass
class Name:
    name: str

    def to_pascal_case(self) -> str:
        return ''.join(x.title() for x in self.name.split('_'))

    def to_snake_case(self) -> str:
        return self.name


class DataclassBuilder:
    def __init__(self, name: Name):
        self.name = name
        self.imports: set[str] = {"from dataclasses import dataclass", "from typing import Optional, Any"}
        self.parameters: List[str] = []
        self.docstring: Optional[str] = None

    def add_import(self, path: Path, name: Name) -> None:
        module_path = f"{path.as_posix().replace('/', '.')}.{name.to_snake_case()}"
        self.imports.add(f"from {module_path} import {name.to_pascal_case()}")

    def add_parameter(self, key: str, type_annotation: TypeAnnotation, description: Optional[str] = None) -> None:
        param = f"{key}: {type_annotation.to_paramterized_type()}"
        if description:
            param += f"  # {description}"
        self.parameters.append(param)

    def build(self) -> str:
        parts = [
            self._build_imports(),
            self._build_class_definition()
        ]
        return "\n\n".join(parts)

    def _build_imports(self) -> str:
        return "\n".join(sorted(self.imports))

    def _build_class_definition(self) -> str:
        class_def = [
            "@dataclass",
            f"class {self.name.to_pascal_case()}:"
        ]

        if self.docstring:
            class_def.append(f'    """{self.docstring}"""')

        if self.parameters:
            class_def.append(f"    {self._format_parameters()}")

        return "\n".join(class_def)

    def _format_parameters(self) -> str:
        return "\n    ".join(self.parameters)


class ValueHandler(ABC):
    def __init__(self, generator: 'DataclassGenerator') -> None:
        self.generator = generator

    @abstractmethod
    def handle(self, value: Any, name: Name, type_comment: Optional[str], description: Optional[str], builder: DataclassBuilder) -> None:
        pass


class DictValueHandler(ValueHandler):
    def handle(self, value: Any, name: Name, type_comment: Optional[str], description: Optional[str], builder: DataclassBuilder) -> None:
        nested_builder = self.generator._generate_dataclass(name, value)
        self.generator.builders.append(nested_builder)
        builder.add_import(self.generator.dest_path, name)
        type_annotation = TypeAnnotation(name.to_pascal_case(), None)
        builder.add_parameter(name.to_snake_case(), type_annotation, description)


class ListValueHandler(ValueHandler):
    def handle(self, value: Any, name: Name, type_comment: Optional[str], description: Optional[str], builder: DataclassBuilder) -> None:
        item_type = self._resolve_item_type(value, name, type_comment, builder)
        type_annotation = TypeAnnotation("list", [item_type])
        builder.add_parameter(name.to_snake_case(), type_annotation, description)

    def _resolve_item_type(self, value: List, name: Name, type_comment: Optional[str], builder: DataclassBuilder) -> str:
        if value and isinstance(value[0], dict):
            nested_name = Name(name.name[:-1])  # Singularize the name
            nested_builder = self.generator._generate_dataclass(nested_name, value[0])
            builder.add_import(self.generator.dest_path, nested_name)
            self.generator.builders.append(nested_builder)
            return nested_name.to_pascal_case()

        return type(value[0]).__name__ if value else "Any"


class DataclassGenerator:
    def __init__(self, dest_path: Path):
        self.dest_path = dest_path
        self.comment_parser = CommentTypeParser()
        self.value_parser = ValueTypeParser()
        self.builders: List[DataclassBuilder] = []
        self.handlers = {
            dict: DictValueHandler(self),
            list: ListValueHandler(self)
        }

    def generate(self, yaml_path: Path) -> None:
        data = self._read_yaml(yaml_path)
        self.builders.append(self._generate_dataclass(Name("config"), data))

        for builder in self.builders:
            output_path = self.dest_path / f"{builder.name.to_snake_case()}.py"
            self._write_to_file(output_path, builder.build())

    def _read_yaml(self, path: Path) -> Dict:
        return YAMLReader(path).load_yaml()

    def _write_to_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "w") as f:
            f.write(content)

    def _generate_dataclass(self, base_name: Name, data: dict) -> DataclassBuilder:
        builder = DataclassBuilder(base_name)

        for key, raw_value in data.items():
            value, type_comment, description = self._parse_field_metadata(raw_value)
            name = Name(key)

            handler = self.handlers.get(type(value))
            if handler:
                handler.handle(value, name, type_comment, description, builder)
            else:
                type_annotation = self.comment_parser.parse(type_comment) if type_comment else self.value_parser.parse(value)
                builder.add_parameter(name.to_snake_case(), type_annotation, description)

        return builder

    def _parse_field_metadata(self, value: Any) -> tuple[Any, Optional[str], Optional[str]]:
        if isinstance(value, dict) and 'value' in value:
            return value['value'], value.get('comment'), value.get('description')
        return value, None, None


if __name__ == '__main__':
    generator = DataclassGenerator(Path('src/config'))
    generator.generate(Path('config.yaml'))
