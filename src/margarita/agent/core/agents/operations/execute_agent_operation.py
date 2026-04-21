import ast
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

from margarita.agent import ContentBlock
from margarita.agent.core.agents.models import BreakSignal, ExecutionModel
from margarita.agent.core.agents.plugins.import_plugin import ImportPlugin
from margarita.agent.core.agents.services.memory import MemoryService
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.entities.context import Context
from margarita.agent.entities.prompt_integrity import (
    TRACKED_PROMPT_EXTENSIONS,
    PromptUnverifiedPathError,
)
from margarita.agent.entities.run import ContentBlockType
from margarita.language.parser import (
    AllAwaitNode,
    BreakNode,
    EffectNode,
    ForNode,
    IfNode,
    ImportNode,
    IncludeNode,
    MemoryNode,
    Node,
    Parser,
    StateNode,
    TextNode,
    VariableNode,
)

EQUALITY_OR_LOGICAL_OPERATORS = [
    "==",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    " and ",
    " or ",
    " not ",
    " in ",
    " is ",
    "not ",
]


class ExecuteAgentOperation:
    """Operation that orchestrates execution of a .mgx agent file.

    Responsibilities include parsing the Margarita AST, dispatching @effect
    tokens to plugins, managing execution state, and collecting run results.
    """

    def __init__(
        self,
        plugins: list[AgentPlugin],
        execution_model: ExecutionModel,
        memory_service: MemoryService,
        prompt_integrity: PromptIntegrity | None = None,
        allow_unverified: bool = False,
    ):
        self.base_path = None
        self.plugins = plugins
        self.memory_service = memory_service
        self.execution_model = execution_model
        self.prompt_integrity = prompt_integrity
        self.allow_unverified = allow_unverified
        self._kv_iterators: dict[tuple[str, str], str] = {}

    def _preprocess_kv_for_loops(self, content: str) -> str:
        """Replace 'for key, value in iterable:' with 'for key in iterable:' and
        record the value variable name so it can be set during iteration."""

        def replace_kv_for(m: re.Match) -> str:
            key_var, val_var, iterable = m.group(1), m.group(2), m.group(3)
            self._kv_iterators[(key_var, iterable)] = val_var
            return f"for {key_var} in {iterable}:"

        return re.sub(
            r"^for\s+(\w+),\s*(\w+)\s+in\s+(\w+):", replace_kv_for, content, flags=re.MULTILINE
        )

    async def execute_async(self, mgx_file: str, base_path: Path | None = None):
        """Execute an .mgx file with an agent

        Args:
            mgx_file: The content of the .mgx file to execute
            base_path: Optional base directory path for resolving include statements
        """
        self.base_path = base_path or Path.cwd()

        for plugin in self.plugins:
            if hasattr(plugin, "set_base_path"):
                plugin.set_base_path(self.base_path)

        self.execution_model.memory = await self.memory_service.load_memory(
            self.execution_model.context
        )

        parser = Parser()
        metadata, nodes = parser.parse(self._preprocess_kv_for_loops(mgx_file))

        self.execution_model.metadata = metadata

        self.execution_model.start_turn()

        await self._process_nodes_async(nodes, self.execution_model.context)

        # Save the memory at the end of execution
        await self.memory_service.save_memory(self.execution_model.memory)

    async def _process_nodes_async(self, nodes: list[Node], context: Context | None = None):
        """Process a list of AST nodes, executing actions based on node type.

        Args:
            nodes: List of parsed AST nodes to process
            context: Context to use for all operations within this method
        """
        if context is None:
            context = self.execution_model.context

        for node in nodes:
            if self.execution_model.stopped:
                return

            if isinstance(node, TextNode):
                if context is None:
                    context = self.execution_model.context

                final_content = context.replace_variables_in_content(node.content)
                context.add_to_context_window(final_content)

            elif isinstance(node, VariableNode):
                value = context.get_variable_value(node.name)
                if value is not None:
                    context.add_to_context_window(str(value))

            elif isinstance(node, IfNode):
                condition_value = self._evaluate_condition(node.condition, context)
                if self._is_truthy(condition_value):
                    await self._process_nodes_async(node.true_block, context)
                elif node.false_block:
                    await self._process_nodes_async(node.false_block, context)

            elif isinstance(node, MemoryNode):
                await self._handle_memory_node_async(node.params)

            elif isinstance(node, BreakNode):
                raise BreakSignal()

            elif isinstance(node, ForNode):
                items = context.get_variable_value(node.iterable)
                if items:
                    value_var = self._kv_iterators.get((node.iterator, node.iterable))
                    if value_var is not None and isinstance(items, dict):
                        pairs = list(items.items())
                    else:
                        pairs = [(item, None) for item in items]

                    for key, val in pairs:
                        context.add_to_state(node.iterator, key)
                        if value_var is not None:
                            context.add_to_state(value_var, val)
                        try:
                            await self._process_nodes_async(node.block, context)
                        except BreakSignal:
                            break
                        finally:
                            context.remove_from_state(node.iterator)
                            if value_var is not None:
                                context.remove_from_state(value_var)

            elif isinstance(node, StateNode):
                variable = self._parse_state_value(node.initial_value)
                context.set_variable(node.variable_name, variable)

            elif isinstance(node, ImportNode):
                ImportPlugin.execute_import(node.raw_import, self.execution_model)

            elif isinstance(node, IncludeNode):
                file_path = self._normalize_include_path(node.template_name)
                include_path = (self.base_path / file_path).resolve(strict=False)
                if not include_path.exists():
                    raise FileNotFoundError(
                        f"Included prompt file was not found: '{include_path}'."
                    )

                should_verify_file = True
                if self.prompt_integrity:
                    try:
                        self.prompt_integrity.verify_trusted_path(include_path)
                    except PromptUnverifiedPathError as error:
                        if not self.allow_unverified:
                            raise

                        should_verify_file = False
                        logger.warning(
                            "Allowing unverified include outside trusted prompt root: path='{}' reason='{}' "
                            "(enabled by --allow-unverified)",
                            include_path,
                            error,
                        )

                content_bytes = include_path.read_bytes()
                if self.prompt_integrity and should_verify_file:
                    self.prompt_integrity.verify_bytes(
                        path=include_path, content_bytes=content_bytes
                    )

                content = content_bytes.decode()
                parser = Parser()
                _, include_nodes = parser.parse(content)

                resolved_params = {}
                for k, v in node.params.items():
                    resolved = context.get_variable_value(v)
                    resolved_params[k] = resolved if resolved is not None else v
                scoped_context = Context(resolved_params)
                await self._process_nodes_async(include_nodes, scoped_context)

                context.add_to_context_window(scoped_context.window)

            elif isinstance(node, AllAwaitNode):
                self.execution_model.add_content_block(
                    ContentBlock(
                        type=ContentBlockType.AWAIT_ALL,
                        text=f"[AwaitAll] processing children... {len(node.effect_nodes)} effect(s)",
                    )
                )
                results = await asyncio.gather(
                    *[
                        self._execute_effect_async(effect.raw_content)
                        for effect in node.effect_nodes
                    ],
                    return_exceptions=True,
                )
                for result in results:
                    if isinstance(result, BaseException):
                        self.execution_model.add_content_block(
                            ContentBlock(
                                type=ContentBlockType.LOGGING,
                                text=f"[AwaitAll] Child failed: {result}",
                            )
                        )

            elif isinstance(node, EffectNode):
                await self._execute_effect_async(node.raw_content)

    async def _execute_effect_async(self, parameters: str):
        """Execute Python code from EffectNodes using imported modules.

        Args:
            parameters: The parameters.
        """
        split = parameters.split(" ", 1)

        plugin = split[0] if len(split) >= 1 else None
        operation = split[1] if len(split) > 1 else None

        await self._execute_plugin_async(plugin=plugin, operation=operation)

    async def _execute_plugin_async(self, plugin: str, operation: str):
        """Execute a plugin operation.

        Args:
            plugin (str): The name of the plugin to execute.
            operation (str): The operation to perform with the plugin.
        """
        for effect_plugin in self.plugins:
            if effect_plugin.is_match(plugin):
                await effect_plugin.handle(
                    params=operation,
                    execution_model=self.execution_model,
                )
                break

    async def _handle_memory_node_async(self, params: str):
        params = params.strip()

        if params == "clear":
            self.memory_service.clear_memory(self.execution_model.memory)
            self.execution_model.add_content_block(
                ContentBlock(
                    type=ContentBlockType.LOGGING, text="[Memory] Cleared all memory variables"
                )
            )
            return

        delete_match = re.match(r"^delete\s+(\w+)$", params)
        if delete_match:
            name = delete_match.group(1)

            self.memory_service.delete_memory_variable(name, self.execution_model.memory)

            self.execution_model.add_content_block(
                ContentBlock(type=ContentBlockType.LOGGING, text=f"[Memory] Deleted '{name}'")
            )
            return

        var_match = re.match(r"^var\s+(\w+)(?:\s*=\s*(.+))?$", params)
        if var_match:
            self.memory_service.add_memory_variable(
                value_group=var_match.group(2),
                name=var_match.group(1),
                memory=self.execution_model.memory,
            )
            self.execution_model.add_content_block(
                ContentBlock(
                    type=ContentBlockType.LOGGING,
                    text=f"[Memory] Set variable '{var_match.group(1)}'",
                )
            )
            return

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

    @staticmethod
    def _parse_state_value(raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(raw)
            except (ValueError, SyntaxError) as e:
                raise ValueError(f"Cannot parse state value: {raw!r}") from e

    @staticmethod
    def _evaluate_condition(condition: str, context: Context) -> Any:
        """Evaluate a condition, which can be a simple variable or a Python expression.

        Args:
            condition: The condition string to evaluate

        Returns:
            The evaluated value of the condition
        """
        condition = condition.strip()

        literal_values = {"true": True, "false": False, "none": None}
        lowered_condition = condition.lower()
        if lowered_condition in literal_values:
            return literal_values[lowered_condition]

        does_condition_contain_equality_or_logical = any(
            op in condition for op in EQUALITY_OR_LOGICAL_OPERATORS
        )

        if does_condition_contain_equality_or_logical:
            try:
                namespace = dict(context.data)
                namespace.update(literal_values)
                result = eval(condition, {"__builtins__": {}}, namespace)
                return result
            except Exception:
                # If evaluation fails, treat as a falsy value
                return None

        result = context.get_variable_value(condition)

        return result

    @staticmethod
    def _normalize_include_path(template_name: str) -> str:
        """Normalize the include path.

        Args:
            template_name: The name of the template to normalize.

        Returns:
            The normalized template name.
        """
        include_path = template_name.strip()
        suffix = Path(include_path).suffix
        if not suffix:
            return f"{include_path}.mg"

        if suffix not in TRACKED_PROMPT_EXTENSIONS:
            raise ValueError(
                f"Unsupported include extension '{suffix}' in '{template_name}'. Only .mg or .mgx are allowed."
            )

        return include_path
