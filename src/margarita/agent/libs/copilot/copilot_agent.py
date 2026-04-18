from dataclasses import asdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from copilot import define_tool
from copilot.generated.session_events import PermissionRequest, SessionEventType
from copilot.session import (
    InfiniteSessionConfig,
    PermissionRequestResult,
    SystemMessageAppendConfig,
    SystemMessageReplaceConfig,
    UserInputRequest,
    UserInputResponse,
)
from wireup import injectable

if TYPE_CHECKING:
    from copilot.tools import Tool

from margarita.agent.app.config import AppConfig
from margarita.agent.core.agents.models import ExecutionModel, InputRequest, PermissionPrompt
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.core.interfaces.query_service import QueryService
from margarita.agent.entities.run import (
    CodeChanges,
    ContentBlock,
    ContentBlockType,
    ModelUsage,
    RunContext,
    RunError,
    RunEventEnum,
    RunStatus,
    ShutdownReason,
    TokenUsage,
    ToolCall,
)
from margarita.agent.libs.copilot.client import GithubCopilotClient, SessionConfig
from margarita.agent.libs.copilot.tools.get_variable_from_state import create_get_variable_tool
from margarita.agent.libs.copilot.tools.set_variable_in_state import (
    create_set_variable_tool,
)

SYSTEM_PROMPT = """# Role
You are an autonomous coding agent with explicit access to two extra tools for shared state:
a get-variable tool and a set-variable tool. For every piece of state you need to read or update you must
use these tools; do not assume, invent, or hardcode values from memory or ask the user for them.

## Rules:
- Always call the get-variable tool before using any variable. If the variable is missing or empty,
do not fabricate it — either compute it from available data or create it via the set-variable tool.
- Always call the set-variable tool to persist any information you want available to future steps. This includes docs, plans, decisions, and any intermediate variables you create. Do not assume that any information is stored in memory unless you have explicitly saved it with set-variable.
- After each tool call, read and respect the tool's result. If a tool call fails, handle the failure
and record an error variable via set-variable if needed.
- Use deterministic variable names and prefer primitive values (string/number/boolean).
If you must store structured data, store it as JSON under a clear name.
- Do not prompt the user for missing values; act autonomously using available tools.

Tool call format (follow this pattern when requesting a tool):
- Read: CALL_TOOL: get_variable with arguments { "name": "<variable_name>" }
- Write: CALL_TOOL: set_variable with arguments { "name": "<variable_name>", "value": <value> }

Behavior after actions:
- Summarize the action taken and any state changes (variable names and values) in the assistant message
so the run log is clear.
- Use temporary names like `temp_<short_desc>` if you need ephemeral storage.

Examples:
- To read build status: CALL_TOOL: get_variable { "name": "build_status" }
- To record an error: CALL_TOOL: set_variable { "name": "latest_error", "value": "stacktrace..." }

Always follow these rules for each run so the shared state remains accurate and consistent."""

SESSION_EVENT_TYPE_MAP: dict[SessionEventType, RunEventEnum] = {
    SessionEventType.SESSION_IDLE: RunEventEnum.THINKING,
    SessionEventType.SESSION_START: RunEventEnum.RUNNING,
    SessionEventType.ASSISTANT_REASONING_DELTA: RunEventEnum.REASONING,
    SessionEventType.ASSISTANT_MESSAGE_DELTA: RunEventEnum.RESPONSE,
    SessionEventType.TOOL_EXECUTION_START: RunEventEnum.FETCHING,
    SessionEventType.TOOL_EXECUTION_COMPLETE: RunEventEnum.THINKING,
}


