"""
Integration tests for prompt integrity DI wiring and end-to-end verification.

Verifies that PromptIntegrity resolves through the container and can execute
scan->load->check with real filesystem artifacts.

Prerequisites:
- None

Usage:
    uv run pytest -q test/integration/test_prompt_integrity_integration.py
"""

import asyncio

from margarita.agent.app.container import container
from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.entities.prompt_integrity import (
    DEFAULT_PROMPT_MANIFEST_CONTENT,
    PROMPT_LOCK_FILE_NAME,
    PROMPT_MANIFEST_FILE_NAME,
)


def test_container_get_should_resolve_prompt_integrity_and_verify_prompts_when_requested(
    tmp_path, monkeypatch
):
    # Arrange
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / PROMPT_MANIFEST_FILE_NAME).write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    (prompts_dir / "base.mg").write_text("<<base>>")
    monkeypatch.chdir(tmp_path)

    # Act
    sut = asyncio.run(container.get(PromptIntegrity))
    lock = sut.scan_and_lock()
    sut.load_policy(
        manifest_path=tmp_path / PROMPT_MANIFEST_FILE_NAME,
        lock_path=tmp_path / PROMPT_LOCK_FILE_NAME,
    )
    sut.check_against_lock()

    # Assert
    assert set(lock.files.keys()) == {"base.mg"}
