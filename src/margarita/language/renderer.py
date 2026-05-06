"""Renderer for Margarita templates.

This module provides functionality to render parsed AST nodes into strings
by applying variable substitution and control flow logic.
"""

import ast
import re
from pathlib import Path
from typing import Any

from margarita.language.parser import (
    AllAwaitNode,
    BreakNode,
    ForNode,
    IfNode,
    IncludeNode,
    Node,
    Parser,
    TextNode,
    VariableNode,
    WhileNode,
)

EQUALITY_OR_LOGICAL_OPERATORS = (
    "==",
    "!=",
    ">=",
    "<=",
    ">",
    "<",
    " in ",
    " not in ",
    " and ",
    " or ",
    "not ",
)


class _BreakSignal(Exception):
    """Internal signal raised when a BreakNode is encountered inside a for loop."""

    pass


# Mapping of ast comparison/bool operator types to callables
_CMP_OPS: dict[type, Any] = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

_ALLOWED_NODES = frozenset(
    {
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.UnaryOp,
        ast.Not,
        ast.Compare,
        ast.Constant,
        ast.Name,
        ast.Attribute,
        ast.List,
        ast.Tuple,
        *_CMP_OPS.keys(),
    }
)

# Aliases recognised as constants
_CONSTANT_ALIASES: dict[str, Any] = {
    "true": True,
    "false": False,
    "none": None,
    "True": True,
    "False": False,
    "None": None,
}


