import hashlib
import json
from pathlib import Path

from click.testing import CliRunner

from margarita.agent.app.cli.prompts import commands as prompts_module
from margarita.agent.entities.prompt_integrity import (
    DEFAULT_PROMPT_MANIFEST_CONTENT,
    PromptIntegrityError,
)
from margarita.agent.libs.prompt_integrity.filesystem_integrity_service import (
    FilesystemPromptIntegrity,
)


def _create_prompt_project(project_root: Path):
    """Create a minimal prompt project with one tracked template."""
    prompts_dir = project_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (project_root / "prompts.toml").write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    (prompts_dir / "base.mg").write_text("<<base>>")


def _patch_prompt_integrity_resolution_with_filesystem_service(monkeypatch):
    """Resolve prompt-integrity service to concrete filesystem implementation for CLI tests."""
    monkeypatch.setattr(
        prompts_module,
        "_resolve_prompt_integrity_service",
        lambda: FilesystemPromptIntegrity(),
    )


def test_init_prompts_should_create_default_manifest_when_manifest_is_missing(
    tmp_path, monkeypatch
):
    # Arrange
    monkeypatch.chdir(tmp_path)
    sut = prompts_module.prompts
    runner = CliRunner()

    # Act
    result = runner.invoke(sut, ["init"])

    # Assert
    assert result.exit_code == 0
    assert (tmp_path / "prompts.toml").read_text() == DEFAULT_PROMPT_MANIFEST_CONTENT


def test_lock_prompts_should_generate_lock_file_when_project_has_manifest_and_prompts(
    tmp_path, monkeypatch
):
    # Arrange
    _create_prompt_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    _patch_prompt_integrity_resolution_with_filesystem_service(monkeypatch)
    sut = prompts_module.prompts
    runner = CliRunner()

    # Act
    result = runner.invoke(sut, ["lock"])

    # Assert
    assert result.exit_code == 0
    assert (tmp_path / "prompts.lock.json").exists()
    assert "tracked prompt files" in result.output


def test_check_prompts_should_fail_when_tracked_prompt_hash_has_drifted(tmp_path, monkeypatch):
    # Arrange
    _create_prompt_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    _patch_prompt_integrity_resolution_with_filesystem_service(monkeypatch)
    sut = prompts_module.prompts
    runner = CliRunner()
    lock_result = runner.invoke(sut, ["lock"])
    assert lock_result.exit_code == 0
    (tmp_path / "prompts" / "base.mg").write_text("<<tampered>>")

    # Act
    result = runner.invoke(sut, ["check"])

    # Assert
    assert result.exit_code != 0
    assert "Prompt hash mismatch" in result.output


def test_lock_prompts_should_use_current_working_directory_when_service_instance_is_reused(
    tmp_path, monkeypatch
):
    # Arrange
    service = FilesystemPromptIntegrity()
    monkeypatch.setattr(prompts_module, "_resolve_prompt_integrity_service", lambda: service)
    sut = prompts_module.prompts
    runner = CliRunner()

    first_project = tmp_path / "first"
    second_project = tmp_path / "second"
    first_project.mkdir(parents=True, exist_ok=True)
    second_project.mkdir(parents=True, exist_ok=True)

    _create_prompt_project(first_project)
    _create_prompt_project(second_project)
    (first_project / "prompts" / "base.mg").write_text("<<first>>")
    (second_project / "prompts" / "base.mg").write_text("<<second>>")

    # Act
    monkeypatch.chdir(first_project)
    first_result = runner.invoke(sut, ["lock"])

    monkeypatch.chdir(second_project)
    second_result = runner.invoke(sut, ["lock"])

    # Assert
    assert first_result.exit_code == 0
    assert second_result.exit_code == 0

    second_lock_payload = json.loads((second_project / "prompts.lock.json").read_text())
    second_file_hash = second_lock_payload["files"]["base.mg"]
    expected_second_hash = f"sha256:{hashlib.sha256(b'<<second>>').hexdigest()}"
    assert second_file_hash == expected_second_hash


def test_check_prompts_should_pass_when_tracked_prompts_match_lock(tmp_path, monkeypatch):
    # Arrange
    _create_prompt_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    _patch_prompt_integrity_resolution_with_filesystem_service(monkeypatch)
    sut = prompts_module.prompts
    runner = CliRunner()
    lock_result = runner.invoke(sut, ["lock"])
    assert lock_result.exit_code == 0

    # Act
    result = runner.invoke(sut, ["check"])

    # Assert
    assert result.exit_code == 0
    assert "Prompt integrity check passed." in result.output


def test_init_prompts_should_fail_when_manifest_exists_and_force_flag_is_not_provided(
    tmp_path, monkeypatch
):
    # Arrange
    monkeypatch.chdir(tmp_path)
    sut = prompts_module.prompts
    (tmp_path / "prompts.toml").write_text("version = 1\n")
    runner = CliRunner()

    # Act
    result = runner.invoke(sut, ["init"])

    # Assert
    assert result.exit_code != 0
    assert "already exists. Use --force to overwrite it." in result.output


def test_init_prompts_should_overwrite_manifest_when_force_flag_is_provided(tmp_path, monkeypatch):
    # Arrange
    monkeypatch.chdir(tmp_path)
    sut = prompts_module.prompts
    manifest_path = tmp_path / "prompts.toml"
    manifest_path.write_text('version = 1\nroot = "custom"\n')
    runner = CliRunner()

    # Act
    result = runner.invoke(sut, ["init", "--force"])

    # Assert
    assert result.exit_code == 0
    assert manifest_path.read_text() == DEFAULT_PROMPT_MANIFEST_CONTENT


def test_lock_prompts_should_fail_with_click_error_when_integrity_service_raises_prompt_integrity_error(
    tmp_path, monkeypatch
):
    # Arrange
    _create_prompt_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    sut = prompts_module.prompts

    class FailingPromptIntegrityService:
        def scan_and_lock(self):
            raise PromptIntegrityError("scan failure")

    monkeypatch.setattr(
        prompts_module,
        "_resolve_prompt_integrity_service",
        lambda: FailingPromptIntegrityService(),
    )
    runner = CliRunner()

    # Act
    result = runner.invoke(sut, ["lock"])

    # Assert
    assert result.exit_code != 0
    assert "scan failure" in result.output
