from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from click.testing import CliRunner

import margarita.agent.app.cli.agents.run as execute_module
import margarita.agent.app.lifecycle as lifecycle_module
from margarita.agent import Context, Memory
from margarita.agent.app.config import AppConfig
from margarita.agent.core.agents.services import MemoryService
from margarita.agent.core.interfaces.logger import LoggerService
from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.core.interfaces.query_service import QueryService
from margarita.agent.core.interfaces.ui import UI
from margarita.agent.entities.prompt_integrity import (
    DEFAULT_PROMPT_MANIFEST_CONTENT,
    PROMPT_MANIFEST_FILE_NAME,
    PromptIntegrityError,
)
from margarita.agent.libs.prompt_integrity.filesystem_integrity_service import (
    FilesystemPromptIntegrity,
)


def _patch_lifecycle_with_noop(monkeypatch):
    """Patch startup/shutdown so execute CLI tests avoid external network setup."""

    async def _noop(_container):
        return None

    monkeypatch.setattr(lifecycle_module, "startup", _noop)
    monkeypatch.setattr(lifecycle_module, "shutdown", _noop)


class _FakeMemoryService(MemoryService):
    async def save_memory(self, memory: Memory):
        pass

    async def load_memory(self, context: Context) -> Memory:
        return Memory(context)


def _patch_execute_container_get(monkeypatch, prompt_integrity=None):
    """Patch DI lookups for execute command and return requested interfaces."""
    requested_interfaces = []
    ui = MagicMock(spec=UI)
    query_service = AsyncMock(spec=QueryService)

    async def _fake_get(interface, **kwargs):
        requested_interfaces.append(interface)
        if interface is AppConfig:
            return AppConfig()
        if interface is UI:
            return ui
        if interface is Context:
            return Context()
        if interface is QueryService:
            return query_service
        if interface is LoggerService:
            logger_service = MagicMock()
            logger_service.print = MagicMock()
            return logger_service
        if interface is MemoryService:
            return _FakeMemoryService()
        if interface is PromptIntegrity:
            if prompt_integrity is None:
                raise AssertionError("PromptIntegrity was requested unexpectedly.")
            return prompt_integrity

        raise AssertionError(f"Unexpected container dependency: {interface}")

    monkeypatch.setattr(execute_module.container, "get", _fake_get)
    return requested_interfaces


def _create_prompt_integrity_mock_that_fails_preflight() -> MagicMock:
    """Create prompt-integrity mock that fails on global preflight check."""
    prompt_integrity = MagicMock(spec=PromptIntegrity)
    prompt_integrity.check_against_lock.side_effect = PromptIntegrityError(
        "global prompt drift detected"
    )
    return prompt_integrity


def _write_mgx_file(project_root: Path, file_name: str = "run.mgx") -> Path:
    """Create a minimal mgx file for execute CLI tests."""
    mgx_path = project_root / file_name
    mgx_path.write_text("")
    return mgx_path


def _patch_execute_operation_with_fake(monkeypatch):
    """Patch execute operation to isolate CLI verification branching behavior."""
    operation_calls: dict[str, dict] = {}

    class FakeExecuteAgentOperation:
        def __init__(self, **kwargs):
            operation_calls["init_kwargs"] = kwargs

        async def execute_async(self, mgx_file: str, base_path: Path | None = None):
            operation_calls["execute_async_kwargs"] = {
                "mgx_file": mgx_file,
                "base_path": base_path,
            }
            return None

    monkeypatch.setattr(execute_module, "ExecuteAgentOperation", FakeExecuteAgentOperation)
    return operation_calls


def test_execute_should_fail_when_prompt_verification_is_enabled_and_manifest_is_missing(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    requested_interfaces = _patch_execute_container_get(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path), "--verify-prompts"])

    # Assert
    assert result.exit_code != 0
    assert (
        f"Prompt verification is enabled, but '{PROMPT_MANIFEST_FILE_NAME}' was not found."
        in result.output
    )
    assert PromptIntegrity not in requested_interfaces