class _SafeConditionEvaluator(ast.NodeVisitor):
    """Walks a parsed AST expression and evaluates it against a context dict.

    Only a strict whitelist of node types is permitted; anything else raises
    ``ValueError`` so the caller can treat the condition as unevaluable.
    """

    def __init__(self, context: dict[str, Any]):
        self._context = context

    def visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        if type(node) not in _ALLOWED_NODES:
            raise ValueError(f"Unsafe AST node type: {type(node).__name__}")
        return super().visit(node)

    # --- literal values ---

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    # --- variable lookup (Name) ---

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in _CONSTANT_ALIASES:
            return _CONSTANT_ALIASES[node.id]
        return self._get_value(node.id)

    # --- dotted attribute access (e.g. user.name) ---

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        attr = node.attr
        if attr.startswith("_"):
            raise ValueError(f"Access to private/dunder attribute '{attr}' is not allowed")
        obj = self.visit(node.value)
        if isinstance(obj, dict):
            return obj.get(attr)
        return getattr(obj, attr, None)

    # --- collections ---

    def visit_List(self, node: ast.List) -> list:
        return [self.visit(el) for el in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> tuple:
        return tuple(self.visit(el) for el in node.elts)

    # --- boolean operators ---

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = self.visit(value)
                if not result:
                    return result
            return result
        else:  # Or
            result = False
            for value in node.values:
                result = self.visit(value)
                if result:
                    return result
            return result

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    # --- comparison operators ---

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            fn = _CMP_OPS.get(type(op))
            if fn is None:
                raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
            if not fn(left, right):
                return False
            left = right
        return True

    # --- helpers ---

    def _get_value(self, name: str) -> Any:
        parts = name.split(".")
        value: Any = self._context
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


class Renderer:
    def __init__(
        self,
        context: dict[str, Any] | None = None,
        base_path: Path | None = None,
        include_paths: list[Path] | None = None,
        package_paths: dict[str, Path] | None = None,
    ):
        """Initialize the renderer with a context dictionary.

        Args:
            context: Dictionary containing variable values for rendering
            base_path: Base directory path for resolving include statements
            include_paths: Additional search paths checked in order when an include
                is not found under base_path
            package_paths: Mapping of package name to its src/ directory.
                Enables conflict-free includes via ``[[ pkg_name/file ]]`` syntax.
                When the first path component matches a key, the rest of the path
                is resolved relative to that package's src/ directory.
        """
        self.context = context or {}
        self.base_path = base_path or Path.cwd()
        self.include_paths = include_paths or []
        self.package_paths = package_paths or {}

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

        elif isinstance(node, WhileNode):
            output = []
            while self._evaluate_condition(node.condition):
                try:
                    output.append(self.render(node.block))
                except _BreakSignal:
                    break
            return "".join(output)

        elif isinstance(node, ForNode):
            iterable = self._resolve_iterable(node.iterable)
            if not iterable:
                return ""

            output = []
            for item in iterable:
                old_value = self.context.get(node.iterator)

                self.context[node.iterator] = item
                try:
                    output.append(self.render(node.block))
                except _BreakSignal:
                    if old_value is not None:
                        self.context[node.iterator] = old_value
                    else:
                        self.context.pop(node.iterator, None)
                    break

                if old_value is not None:
                    self.context[node.iterator] = old_value
                else:
                    self.context.pop(node.iterator, None)

            return "".join(output)

        elif isinstance(node, BreakNode):
            raise _BreakSignal()

        elif isinstance(node, AllAwaitNode):
            return ""

        elif isinstance(node, IncludeNode):
            template_name = node.template_name
            if not template_name.endswith(".mg"):
                template_name += ".mg"

            include_path = self._resolve_include_path(template_name)

            if include_path is None:
                print(f"Included template not found: {template_name}")
                return ""

            try:
                template_content = include_path.read_text()

                parser = Parser()
                _, included_nodes = parser.parse(template_content)

                # Included templates only see variables explicitly passed as params
                include_context = dict(node.params)

                included_renderer = Renderer(
                    context=include_context,
                    base_path=self.base_path,
                    include_paths=self.include_paths,
                    package_paths=self.package_paths,
                )
                return included_renderer.render(included_nodes)

            except Exception:
                return ""
        else:
            return ""

    def _resolve_include_path(self, template_name: str) -> Path | None:
        """Resolve the path to an included template.

        Resolution order:
        1. base_path / template_name (local files always win)
        2. If the first path component matches a key in package_paths, resolve
           the remainder relative to that package's src/ directory.
        3. Each path in include_paths in order (unnamespaced fallback)

        Args:
            template_name: Template filename (with .mg extension)

        Returns:
            Resolved Path if found, None otherwise
        """
        candidate = self.base_path / template_name
        if candidate.exists():
            return candidate

        parts = Path(template_name).parts
        if len(parts) > 1 and parts[0] in self.package_paths:
            pkg_src = self.package_paths[parts[0]]
            candidate = pkg_src.joinpath(*parts[1:])
            if candidate.exists():
                return candidate

        for search_path in self.include_paths:
            candidate = search_path / template_name
            if candidate.exists():
                return candidate

        return None

    def _resolve_iterable(self, expr: str) -> Any:
        """Resolve a for-loop iterable — either a context variable or a range() call."""
        expr = expr.strip()
        range_match = re.match(r"^range\((.+)\)$", expr)
        if range_match:
            args_str = range_match.group(1)
            args = [arg.strip() for arg in args_str.split(",")]
            int_args = []
            for arg in args:
                try:
                    int_args.append(int(arg))
                except ValueError:
                    val = self._get_variable_value(arg)
                    if val is None:
                        return []
                    int_args.append(int(val))
            return range(*int_args)
        return self._get_variable_value(expr)

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
        """Safely evaluate a condition expression using the ast module.

        Supports: or, and, not, in, not in, ==, !=, >, <, >=, <=, and simple truthy checks.
        No arbitrary code execution — only a strict whitelist of AST node types is allowed.

        Args:
            condition: The condition string to evaluate

        Returns:
            True if the condition is true, False otherwise, None on error
        """
        condition = condition.strip()

        does_condition_contain_equality_or_logical = any(
            op in condition for op in EQUALITY_OR_LOGICAL_OPERATORS
        )

        if does_condition_contain_equality_or_logical:
            try:
                tree = ast.parse(condition, mode="eval")
                result = _SafeConditionEvaluator(self.context).visit(tree.body)
                return bool(result)
            except Exception:
                return None

        # Simple variable — evaluate as a truthy check
        value = self._get_variable_value(condition)
        return self._is_truthy(value)

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
