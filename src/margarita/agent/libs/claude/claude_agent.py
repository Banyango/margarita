from datetime import UTC, datetime

from claude_agent_sdk import ClaudeAgentOptions, SdkMcpTool, create_sdk_mcp_server
from claude_agent_sdk.query import query
from claude_agent_sdk.types import (
    AssistantMessage,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolPermissionContext,
    ToolResultBlock,
    ToolUseBlock, UserMessage,
)
from wireup import injectable

from margarita.agent import ContentBlock
from margarita.agent.app.config import AppConfig
from margarita.agent.core.agents.models import ExecutionModel, PermissionPrompt
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.core.interfaces.query_service import QueryService
from margarita.agent.entities.run import (
    ContentBlockType,
    ModelUsage,
    RunStatus,
    ShutdownReason,
    TokenUsage,
    ToolCall,
)
from margarita.agent.libs.claude.tools.get_variable_from_state import create_get_variable_tool
from margarita.agent.libs.claude.tools.set_variable_in_state import create_set_variable_tool

SYSTEM_PROMPT = """
Role
You are an autonomous coding agent with access to persistent state management through MCP (Model Context Protocol) tools.

# MANDATORY RULE — Read Before You Use

**You MUST call `get_variable` before using ANY variable value — no exceptions.**

This rule overrides everything else. It applies even when:
- The value appears in the conversation history
- You believe you already know it
- It seems obvious from context
- You computed it yourself in a previous turn

**Do NOT infer, recall, or concatenate variable values from memory or conversation text. Always retrieve them with `get_variable` first.**

If a task involves a variable and you have not yet called `get_variable` for it in this turn, stop and call it now before proceeding.

# Available State Tools
You have two MCP tools for managing shared state across conversation turns:
- **get_variable**: Retrieves a variable from persistent state
- **set_variable**: Stores a variable in persistent state

# State Management Rules

## Reading State
- Call `get_variable` at the start of every task for each variable you will use
- If get_variable returns no result or null, handle it gracefully — compute a default rather than asking the user
- Never substitute string concatenation, f-strings, or text interpolation for a proper `get_variable` call

## Writing State
- Call `set_variable` after computing any value needed in future turns or steps
- Checkpoint progress in long-running workflows
- Record errors or debugging information when relevant

## Variable Naming
- Use clear, deterministic names: `build_status`, `user_config`, `current_step`
- Prefer primitive types: strings, numbers, booleans
- Store complex data as JSON strings: `test_results_json`
- Use prefixes for organization: `temp_*` for ephemeral data, `config_*` for settings

## State Hygiene
- Briefly mention which variable names were read or written — not their full values unless relevant
- Don't clutter output with excessive state management details

# Workflow Pattern
1. **Read** — call `get_variable` for every variable this task touches
2. **Process** — use the retrieved values to compute, analyze, or decide
3. **Write** — persist results with `set_variable`
4. **Report** — summarize progress to the user concisely
"""

INTERNAL_TOOLS = [
    "ToolSearch"
]

IGNORE_PERMISSION_TOOLS = [
    "get_variable",
    "set_variable",
]

def _normalize_tool_name(name: str) -> str:
    if "get_variable" in name:
        return "get_variable"
    if "set_variable" in name:
        return "set_variable"
    return name


