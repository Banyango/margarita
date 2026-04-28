import asyncio
import sys
from pathlib import Path

import click

from margarita.agent.app.config import AppConfig
from margarita.agent.app.container import container
from margarita.agent.app.lifecycle import with_lifecycle
from margarita.agent.core.agents.models import ExecutionModel
from margarita.agent.core.agents.operations.execute_agent_operation import ExecuteAgentOperation
from margarita.agent.core.agents.plugins import ExecPlugin
from margarita.agent.core.agents.plugins.console import ConsoleLogPlugin
from margarita.agent.core.agents.plugins.context import ContextPlugin
from margarita.agent.core.agents.plugins.func import FuncPlugin
from margarita.agent.core.agents.plugins.input import InputPlugin
from margarita.agent.core.agents.plugins.run_agent import RunAgentPlugin
from margarita.agent.core.agents.plugins.stop import StopPlugin
from margarita.agent.core.agents.plugins.tools import ToolsPlugin
from margarita.agent.core.agents.services.memory import MemoryService
from margarita.agent.core.interfaces.agent_plugin import AgentPlugin
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.core.interfaces.query_service import QueryService
from margarita.agent.core.interfaces.ui import UI
from margarita.agent.entities.prompt_integrity import (
    PROMPT_LOCK_FILE_NAME,
    PROMPT_MANIFEST_FILE_NAME,
    PromptIntegrityError,
)
from margarita.agent.entities.run import StopError


def make_plugins(
    query_service: QueryService,
    logger_service: LoggerService,
    memory_service: MemoryService,
    prompt_integrity: PromptIntegrity | None,
    allow_unverified: bool,
) -> list[AgentPlugin]:
    return [
        RunAgentPlugin(agent_service=query_service),
        FuncPlugin(),
        ToolsPlugin(),
        ContextPlugin(),
        ConsoleLogPlugin(logger_service=logger_service),
        InputPlugin(),
        StopPlugin(),
        ExecPlugin(
            plugin_factory=lambda: make_plugins(
                query_service, logger_service, memory_service, prompt_integrity, allow_unverified
            ),
            memory_service=memory_service,
            prompt_integrity=prompt_integrity,
            allow_unverified=allow_unverified,
        ),
    ]


@click.command()
@click.argument("file_name", type=str)
@click.option("--verify-prompts/--no-verify-prompts", default=None)
@click.option("--allow-unverified", is_flag=True, default=False)
@click.option("--headless/--no-headless", default=False)
@with_lifecycle
async def run(
    file_name: str, verify_prompts: bool | None, allow_unverified: bool, headless: bool
) -> None:
    """Execute an .mgx file with optional prompt integrity verification.

    Args:
        file_name (str): The path to the .mgx file.
        verify_prompts: Explicitly enable/disable prompt verification.
        allow_unverified: If True, allow unverified includes with a warning.
    """
    if not Path(file_name).is_file():
        raise click.ClickException(f"File '{file_name}' does not exist.")

    base_path = Path(file_name).parent
    manifest_path = Path(PROMPT_MANIFEST_FILE_NAME)
    lock_path = Path(PROMPT_LOCK_FILE_NAME)
    has_manifest = manifest_path.exists()

    should_verify_prompts = verify_prompts if verify_prompts is not None else has_manifest

    ui = await container.get(UI)
    # retrieve AppConfig to ensure it's initialized in the container, but we don't need to keep a reference
    config = await container.get(AppConfig)
    query_service = await container.get(QueryService, qualifier=config.backend)
    logger_service = await container.get(LoggerService)
    memory_service = await container.get(MemoryService)
    prompt_integrity = None

    if should_verify_prompts:
        if not has_manifest:
            raise click.ClickException(
                f"Prompt verification is enabled, but '{PROMPT_MANIFEST_FILE_NAME}' was not found."
            )

        prompt_integrity = await container.get(PromptIntegrity)
        try:
            prompt_integrity.load_policy(manifest_path=manifest_path, lock_path=lock_path)
            prompt_integrity.check_against_lock()
        except PromptIntegrityError as error:
            raise click.ClickException(str(error)) from error

    with open(file_name) as f:
        mgx_code = f.read()

        model = ExecutionModel()

        operation = ExecuteAgentOperation(
            plugins=make_plugins(
                query_service, logger_service, memory_service, prompt_integrity, allow_unverified
            ),
            memory_service=memory_service,
            execution_model=model,
            prompt_integrity=prompt_integrity,
            allow_unverified=allow_unverified,
        )

        ui_task = None
        if not headless:
            ui_task = asyncio.create_task(ui.render_ui(model))

        try:
            await operation.execute_async(mgx_file=mgx_code, base_path=base_path)
        except (PromptIntegrityError, ValueError, FileNotFoundError) as error:
            raise click.ClickException(str(error)) from error
        except StopError as stop_error:
            raise click.ClickException(str(stop_error)) from stop_error

        # Prevent hanging in headless mode if the run requires user input or permission
        if headless and (model.pending_input is not None or model.pending_permission is not None):
            # mark done and exit with distinct code to indicate interactive prompt required
            model.done = True
            sys.exit(2)

        if ui_task is not None:
            await ui_task
