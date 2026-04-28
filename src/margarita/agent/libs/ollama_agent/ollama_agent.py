import asyncio
from datetime import UTC, datetime

from margarita_open_agent.core.llm import LLMClient
from margarita_open_agent.core.models.llm_model_enum import LLMModelEnum
from margarita_open_agent.core.models.session import SessionStartedMetadata
from margarita_open_agent.core.models.tool import ToolDefinition
from margarita_open_agent.core.models.tool_call_event import (
    ToolCallCallingMetadata,
    ToolCallDoneMetadata,
)
from margarita_open_agent.session import AgentSession
from margarita_open_agent.session_event import SessionEventType
from wireup import injectable

from margarita.agent import ContentBlock
from margarita.agent.app.config import AppConfig
from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.core.interfaces.query_service import QueryService
from margarita.agent.entities.run import (
    ContentBlockType,
    Run,
    RunEventEnum,
    RunStatus,
    ShutdownReason,
    ToolCall,
)
from margarita.agent.libs.ollama_agent.custom_tool_handler import (
    GET_TOOL_DEFINITION,
    SET_TOOL_DEFINITION,
    OllamaCustomToolHandler,
)
from margarita.agent.libs.ollama_agent.tool_converter import convert_core_tool_to_ollama
from margarita.agent.libs.ollama_agent.user_input_handler import OllamaUserInputHandler
from margarita.agent.libs.ollama_agent.user_permission_handler import OllamaPermissionHandler

SYSTEM_PROMPT = """
# ROLE:
You are an coding agent with state memory. You can assume other roles but you must always remember
about the following tools at all times and use them to solve the user requests.

get_variable - Gets variables that are not provided. Call this tool to get a variable if you are missing it.
set_variable - Sets variables into the state memory. Call this tool to set a variable for future runs.

Examples:
- Tell me about cats: No tool calls
- Say Hello: No tool calls
- 1 + test = result: CALL_TOOL get_variable {"variable":"test"} then CALL_TOOL set_variable { "variable":"result", "arguments":"2" }
- To read build status: CALL_TOOL: get_variable { "variable": "build_status" }
- To record an error: CALL_TOOL: set_variable { "variable": "latest_error", "arguments": "stacktrace..." }

Always follow these rules for each run so the shared state remains accurate and consistent."""

SESSION_EVENT_TYPE_MAP: dict[SessionEventType, RunEventEnum] = {
    SessionEventType.SESSION_IDLE: RunEventEnum.THINKING,
    SessionEventType.SESSION_START: RunEventEnum.RUNNING,
    SessionEventType.ASSISTANT_REASONING_DELTA: RunEventEnum.REASONING,
    SessionEventType.ASSISTANT_MESSAGE_DELTA: RunEventEnum.RESPONSE,
    SessionEventType.TOOL_EXECUTION_START: RunEventEnum.FETCHING,
    SessionEventType.TOOL_EXECUTION_COMPLETE: RunEventEnum.THINKING,
}