@injectable(as_type=QueryService)
class CopilotQuery(QueryService):
    """QueryService implementation for interacting with GitHub Copilot.

    Manages sessions, streams events from the Copilot SDK, and exposes run
    methods used by RunAgentPlugin to execute LLM queries.
    """

    def __init__(
        self,
        copilot_client: GithubCopilotClient,
        app_config: AppConfig | None = None,
        logger: LoggerService | None = None,
    ):
        self.client = copilot_client
        # Allow omission in tests; default to a basic AppConfig when not provided.
        self.app_config = app_config or AppConfig()
        self.logger_service = logger

    async def execute_query(self, execution_model: ExecutionModel, params: str) -> str:
        """Execute a query using the Copilot client.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
            params (str): The query parameters for the execution model.
        """
        if not self.client.con:
            raise Exception("Copilot client is not connected")

        async def on_user_input_request(
            request: UserInputRequest, _properties: dict[str, str]
        ) -> UserInputResponse:
            """Handle a user input request from the Copilot session.

            This method is called when the agent uses the get-variable tool to request a variable that has not been set yet.
            The prompt argument contains the message from the agent describing what information it needs.

            Args:
                request (UserInputRequest): The user input request from the Copilot session, containing the prompt.
                _properties (dict[str, str]): Additional properties related to the request.
            """
            request = InputRequest(prompt=request["question"])
            await execution_model.request_input(request)
            user_input = request.response or ""

            return UserInputResponse(answer=user_input, wasFreeform=True)

        _INTERNAL_TOOLS = {"get_variable", "set_variable"}

        async def on_permission_request(
            request: PermissionRequest, _properties: dict
        ) -> PermissionRequestResult:
            if self.app_config.ignore_permissions:
                return PermissionRequestResult(kind="approved")

            if request.tool_name in _INTERNAL_TOOLS:
                return PermissionRequestResult(kind="approved")

            prompt = PermissionPrompt(kind=request.kind.value, details=asdict(request))

            await execution_model.request_permission(prompt)

            if prompt.approved:
                return PermissionRequestResult(kind="approved")

            return PermissionRequestResult(kind="denied-interactively-by-user")

        # Convert any internal Tool descriptors into Copilot SDK Tool objects.
        # We'll build a list of extra tools and pass them into the session.
        extra_tools: list[Tool] = []
        if execution_model.context.tools:
            for tool in execution_model.context.tools:
                name = tool.name
                params = tool.params
                description = tool.description

                funct = execution_model.globals_dict[name]
                if not funct:
                    break

                if params and len(params) == 1:
                    params_type = execution_model.globals_dict[params[0].type]

                    if not params_type:
                        execution_model.current_run.errors.append(
                            "Invalid tool parameter type: (Did you forget to import this type?)"
                            + params[0].type
                        )

                    tool = define_tool(
                        name=name,
                        description=description or "",
                        params_type=params_type,
                        handler=funct,
                    )

                    extra_tools.append(tool)

        get_var_tool = await create_get_variable_tool(execution_model=execution_model)
        set_var_tool = await create_set_variable_tool(execution_model=execution_model)

        # Build tool list for the session (set and get variable tools first)
        session_tools = [set_var_tool, get_var_tool, *extra_tools]

        model_value = execution_model.model
        if isinstance(model_value, str):
            # Strip surrounding quotes if parser preserved them in front-matter
            model_value = model_value.strip('"').strip("'")

        system_message = SystemMessageAppendConfig(content=SYSTEM_PROMPT)
        if not self.app_config.use_existing_system_prompt:
            system_message = SystemMessageReplaceConfig(
                mode="replace",
                content=self.app_config.system_prompt + SYSTEM_PROMPT,
            )

        session_attr = getattr(self.client, "session", None)
        if not session_attr:
            try:
                session_config = SessionConfig(
                    system_message=system_message,
                    model=model_value or "gpt-5-mini",
                    streaming=True,
                    on_user_input_request=on_user_input_request,
                    on_permission_request=on_permission_request,
                    infinite_sessions=InfiniteSessionConfig(
                        enabled=True,
                    ),
                    tools=session_tools,
                )
            except TypeError:
                # Fallback for test doubles that accept a simpler signature
                session_config = SessionConfig(
                    system_message=SystemMessageAppendConfig(content=SYSTEM_PROMPT),
                    model=model_value or "gpt-5-mini",
                    streaming=True,
                    tools=session_tools,
                    infinite_sessions=None,
                )

            await self.client.create_session(session_config=session_config)

        if self.logger_service:
            self.logger_service.print(
                f"[Run started]\n"
                f" model={execution_model.model}"
                f" prompt={execution_model.context.window},\n"
                f" state=f{execution_model.context.data}\n tools={[tool.name for tool in session_tools]}"
            )

        run = execution_model.start_run(
            name=params,
            prompt=execution_model.context.window,
            provider="copilot",
            status=RunStatus.RUNNING,
            start_time=datetime.now(UTC),
        )

        def handle_event(event):
            d = event.data

            if event.type in SESSION_EVENT_TYPE_MAP:
                execution_model.current_run.event_name = SESSION_EVENT_TYPE_MAP[event.type]

            if event.type == SessionEventType.SESSION_START:
                run.session_id = d.session_id
                run.model = d.selected_model or d.current_model
                if d.context and hasattr(d.context, "cwd"):
                    run.context = RunContext(
                        cwd=d.context.cwd,
                        git_root=d.context.git_root,
                        branch=d.context.branch,
                    )
                if d.repository:
                    run.context.repository_owner = d.repository.owner
                    run.context.repository_name = d.repository.name

            elif event.type == SessionEventType.ASSISTANT_REASONING_DELTA:
                if run.reasoning is None:
                    run.reasoning = [""]
                run.reasoning[-1] += d.delta_content
                if (
                    not run.content_blocks
                    or run.content_blocks[-1].type != ContentBlockType.REASONING
                ):
                    run.content_blocks.append(ContentBlock(type=ContentBlockType.REASONING))
                run.content_blocks[-1].text += d.delta_content

            elif event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
                if run.responses is None:
                    run.responses = [""]
                run.responses[-1] += d.delta_content
                if (
                    not run.content_blocks
                    or run.content_blocks[-1].type != ContentBlockType.RESPONSE
                ):
                    run.content_blocks.append(ContentBlock(type=ContentBlockType.RESPONSE))
                run.content_blocks[-1].text += d.delta_content

            elif (
                event.type == SessionEventType.ASSISTANT_TURN_END
                or event.type == SessionEventType.ASSISTANT_MESSAGE
            ):
                # Start a new entry for the next turn
                if run.responses is not None:
                    if self.logger_service:
                        self.logger_service.print(f"[response] {run.responses[-1]}")
                    run.responses.append("")
                if run.reasoning is not None:
                    if self.logger_service:
                        self.logger_service.print(f"[reasoning] {run.reasoning[-1]}")
                    run.reasoning.append("")
            elif event.type == SessionEventType.SESSION_USAGE_INFO:
                pass
            elif event.type == SessionEventType.ASSISTANT_USAGE:
                run.request_count += 1
                turn_tokens = TokenUsage(
                    input_tokens=int(d.input_tokens or 0),
                    output_tokens=int(d.output_tokens or 0),
                    cache_read_tokens=int(d.cache_read_tokens or 0),
                    cache_write_tokens=int(d.cache_write_tokens or 0),
                )
                run.tokens.accumulate(turn_tokens)
                if d.cost:
                    run.total_cost += d.cost
                model = d.model or run.model
                if model:
                    if model not in run.model_usage:
                        run.model_usage[model] = ModelUsage(model=model)
                    mu = run.model_usage[model]
                    mu.request_count += 1
                    mu.tokens.accumulate(turn_tokens)
                    if d.cost:
                        mu.cost += d.cost

            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                if d.tool_name == "report_intent":
                    # This is an internal tool used for logging the agent's intent,
                    # we can ignore it in the run log.
                    return

                if d.tool_name == "ask_user":
                    response = f"[Question] {d.arguments.get('question', '')}"
                    for choice in d.arguments.get("choices", []):
                        response += f"\n- {choice}"

                    run.content_blocks.append(
                        ContentBlock(
                            type=ContentBlockType.INPUT,
                            ref=d.tool_call_id,
                            text=response,
                        )
                    )
                else:
                    run.tool_calls.append(
                        ToolCall(
                            tool_name=d.tool_name,
                            tool_call_id=d.tool_call_id,
                            arguments=d.arguments,
                        )
                    )
                    run.content_blocks.append(
                        ContentBlock(
                            type=ContentBlockType.TOOL_CALL,
                            ref=d.tool_call_id,
                        )
                    )

            elif event.type == SessionEventType.TOOL_EXECUTION_COMPLETE:
                for tc in reversed(run.tool_calls):
                    if tc.tool_call_id == d.tool_call_id:
                        tc.result = d.result.content if d.result else None
                        tc.success = d.success
                        tc.duration_ms = d.duration
                        if self.logger_service:
                            self.logger_service.print(f"[Tool call - {tc.tool_name}]: {tc.result}")
                        break

            elif event.type == SessionEventType.SESSION_MODEL_CHANGE:
                run.model = d.new_model

            elif event.type == SessionEventType.SESSION_ERROR:
                run.errors.append(
                    RunError(
                        message=d.message or "Unknown error",
                        code=d.error_type,
                        stack=d.stack,
                        error_type=d.error_type,
                    )
                )

            elif event.type == SessionEventType.SESSION_SHUTDOWN:
                run.end_time = datetime.now(UTC)
                run.status = RunStatus.COMPLETED
                if d.shutdown_type:
                    run.shutdown_reason = ShutdownReason(d.shutdown_type.value)
                if d.code_changes:
                    run.code_changes = CodeChanges(
                        files_modified=d.code_changes.files_modified,
                        lines_added=int(d.code_changes.lines_added),
                        lines_removed=int(d.code_changes.lines_removed),
                    )
                if d.model_metrics:
                    for model_name, metric in d.model_metrics.items():
                        if model_name not in run.model_usage:
                            run.model_usage[model_name] = ModelUsage(model=model_name)
                        mu = run.model_usage[model_name]
                        mu.request_count = int(metric.requests.count)
                        mu.cost = metric.requests.cost

            elif event.type == SessionEventType.SESSION_IDLE:
                pass

        unsubscribe = self.client.session.on(handle_event)

        try:
            response = await self.client.session.send_and_wait(
                prompt=execution_model.context.window, mode="immediate", timeout=300
            )

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
                    f" shutdown_reason={run.shutdown_reason}"
                )

            execution_model.current_run.result = response.data.content if response else None

            unsubscribe()
        except TimeoutError:
            run.status = RunStatus.ERROR
            run.end_time = datetime.now(UTC)
            await execution_model.dismiss_all_overlays()
            unsubscribe()

            if self.logger_service:
                self.logger_service.print(f"[Run error] shutdown_reason={ShutdownReason.TIMEOUT}")

            execution_model.start_turn()

            return ""

        execution_model.current_run.on_complete()
        execution_model.start_turn()

        return response.data.content

    async def clear_session(self):
        await self.client.destroy_current_session()
