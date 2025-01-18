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
            # If it's a simple type (e.g., str)
            elif match[2]:
                generic_type = match[2]
                return TypeAnnotation(generic_type, None)

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
        self.imports: set[str] = {
            "from dataclasses import dataclass",
            "from typing import Optional, List, Any, Union"
        }
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
        imports = "\n".join(sorted(self.imports))
        parameters = "\n    ".join(self.parameters)
        class_def = [
            "@dataclass",
            f"class {self.name.to_pascal_case()}:"
        ]

        if self.docstring:
            class_def.append(f'    """{self.docstring}"""')

        class_def.append(f"    {parameters}")
        return f"{imports}\n\n{'\n'.join(class_def)}"


class DataclassGenerator:
    def __init__(self, dest_path: Path):
        self.dest_path = dest_path
        self.comment_parser = CommentTypeParser()
        self.value_parser = ValueTypeParser()

    def generate(self, yaml_path: Path) -> None:
        data = self._read_yaml(yaml_path)
        meta_dataclasses: List[DataclassBuilder] = []
        meta_dataclasses.append(self._generate_dataclass(Name("config"), data, meta_dataclasses))

        for builder in meta_dataclasses:
            output_path = self.dest_path / f"{builder.name.to_snake_case()}.py"
            self._write_to_file(output_path, builder)

    def _read_yaml(self, path: Path) -> Dict:
        return YAMLReader(path).load_yaml()

    def _write_to_file(self, path: Path, builder: DataclassBuilder) -> None:
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "w") as f:
            f.write(builder.build())

    def _parse_field_metadata(self, value: Any) -> tuple[Any, Optional[str], Optional[str]]:
        if isinstance(value, dict) and 'value' in value:
            return value.get('value'), value.get('comment'), value.get('description')
        return value, None, None

    def _handle_dict_value(self, value, name, type_comment, description, builder, builders):
        nested_builder = self._generate_dataclass(name, value, builders)
        builders.append(nested_builder)
        builder.add_import(self.dest_path, name)
        type_annotation = (self.comment_parser.parse(type_comment) if type_comment
                         else TypeAnnotation(name.to_pascal_case(), None))
        builder.add_parameter(name.to_snake_case(), type_annotation, description)

    def _handle_list_value(self, value, name, type_comment, description, builder, builders):
        if value and isinstance(value[0], dict):
            nested_builder = self._generate_dataclass(name, value[0], builders)
            builders.append(nested_builder)

            type_annotation = self.comment_parser.parse(type_comment) if type_comment else TypeAnnotation("list", [name.to_pascal_case()])
            if type_comment and type_annotation.type_params and type_annotation.generic_type == "list":
                nested_builder.name = Name(type_annotation.type_params[0].lower())

            builder.add_import(self.dest_path, nested_builder.name)
            builder.add_parameter(name.to_snake_case(), type_annotation, description)
        else:
            item_type = type(value[0]).__name__ if value else "Any"
            type_annotation = (self.comment_parser.parse(type_comment) if type_comment
                             else TypeAnnotation("list", [item_type]))
            builder.add_parameter(name.to_snake_case(), type_annotation, description)

    def _generate_dataclass(self, base_name: Name, data: dict, builders: List[DataclassBuilder]) -> DataclassBuilder:
        builder = DataclassBuilder(base_name)

        handlers = {
            dict: self._handle_dict_value,
            list: self._handle_list_value
        }

        for key, raw_value in data.items():
            value, type_comment, description = self._parse_field_metadata(raw_value)
            name = Name(key)

            handler = handlers.get(type(value))
            if handler:
                handler(value, name, type_comment, description, builder, builders)
            else:
                type_annotation = (self.comment_parser.parse(type_comment) if type_comment
                                 else self.value_parser.parse(value))
                builder.add_parameter(name.to_snake_case(), type_annotation, description)

        return builder


if __name__ == '__main__':
    generator = DataclassGenerator(Path('src/config'))
    generator.generate(Path('config.yaml'))
