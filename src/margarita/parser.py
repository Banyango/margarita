import re
from dataclasses import dataclass, field


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
    params: dict[str, str] = field(default_factory=dict)


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
        self.lines: list[tuple[int, str]] = []  # (indent_level, line_content)
        self.pos: int = 0

    def parse(self, template: str) -> tuple[dict[str, str], list[Node]]:
        """Parse a Margarita template into metadata and an AST.

        Args:
            template (str): The template source string to parse.

        Returns:
            tuple[dict[str, str], list[Node]]: A tuple containing:
                - metadata: a dict mapping metadata keys to their string values.
                - nodes: a list of top-level AST Node instances representing
                  the parsed template.
        """
        self.metadata = {}
        self._preprocess(template)
        self.pos = 0
        nodes = self._parse_block(base_indent=-1)
        return self.metadata, nodes

    def _preprocess(self, template: str) -> None:
        """Preprocess the template to extract metadata and prepare lines."""
        lines = template.split('\n')
        self.lines = []

        # Check for metadata block at the beginning (enclosed by ---)
        # Metadata is optional - only parse if template starts with ---
        i = 0

        # Skip leading empty lines to check if template starts with metadata
        while i < len(lines) and not lines[i].strip():
            i += 1

        # Check if we have metadata block
        if i < len(lines) and lines[i].strip() == '---':
            # Found metadata block
            i += 1  # Skip opening ---

            # Parse metadata lines until we find closing ---
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                # Check for closing delimiter
                if stripped == '---':
                    i += 1  # Skip closing ---
                    break

                # Parse metadata line
                metadata_match = re.match(r'^(\w+):\s*(.+)$', stripped)
                if metadata_match:
                    self.metadata[metadata_match.group(1)] = metadata_match.group(2).strip()
                i += 1
        else:
            # No metadata block, reset to start
            i = 0

        # Process remaining lines after metadata (or all lines if no metadata)
        for j in range(i, len(lines)):
            line = lines[j]

            # Check for comments (skip them)
            if line.strip().startswith('//'):
                continue

            # Calculate indentation level (number of leading spaces / 4)
            indent = len(line) - len(line.lstrip())
            self.lines.append((indent, line))

    def _parse_block(self, base_indent: int) -> list[Node]:
        """Parse a block of nodes at a given indentation level."""
        nodes: list[Node] = []

        while self.pos < len(self.lines):
            indent, line = self.lines[self.pos]
            stripped = line.strip()

            # If we've dedented past the base level, stop
            if stripped and indent <= base_indent:
                break

            # Skip empty lines
            if not stripped:
                self.pos += 1
                continue

            # Check for control structures
            if_match = re.match(r'^if\s+(\w+):$', stripped)
            for_match = re.match(r'^for\s+(\w+)\s+in\s+(\w+):$', stripped)
            else_match = re.match(r'^else:$', stripped)
            include_match = re.match(r'^\[\[\s*([^]]+)\s*]]$', stripped)
            text_block_start = stripped.startswith('<<')

            if if_match:
                # Parse if statement
                condition = if_match.group(1)
                self.pos += 1
                # Parse the true block - content should be more indented than the if statement
                true_block = self._parse_block(indent)

                # Check for else at the same indent level as the if
                false_block = None
                if self.pos < len(self.lines):
                    next_indent, next_line = self.lines[self.pos]
                    if next_indent == indent and next_line.strip() == 'else:':
                        self.pos += 1
                        # Parse the false block - content should be more indented than the else
                        false_block = self._parse_block(indent)

                nodes.append(IfNode(condition, true_block, false_block))

            elif for_match:
                # Parse for loop
                iterator = for_match.group(1)
                iterable = for_match.group(2)
                self.pos += 1
                # Parse the loop block - content should be more indented than the for statement
                block = self._parse_block(indent)
                nodes.append(ForNode(iterator, iterable, block))

            elif else_match:
                # We've hit an else at this level, return to let parent handle it
                break

            elif include_match:
                # Parse include with optional parameters
                include_content = include_match.group(1).strip()
                # Parse [[filename param1="value1" param2="value2"]]
                parts = include_content.split(None, 1)
                template_name = parts[0]
                params = {}

                if len(parts) > 1:
                    # Parse parameters
                    param_str = parts[1]
                    param_matches = re.finditer(r"(\w+)=(?:\"([^\"]*)\"|([^\"\s]+))", param_str)
                    params = {}
                    for m in param_matches:
                        key = m.group(1)
                        value = m.group(2) if m.group(2) is not None else m.group(3)
                        params[key] = value

                nodes.append(IncludeNode(template_name, params))
                self.pos += 1

            elif text_block_start:
                # Parse text block
                text_content = self._parse_text_block()
                if text_content:
                    nodes.append(TextNode(text_content))

            else:
                # Unknown line - skip
                self.pos += 1

        return nodes

    def _parse_text_block(self) -> str:
        """Parse a text block delimited by << and >>."""
        indent, first_line = self.lines[self.pos]

        # Check if it's a single-line text block
        if first_line.strip().startswith('<<') and first_line.strip().endswith('>>'):
            # Single line block
            content = first_line.strip()[2:-2].strip()
            self.pos += 1
            # Process variables in the content
            processed = self._process_text_variables(content)
            # Add newline after text block
            return processed + '\n' if processed else processed

        # Multi-line block
        if not first_line.strip().startswith('<<'):
            return ""

        # The block's base indentation is the indentation of the << line
        block_indent = indent

        # Check if there's content after << on the first line
        first_line_content = first_line.strip()[2:].strip()  # Remove << and strip

        self.pos += 1  # Move past the << line
        content_lines = []

        # If there was content after <<, add it as the first line
        if first_line_content:
            content_lines.append(first_line_content)

        while self.pos < len(self.lines):
            line_indent, line = self.lines[self.pos]
            stripped = line.strip()

            if stripped == '>>':
                self.pos += 1  # Skip the >> line
                break

            # Remove the block's base indentation from each line
            # Empty lines are kept as-is
            if line:  # Non-empty line
                if line_indent >= block_indent:
                    # Remove the base indentation
                    dedented_line = line[block_indent:]
                else:
                    # Line is less indented than the block - keep as-is
                    dedented_line = line
            else:
                # Empty line
                dedented_line = ''

            content_lines.append(dedented_line)
            self.pos += 1

        content = '\n'.join(content_lines)
        # Process variables in the content
        processed = self._process_text_variables(content)
        # Always add a trailing newline to text blocks to ensure proper spacing
        # Special case: if content_lines has content (even if empty strings), add newline
        if processed or content_lines:
            processed += '\n'
        return processed

    def _process_text_variables(self, text: str) -> str:
        """Convert ${var} syntax to internal representation."""
        # For now, we'll convert ${var} to {{var}} internally for compatibility
        # But we need to track these as VariableNodes within TextNodes

        # Actually, we need to split the text into TextNode and VariableNode pieces
        # For simplicity in this iteration, we'll leave the text as-is and handle
        # variable substitution in a separate pass or in the renderer

        # Let's use a placeholder approach: we'll keep ${var} as is in TextNode
        # and the renderer will handle the substitution
        return text




