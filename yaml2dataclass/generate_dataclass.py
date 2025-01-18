from pathlib import Path
from dataclasses import dataclass
from typing import Any, Union, Optional
from yaml2dataclass.yaml_reader import YAMLReader
import re



@dataclass
class TypeAnnotation:
    # example: "dict[str, Any]" or "list[str]"
    generic_type: str
    type_params: Optional[list[str]]

    @classmethod
    def from_comment(cls, comment: Optional[str]) -> 'TypeAnnotation':
        if not comment:
            return cls("", None)

        paramterized_type = comment.strip('# ').strip()

        pattern = r"(\w+)\[([^\]]+)\]|\b(\w+)\b"

        # Find matches
        matches = re.findall(pattern, paramterized_type)

        parsed_result = []

        for match in matches:
            # If there's a match for a type with parameters (e.g., list[str])
            if match[0] and match[1]:
                generic_type = match[0]
                type_params = [param.strip() for param in match[1].split(',')]
                return cls(generic_type, type_params)
            # If it's a simple type (e.g., str)
            elif match[2]:
                generic_type = match[2]
                return cls(generic_type, None)

        raise Exception(f"Failed to parse type annotation: {paramterized_type}")

    @classmethod
    def from_value(cls, value: Any) -> 'TypeAnnotation':
        return cls(type(value).__name__, None)

    def to_paramterized_type(self) -> str:
        if self.type_params:
            return f"{self.generic_type}[{', '.join(self.type_params)}]"
        return self.generic_type



@dataclass
class Name:
    name: str

    def to_pascal_case(self) -> str:
        components = self.name.split('_')
        return ''.join(x.title() for x in components)

    def to_snake_case(self) -> str:
        return self.name


class MetaDataclass:
    def __init__(self, name: Name) -> None:
        self.imports: list[str] = [
            "from dataclasses import dataclass",
            "from typing import Optional, List, Any, Union"
        ]
        self.parameters: list[str] = []
        self.name = name
        self.docstring: Optional[str] = None

    def add_import(self, path: Path, name: Name):
        p = path.as_posix().replace("/", ".")
        p += "." + name.to_snake_case()
        self.imports.append(f"from {p} import {name.to_pascal_case()}")

    def add_parameter(self, key: str, type_annotation: TypeAnnotation, description: Optional[str] = None):
        param = f"{key}: {type_annotation.to_paramterized_type()}"
        if description:
            param += f"  # {description}"
        self.parameters.append(param)

    def build(self) -> str:
        imports = "\n".join(sorted(set(self.imports)))
        parameters = "\n    ".join(self.parameters)
        class_def = f"@dataclass\nclass {self.name.to_pascal_case()}:"

        if self.docstring:
            class_def += f'\n    """{self.docstring}"""'

        class_def += f"\n    {parameters}"

        return f"{imports}\n\n{class_def}"

    def __str__(self) -> str:
        return f"{self.imports}\n\n{self.parameters}"


def read_yaml(path: Path) -> dict:
    r = YAMLReader(path)
    return r.load_yaml()


def write_to_file(path: Path, metacl: MetaDataclass):
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, "w") as f:
        f.write(metacl.build())


def parse_field_metadata(value: Any) -> tuple[Any, Optional[str], Optional[str]]:
    if isinstance(value, dict) and 'value' in value:
        return (
            value.get('value'),
            value.get('comment'),
            value.get('description')
        )
    return value, None, None


def generate_dataclass(base_name: Name, data: dict, meta_dataclasses: list, dest_path: Path) -> MetaDataclass:
    md = MetaDataclass(base_name)

    for key, raw_value in data.items():
        value, type_comment, description = parse_field_metadata(raw_value)
        name = Name(key)

        if isinstance(value, dict):
            m = generate_dataclass(name, value, meta_dataclasses, dest_path)
            meta_dataclasses.append(m)
            md.add_import(dest_path, name)
            type_annotation = TypeAnnotation.from_comment(type_comment) if type_comment else TypeAnnotation(name.to_pascal_case(), None)
            md.add_parameter(name.to_snake_case(), type_annotation, description)

        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                m = generate_dataclass(name, value[0], meta_dataclasses, dest_path)
                meta_dataclasses.append(m)

                if type_comment:
                    type_annotation = TypeAnnotation.from_comment(type_comment)
                    if type_annotation.type_params is not None and type_annotation.generic_type == "list":
                        m.name = Name(type_annotation.type_params[0].lower())
                else:
                    type_annotation = TypeAnnotation("list", [name.to_pascal_case()])

                md.add_import(dest_path, m.name)
                md.add_parameter(name.to_snake_case(), type_annotation, description)
            else:
                item_type = type(value[0]).__name__ if value else "Any"
                type_annotation = TypeAnnotation.from_comment(type_comment) if type_comment else TypeAnnotation("list", [item_type])
                md.add_parameter(name.to_snake_case(), type_annotation, description)
        else:
            type_annotation = TypeAnnotation.from_comment(type_comment) if type_comment else TypeAnnotation.from_value(value)
            md.add_parameter(name.to_snake_case(), type_annotation, description)

    return md


def generate_dataclasses(dest_path: Path, data: dict):
    meta_dataclasses: list[MetaDataclass] = []
    meta_dataclasses.append(generate_dataclass(Name("config"), data, meta_dataclasses, dest_path))

    for m in meta_dataclasses:
        p = dest_path / (m.name.to_snake_case() + '.py')
        write_to_file(p, m)


if __name__ == '__main__':
    # Uncomment below to test with actual data
    generate_dataclasses(Path('src/config'), read_yaml(Path('config.yaml')))
