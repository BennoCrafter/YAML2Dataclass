import ruamel.yaml
import json
from typing import Dict, List, Union, Optional, Tuple, Generator
from pathlib import Path

class YAMLReader:
    def __init__(self, yaml_file: str | Path) -> None:
        self.yaml_file = yaml_file
        self.data = None
        self.yaml = ruamel.yaml.YAML()

    def load_yaml(self) -> Dict:
        """Loads the YAML file into memory."""
        with open(self.yaml_file, 'r', encoding='utf-8') as f:
            self.data = self.yaml.load(f)

        return self.extract_comments()

    def extract_comments(self) -> Dict:
        """Starts recursive extraction of comments."""
        if self.data is None:
            raise ValueError("YAML data not loaded. Call load_yaml() first.")
        return self._process_node(self.data) # type: ignore

    def _process_node(self, node: Union[ruamel.yaml.comments.CommentedMap, # type: ignore
                                      ruamel.yaml.comments.CommentedSeq, # type: ignore
                                      str, int, float, bool]) -> Union[Dict, List, str, int, float, bool]:
        """Recursively processes YAML nodes to extract values and comments."""
        if isinstance(node, ruamel.yaml.comments.CommentedMap):  # type: ignore
            return self._process_commented_map(node)
        elif isinstance(node, ruamel.yaml.comments.CommentedSeq): # type: ignore
            return self._process_commented_seq(node)
        else:
            return node  # Scalar value

    def _process_commented_map(self, node: ruamel.yaml.comments.CommentedMap) -> Dict: # type: ignore
        """Processes a CommentedMap node."""
        result = {}
        for key, value in node.items():
            comment = self._extract_key_comment(node, key)
            result[key] = {
                "value": self._process_node(value),
                "comment": comment
            }
        return result

    def _process_commented_seq(self, node: ruamel.yaml.comments.CommentedSeq) -> List:  # type: ignore
        """Processes a CommentedSeq node."""
        return [self._process_node(item) for item in node]

    def _extract_key_comment(self, node: ruamel.yaml.comments.CommentedMap, key: str) -> Optional[str]:  # type: ignore
        """Extracts comments for a given key in a CommentedMap."""
        if key in node.ca.items:  # type: ignore
            return " ".join(
                token.value.strip()
                for _, token in self._extract_from_token(node.ca.items[key])  # type: ignore
            )
        return None

    @staticmethod
    def _extract_from_token(token_list: List) -> Generator[Tuple[int, ruamel.yaml.tokens.CommentToken], None, None]:  # type: ignore
        """Extracts line and comment text from tokens."""
        assert isinstance(token_list, list)
        for token in token_list:
            if token is None:
                continue
            if isinstance(token, list):
                for sub_token in token:
                    yield sub_token.start_mark.line, sub_token
            else:
                yield token.start_mark.line, token


# Example usage
if __name__ == "__main__":
    yaml_file = 'config.yaml'  # Replace with your YAML file path
    extractor = YAMLReader(yaml_file)

    data = extractor.load_yaml()
    print(data)
    print(json.dumps(data, indent=4))