@injectable(as_type=QueryService, qualifier="ollama")
class OllamaQuery(QueryService):
    """QueryService implementation for interacting with Ollama.

    Manages sessions, streams events from the Ollama SDK, and exposes run
    methods used by RunAgentPlugin to execute LLM queries.
    """

    def __init__(
        self,
        ollama_client: LLMClient,
        app_config: AppConfig | None = None,
        logger: LoggerService | None = None,
    ):
        self.client = ollama_client
        # Allow omission in tests; default to a basic AppConfig when not provided.
        self.app_config = app_config or AppConfig()
        self.logger_service = logger
        # Per-execution-model sessions so concurrent sub-executions don't share a session.
        self._model_sessions: dict[int, AgentSession] = {}
        self._session_lock = asyncio.Lock()

    async def execute_query(self, execution_model: ExecutionModel, params: str) -> str:
        """Execute a query using the Ollama client.

        Args:
            execution_model (ExecutionModel): The execution model for the current agent run.
            params (str): The query parameters for the execution model.
        """
        extra_tools: list[ToolDefinition] = []
        if execution_model.context.tools:
            extra_tools = convert_core_tool_to_ollama(execution_model.context.tools)

        session_tools = [SET_TOOL_DEFINITION, GET_TOOL_DEFINITION, *extra_tools]

        session = await self.create_session(execution_model, session_tools)

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
            provider="Ollama",
            status=RunStatus.RUNNING,
            start_time=datetime.now(UTC),
        )

        var_list = ""
        if len(execution_model.context.data.keys()) > 0:
            var_list = f"These are variable names that exist in state \n {execution_model.context.data.keys()}\n\n"

        result = ""
        try:
            async for event in session.send_and_stream_async(
                prompt=var_list + execution_model.context.window
            ):
                if event.type == SessionEventType.TOOL_EXECUTION_START:
                    await self.on_tool_start(event.metadata, run)
                elif event.type == SessionEventType.ASSISTANT_REASONING_DELTA:
                    await self.on_reasoning_delta(event.text, run)
                elif event.type == SessionEventType.ASSISTANT_STREAMING_DELTA:
                    await self.on_content_delta(event.text, run)
                    result += event.text
                elif event.type == SessionEventType.TOOL_EXECUTION_COMPLETE:
                    await self.on_tool_complete(event.metadata, run)
                elif event.type == SessionEventType.SESSION_SHUTDOWN:
                    await self.on_shutdown(run)
                elif event.type == SessionEventType.SESSION_START:
                    await self.on_session_start(event.metadata, run)

            if run.status != RunStatus.COMPLETED:
                run.end_time = datetime.now(UTC)
                run.status = RunStatus.COMPLETED
            if run.start_time and run.end_time:
                run.duration_ms = (run.end_time - run.start_time).total_seconds() * 1000

            if self.logger_service:
                self.logger_service.print(f"[Run completed] status={run.status.value}")

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

    async def on_session_start(self, metadata: SessionStartedMetadata, run: Run):
        run.session_id = metadata.id
        run.model = metadata.model_id

    async def on_content_delta(self, content_delta: str, run: Run) -> None:
        if run.responses is None:
            run.responses = [""]
        run.responses[-1] += content_delta
        if not run.content_blocks or run.content_blocks[-1].type != ContentBlockType.RESPONSE:
            run.content_blocks.append(ContentBlock(type=ContentBlockType.RESPONSE))
        run.content_blocks[-1].text += content_delta

    async def on_reasoning_delta(self, reasoning_delta: str, run: Run) -> None:
        if run.reasoning is None:
            run.reasoning = [""]
        run.reasoning[-1] += reasoning_delta
        if not run.content_blocks or run.content_blocks[-1].type != ContentBlockType.REASONING:
            run.content_blocks.append(ContentBlock(type=ContentBlockType.REASONING))
        run.content_blocks[-1].text += reasoning_delta

    async def on_tool_start(self, metadata: ToolCallCallingMetadata, run: Run):
        if metadata.name != "ask_user":
            run.tool_calls.append(
                ToolCall(
                    tool_call_id=metadata.tool_call_id,
                    tool_name=metadata.name,
                    arguments=metadata.arguments,
                )
            )
            run.content_blocks.append(
                ContentBlock(
                    type=ContentBlockType.TOOL_CALL,
                    ref=metadata.tool_call_id,
                )
            )

    async def on_tool_complete(self, metadata: ToolCallDoneMetadata, run: Run):
        for tc in reversed(run.tool_calls):
            if tc.tool_call_id == metadata.tool_call_id:
                tc.result = metadata.result if metadata.result else None
                tc.success = metadata.success
                if self.logger_service:
                    self.logger_service.print(f"[Tool call - {tc.tool_name}]: {tc.result}")
                break

    async def on_shutdown(self, run: Run):
        run.end_time = datetime.now(UTC)
        run.status = RunStatus.COMPLETED

    async def create_session(
        self, execution_model: ExecutionModel, extra_tools: list[ToolDefinition]
    ) -> AgentSession:
        model_id = id(execution_model)
        async with self._session_lock:
            session = AgentSession(
                model=LLMModelEnum.GEMMA_4_E2B,
                system_message=SYSTEM_PROMPT,
                additional_tools=extra_tools,
                on_user_input_request=OllamaUserInputHandler(execution_model),
                on_permission_request=OllamaPermissionHandler(execution_model, self.app_config),
                on_custom_tool_request=OllamaCustomToolHandler(execution_model),
            )
            self._model_sessions[model_id] = session

        session = self._model_sessions[model_id]
        return session

    async def clear_session(self):
        pass
