import re
from dataclasses import dataclass
from typing import Any


# -------------------------
# AST Nodes
# -------------------------
@dataclass
class Node:
    """Base class for AST nodes."""

    pass


@dataclass
class TextNode(Node):
    content: str


@dataclass
class VariableNode(Node):
    name: str


@dataclass
class IfNode(Node):
    condition: str
    true_block: list[Node]
    false_block: list[Node] | None = None


@dataclass
class ForNode(Node):
    iterator: str
    iterable: str
    block: list[Node]


@dataclass
class IncludeNode(Node):
    template_name: str


@dataclass
class MetadataNode(Node):
    key: str
    value: str


# -------------------------
# Parser
# -------------------------
class Parser:
    def __init__(self):
        self.metadata: dict[str, str] = {}
        self.tokens: list[tuple[str, Any]] = []
        self.pos: int = 0

        self.patterns: list[tuple[str, re.Pattern]] = [
            ("METADATA", re.compile(r"@(\w+):\s*(.+?)(?:\n|$)")),
            ("COMMENT", re.compile(r"\{#.*?#\}(?:\n)?")),
            ("IF_START", re.compile(r"\{%\s*if\s+(\w+)\s*%\}(?:\n)?")),
            ("ELSE", re.compile(r"\{%\s*else\s*%\}(?:\n)?")),
            ("ENDIF", re.compile(r"\{%\s*endif\s*%\}(?:\n)?")),
            ("FOR_START", re.compile(r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(?:\n)?")),
            ("ENDFOR", re.compile(r"\{%\s*endfor\s*%\}(?:\n)?")),
            ("INCLUDE", re.compile(r'\{%\s*include\s+"([^"]+)"\s*%\}(?:\n)?')),
            ("VARIABLE", re.compile(r"\{\{([\w\.]+)\}\}")),  # supports dotted names
        ]

    def parse(self, template: str) -> tuple[dict[str, str], list[Node]]:
        """Parse a PromptML template into metadata and an AST.

        Args:
            template (str): The template source string to parse.

        Returns:
            tuple[dict[str, str], list[Node]]: A tuple containing:
                - metadata: a dict mapping metadata keys to their string values.
                - nodes: a list of top-level AST Node instances representing
                  the parsed template.
        """
        self.metadata = {}
        self.tokens = self._tokenize(template)
        self.pos = 0
        nodes = self._parse_nodes()
        return self.metadata, nodes

    def _tokenize(self, template: str) -> list[tuple[str, Any]]:
        tokens = []
        pos = 0
        length = len(template)

        while pos < length:
            match_found = False

            for token_type, pattern in self.patterns:
                match = pattern.match(template, pos)
                if match:
                    if token_type == "METADATA":
                        self.metadata[match.group(1)] = match.group(2).strip()
                    elif token_type == "COMMENT":
                        pass  # skip comments
                    else:
                        tokens.append((token_type, match.groups()))
                    pos = match.end()
                    match_found = True
                    break

            if not match_found:
                # Collect text until next token
                next_positions = [
                    m.start() for _, p in self.patterns for m in p.finditer(template, pos)
                ]
                next_pos = min(next_positions, default=length)
                text = template[pos:next_pos]
                if text:
                    tokens.append(("TEXT", text))
                pos = next_pos

        return tokens

    # -------------------------
    # Parsing AST Nodes
    # -------------------------
    def _parse_nodes(self, stop_tokens: set | None = None) -> list[Node]:
        nodes: list[Node] = []
        stop_tokens = stop_tokens or set()

        while self.pos < len(self.tokens):
            token_type, data = self.tokens[self.pos]

            if token_type in stop_tokens:
                break

            if token_type == "TEXT":
                # Coalesce consecutive TextNodes
                if nodes and isinstance(nodes[-1], TextNode):
                    nodes[-1].content += data
                else:
                    nodes.append(TextNode(data))
                self.pos += 1

            elif token_type == "VARIABLE":
                nodes.append(VariableNode(data[0]))
                self.pos += 1

            elif token_type == "IF_START":
                self.pos += 1
                condition = data[0]
                true_block = self._parse_nodes({"ELSE", "ENDIF"})

                false_block = None
                if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "ELSE":
                    self.pos += 1
                    false_block = self._parse_nodes({"ENDIF"})

                if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "ENDIF":
                    self.pos += 1

                nodes.append(IfNode(condition, true_block, false_block))

            elif token_type == "FOR_START":
                self.pos += 1
                iterator, iterable = data
                block = self._parse_nodes({"ENDFOR"})

                if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "ENDFOR":
                    self.pos += 1

                nodes.append(ForNode(iterator, iterable, block))

            elif token_type == "INCLUDE":
                nodes.append(IncludeNode(data[0]))
                self.pos += 1

            else:
                # unknown token → skip
                self.pos += 1

        return nodes