@injectable(as_type=QueryService, qualifier="claude")
class ClaudeAgent(QueryService):
    def __init__(
        self,
        app_config: AppConfig | None = None,
        logger: LoggerService | None = None,
    ):
        self.app_config = app_config or AppConfig()
        self.logger_service = logger

    async def execute_query(self, execution_model: ExecutionModel, params: str) -> str:
        async def can_use_tool(
            tool_name: str, tool_input: dict, context: ToolPermissionContext
        ) -> PermissionResultAllow | PermissionResultDeny:
            tool_name = _normalize_tool_name(tool_name)

            if self.app_config.ignore_permissions or tool_name in IGNORE_PERMISSION_TOOLS:
                return PermissionResultAllow()

            prompt = PermissionPrompt(
                kind="tool",
                details={"tool_name": tool_name, "input": tool_input},
            )

            await execution_model.request_permission(prompt)

            if prompt.approved:
                return PermissionResultAllow()
            return PermissionResultDeny(message="Denied by user")

        model_id = id(execution_model)

        model_value = execution_model.model
        if isinstance(model_value, str):
            model_value = model_value.strip('"').strip("'")

        system_prompt = SYSTEM_PROMPT
        if not self.app_config.use_existing_system_prompt and self.app_config.system_prompt:
            system_prompt = self.app_config.system_prompt

        state_tools: list[SdkMcpTool] = [
            create_get_variable_tool(execution_model),
            create_set_variable_tool(execution_model),
        ]
        state_server = create_sdk_mcp_server(name="variables", tools=state_tools)

        options = ClaudeAgentOptions(
            model=model_value,
            system_prompt=system_prompt,
            can_use_tool=can_use_tool,
            permission_mode="bypassPermissions" if self.app_config.ignore_permissions else None,
            mcp_servers={"state": state_server},
            strict_mcp_config=True,
            allowed_tools=["get_variable", "set_variable"],
        )

        async def prompt_stream():
            yield {
                "type": "user",
                "message": {"role": "user", "content": var_list + execution_model.context.window},
                "parent_tool_use_id": None,
            }

        if self.logger_service:
            self.logger_service.print(
                f"[Run started]\n"
                f" model={execution_model.model}"
                f" prompt={execution_model.context.window}\n"
                f" state={execution_model.context.data}"
            )

        execution_model.on_complete_run()

        var_list = ""
        if len(execution_model.context.data.keys()) > 0:
            var_list = f"These are variable names that exist in state \n {execution_model.context.data.keys()}\n\n"

        run = execution_model.start_run(
            name=params,
            prompt=execution_model.context.window,
            provider="claude",
            status=RunStatus.RUNNING,
            start_time=datetime.now(UTC),
        )

        result = ""
        try:
            async for message in query(prompt=prompt_stream(), options=options):
                if isinstance(message, AssistantMessage):
                    if message.model:
                        run.model = message.model

                    for block in message.content:
                        if isinstance(block, TextBlock):
                            if run.responses is None:
                                run.responses = [""]
                            run.responses[-1] += block.text
                            if (
                                not run.content_blocks
                                or run.content_blocks[-1].type != ContentBlockType.REASONING
                            ):
                                run.content_blocks.append(ContentBlock(type=ContentBlockType.RESPONSE))
                            run.content_blocks[-1].text += block.text
                            result += block.text

                        elif isinstance(block, ThinkingBlock):
                            if run.reasoning is None:
                                run.reasoning = [""]
                            run.reasoning[-1] += block.thinking
                            if (
                                not run.content_blocks
                                or run.content_blocks[-1].type != ContentBlockType.REASONING
                            ):
                                run.content_blocks.append(ContentBlock(type=ContentBlockType.REASONING))
                            run.content_blocks[-1].text += block.thinking

                        elif isinstance(block, ToolUseBlock):
                            if block.name in INTERNAL_TOOLS:
                                continue

                            run.tool_calls.append(
                                ToolCall(
                                    tool_call_id=block.id,
                                    tool_name=_normalize_tool_name(block.name),
                                    arguments=block.input,
                                )
                            )
                            run.content_blocks.append(
                                ContentBlock(
                                    type=ContentBlockType.TOOL_CALL,
                                    ref=block.id,
                                )
                            )
                            if self.logger_service:
                                self.logger_service.print(f"[Tool call - {block.name}]")

                    if message.usage:
                        turn_tokens = TokenUsage(
                            input_tokens=int(message.usage.get("input_tokens", 0)),
                            output_tokens=int(message.usage.get("output_tokens", 0)),
                            cache_read_tokens=int(message.usage.get("cache_read_input_tokens", 0)),
                            cache_write_tokens=int(message.usage.get("cache_creation_input_tokens", 0)),
                        )
                        run.tokens.accumulate(turn_tokens)
                        run.request_count += 1
                        if message.model and message.model not in run.model_usage:
                            run.model_usage[message.model] = ModelUsage(model=message.model)
                        if message.model:
                            mu = run.model_usage[message.model]
                            mu.request_count += 1
                            mu.tokens.accumulate(turn_tokens)
                elif isinstance(message, UserMessage):
                    for block in message.content:
                        if isinstance(block, ToolResultBlock):
                            for tc in reversed(run.tool_calls):
                                if tc.tool_call_id == block.tool_use_id:
                                    tc.success = not block.is_error
                                    if isinstance(block.content, str):
                                        tc.result = block.content
                                    elif block.content:
                                        tc.result = str(block.content)
                                    break
                elif isinstance(message, ResultMessage):
                    if message.total_cost_usd:
                        run.total_cost += message.total_cost_usd
                    if message.result and not result:
                        result = message.result
                    run.end_time = datetime.now(UTC)
                    run.status = RunStatus.COMPLETED

            if run.status != RunStatus.COMPLETED:
                run.end_time = datetime.now(UTC)
                run.status = RunStatus.COMPLETED
            if run.start_time and run.end_time:
                run.duration_ms = (run.end_time - run.start_time).total_seconds() * 1000

            if self.logger_service:
                self.logger_service.print(
                    f"[Run completed]"
                    f" duration={(run.duration_ms or 0) / 1000:.1f}s"
                    f" status={run.status.value}"
                )

            execution_model.current_run.result = result

        except TimeoutError:
            run.status = RunStatus.ERROR
            run.end_time = datetime.now(UTC)
            await execution_model.dismiss_all_overlays()

            if self.logger_service:
                self.logger_service.print(f"[Run error] shutdown_reason={ShutdownReason.TIMEOUT}")

            execution_model.start_turn()

            return ""

        execution_model.start_turn()

        return result

    async def clear_session(self):
        pass
