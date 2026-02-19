"""Renderer for Margarita templates.

This module provides functionality to render parsed AST nodes into strings
by applying variable substitution and control flow logic.
"""

import re
from pathlib import Path
from typing import Any

from margarita.parser import (
    ForNode,
    IfNode,
    IncludeNode,
    Node,
    Parser,
    TextNode,
    VariableNode,
)


class Renderer:
    def __init__(self, context: dict[str, Any] | None = None, base_path: Path | None = None):
        """Initialize the renderer with a context dictionary.

        Args:
            context: Dictionary containing variable values for rendering
            base_path: Base directory path for resolving include statements
        """
        self.context = context or {}
        self.base_path = base_path or Path.cwd()

    def render(self, nodes: list[Node]) -> str:
        """Render a list of AST nodes into a string.

        Args:
            nodes: List of parsed AST nodes to render

        Returns:
            Rendered string output
        """
        output = []
        for node in nodes:
            output.append(self._render_node(node))
        return "".join(output)

    def _render_node(self, node: Node) -> str:
        """Render a single AST node.

        Args:
            node: The AST node to render

        Returns:
            Rendered string for this node
        """
        if isinstance(node, TextNode):
            content = node.content

            def replace_var(match):
                var_name = match.group(1)
                _val = self._get_variable_value(var_name)
                return str(_val) if _val is not None else ""

            content = re.sub(r"\$\{([\w\.]+)\}", replace_var, content)
            return content

        elif isinstance(node, VariableNode):
            # Support dotted notation like "user.name"
            value = self._get_variable_value(node.name)
            return str(value) if value is not None else ""

        elif isinstance(node, IfNode):
            # Evaluate the condition expression
            condition_result = self._evaluate_condition(node.condition)
            if condition_result:
                return self.render(node.true_block)
            elif node.false_block:
                return self.render(node.false_block)
            return ""

        elif isinstance(node, ForNode):
            iterable = self._get_variable_value(node.iterable)
            if not iterable:
                return ""

            output = []
            for item in iterable:
                old_value = self.context.get(node.iterator)

                self.context[node.iterator] = item
                output.append(self.render(node.block))

                if old_value is not None:
                    self.context[node.iterator] = old_value
                else:
                    self.context.pop(node.iterator, None)

            return "".join(output)

        elif isinstance(node, IncludeNode):
            template_name = node.template_name
            if not template_name.endswith(".mg"):
                template_name += ".mg"

            include_path = self.base_path / template_name

            try:
                template_content = include_path.read_text()

                parser = Parser()
                _, included_nodes = parser.parse(template_content)

                # Create a new context with include parameters merged in
                include_context = self.context.copy()
                include_context.update(node.params)

                included_renderer = Renderer(context=include_context, base_path=self.base_path)
                return included_renderer.render(included_nodes)

            except FileNotFoundError:
                print(f"Included template not found: {include_path}")
                return ""
            except Exception:
                return ""
        else:
            return ""

    def _get_variable_value(self, name: str) -> Any:
        """Get a variable value from context, supporting dotted notation.

        Args:
            name: Variable name, possibly with dots like "user.name"

        Returns:
            The variable value or None if not found
        """
        parts = name.split(".")
        value = self.context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def _evaluate_condition(self, condition: str) -> bool | None:
        """Evaluate a condition expression.

        Args:
            condition: The condition string to evaluate (e.g., "var", "var == 'test'", "x > 5")

        Returns:
            True if the condition is true, False otherwise
        """
        condition = condition.strip()

        comparison_pattern = r'^(.+?)\s*(==|!=|>=|<=|>|<)\s*(.+)$'
        match = re.match(comparison_pattern, condition)

        if match:
            left_expr = match.group(1).strip()
            operator = match.group(2)
            right_expr = match.group(3).strip()

            left_value = self._evaluate_expression(left_expr)
            right_value = self._evaluate_expression(right_expr)

            result = {
                "==": left_value == right_value,
                "!=": left_value != right_value,
                ">": left_value > right_value,
                "<": left_value < right_value,
                ">=": left_value >= right_value,
                "<=": left_value <= right_value,
            }

            if operator in result:
                return result[operator]
            else:
                return None

        # No comparison operator, just evaluate as a simple expression
        value = self._evaluate_expression(condition)
        return self._is_truthy(value)

    def _evaluate_expression(self, expr: str) -> Any:
        """Evaluate an expression (variable or literal).

        Args:
            expr: The expression to evaluate

        Returns:
            The evaluated value
        """
        expr = expr.strip()

        # Check if it's a string literal (quoted)
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]  # Remove quotes

        # Check if it's a number
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass

        # Check if it's a boolean
        if expr.lower() == 'true':
            return True
        elif expr.lower() == 'false':
            return False
        elif expr.lower() == 'none':
            return None

        # Otherwise, treat it as a variable name
        return self._get_variable_value(expr)

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        """Determine if a value is truthy for conditional evaluation.

        Args:
            value: The value to check

        Returns:
            True if the value is truthy, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (list, dict, str)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value != 0
        return True
