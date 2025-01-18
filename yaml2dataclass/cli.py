import argparse
from pathlib import Path
from yaml2dataclass.generate_dataclass import generate_dataclasses
from yaml2dataclass.yaml_reader import YAMLReader


def main():
    parser = argparse.ArgumentParser(description="Convert yaml to dataclass")
    parser.add_argument("yaml_file", type=Path, help="yaml file to convert")
    parser.add_argument("output_path", type=Path, help="output path to write dataclasses")
    args = parser.parse_args()

    data = YAMLReader(args.yaml_file).load_yaml()

    generate_dataclasses(args.output_path, data)


if __name__ == "__main__":
    main()