def test_execute_should_fail_when_manifest_exists_and_lock_file_is_missing_in_auto_verify_mode(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    requested_interfaces = _patch_execute_container_get(
        monkeypatch=monkeypatch,
        prompt_integrity=FilesystemPromptIntegrity(),
    )
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    (tmp_path / PROMPT_MANIFEST_FILE_NAME).write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path)])

    # Assert
    assert result.exit_code != 0
    assert "Prompt lock 'prompts.lock.json' was not found." in result.output
    assert PromptIntegrity in requested_interfaces


def test_execute_should_skip_prompt_verification_when_manifest_is_missing_and_auto_mode_is_used(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    requested_interfaces = _patch_execute_container_get(monkeypatch)
    operation_calls = _patch_execute_operation_with_fake(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path)])

    # Assert
    assert result.exit_code == 0
    assert PromptIntegrity not in requested_interfaces
    assert operation_calls["init_kwargs"]["prompt_integrity"] is None


def test_execute_should_skip_prompt_verification_when_no_verify_prompts_flag_is_used(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    requested_interfaces = _patch_execute_container_get(monkeypatch)
    operation_calls = _patch_execute_operation_with_fake(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    (tmp_path / PROMPT_MANIFEST_FILE_NAME).write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path), "--no-verify-prompts"])

    # Assert
    assert result.exit_code == 0
    assert PromptIntegrity not in requested_interfaces
    assert operation_calls["init_kwargs"]["prompt_integrity"] is None


def test_execute_should_fail_when_preflight_prompt_integrity_check_detects_global_drift(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    prompt_integrity = _create_prompt_integrity_mock_that_fails_preflight()
    requested_interfaces = _patch_execute_container_get(
        monkeypatch, prompt_integrity=prompt_integrity
    )
    operation_calls = _patch_execute_operation_with_fake(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    (tmp_path / PROMPT_MANIFEST_FILE_NAME).write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path)])

    # Assert
    assert result.exit_code != 0
    assert "global prompt drift detected" in result.output
    assert PromptIntegrity in requested_interfaces
    prompt_integrity.load_policy.assert_called_once()
    prompt_integrity.check_against_lock.assert_called_once()
    assert "init_kwargs" not in operation_calls


def test_execute_should_fail_when_any_tracked_prompt_has_drift_even_when_not_included(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    operation_calls = _patch_execute_operation_with_fake(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    (tmp_path / PROMPT_MANIFEST_FILE_NAME).write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    tracked_file = prompts_dir / "base.mg"
    tracked_file.write_text("<<original>>")
    prompt_integrity = FilesystemPromptIntegrity()
    prompt_integrity.scan_and_lock()
    tracked_file.write_text("<<tampered>>")
    requested_interfaces = _patch_execute_container_get(
        monkeypatch, prompt_integrity=prompt_integrity
    )
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path)])

    # Assert
    assert result.exit_code != 0
    assert "Prompt hash mismatch" in result.output
    assert PromptIntegrity in requested_interfaces
    assert "init_kwargs" not in operation_calls


def test_execute_should_pass_when_verify_prompts_is_explicitly_enabled_and_lock_is_valid(
    tmp_path, monkeypatch
):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    operation_calls = _patch_execute_operation_with_fake(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()

    (tmp_path / PROMPT_MANIFEST_FILE_NAME).write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "base.mg").write_text("<<base>>")

    prompt_integrity = FilesystemPromptIntegrity()
    prompt_integrity.scan_and_lock()
    requested_interfaces = _patch_execute_container_get(
        monkeypatch, prompt_integrity=prompt_integrity
    )
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path), "--verify-prompts"])

    # Assert
    assert result.exit_code == 0
    assert PromptIntegrity in requested_interfaces
    assert operation_calls["init_kwargs"]["prompt_integrity"] is prompt_integrity


def test_execute_should_pass_allow_unverified_to_operation_when_flag_is_set(tmp_path, monkeypatch):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    operation_calls = _patch_execute_operation_with_fake(monkeypatch)
    requested_interfaces = _patch_execute_container_get(monkeypatch)
    monkeypatch.chdir(tmp_path)
    sut = execute_module.run
    runner = CliRunner()
    mgx_path = _write_mgx_file(tmp_path)

    # Act
    result = runner.invoke(sut, [str(mgx_path), "--allow-unverified"])

    # Assert
    assert result.exit_code == 0
    assert PromptIntegrity not in requested_interfaces
    assert operation_calls["init_kwargs"]["allow_unverified"] is True
