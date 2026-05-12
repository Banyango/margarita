import pytest
from click.testing import CliRunner

import margarita.agent.app.cli.agents.use as use_module
import margarita.agent.app.lifecycle as lifecycle_module
from margarita.agent.app.config import AppConfig, FeatureFlags
from margarita.agent.core.agents.models import ModelBackend


def _patch_lifecycle_with_noop(monkeypatch):
    async def _noop(_container):
        return None

    monkeypatch.setattr(lifecycle_module, "startup", _noop)
    monkeypatch.setattr(lifecycle_module, "shutdown", _noop)


def _patch_use_container_get(monkeypatch, config: AppConfig):
    async def _fake_get(interface, **kwargs):
        if interface is AppConfig:
            return config
        raise AssertionError(f"Unexpected container dependency: {interface}")

    monkeypatch.setattr(use_module.container, "get", _fake_get)


def _patch_save_app_config(monkeypatch):
    saved = []
    monkeypatch.setattr(use_module, "save_app_config", lambda c: saved.append(c))
    return saved


@pytest.mark.parametrize(
    "model_arg,expected_backend",
    [
        ("copilot", ModelBackend.COPILOT),
        ("ollama", ModelBackend.OLLAMA),
        ("claude", ModelBackend.CLAUDE),
    ],
)
def test_use_should_set_backend_for_valid_models(model_arg, expected_backend, monkeypatch):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    config = AppConfig()
    _patch_use_container_get(monkeypatch, config)
    saved = _patch_save_app_config(monkeypatch)
    runner = CliRunner()

    # Act
    result = runner.invoke(use_module.use, [model_arg])

    # Assert
    assert result.exit_code == 0
    assert f"Switched to {model_arg} backend" in result.output
    assert config.backend == expected_backend
    assert len(saved) == 1
    assert saved[0].backend == expected_backend


def test_use_should_set_backend_to_openai_when_feature_flag_is_enabled(monkeypatch):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    config = AppConfig(feature_flags=FeatureFlags(is_open_ai_api_enabled=True))
    _patch_use_container_get(monkeypatch, config)
    saved = _patch_save_app_config(monkeypatch)
    runner = CliRunner()

    # Act
    result = runner.invoke(use_module.use, ["openai"])

    # Assert
    assert result.exit_code == 0
    assert "Switched to openai backend" in result.output
    assert config.backend == ModelBackend.OPENAI
    assert saved[0].backend == ModelBackend.OPENAI


def test_use_should_fail_when_openai_is_requested_but_feature_flag_is_disabled(monkeypatch):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    config = AppConfig(feature_flags=FeatureFlags(is_open_ai_api_enabled=False))
    _patch_use_container_get(monkeypatch, config)
    saved = _patch_save_app_config(monkeypatch)
    runner = CliRunner()

    # Act
    result = runner.invoke(use_module.use, ["openai"])

    # Assert
    assert result.exit_code != 0
    assert len(saved) == 0


def test_use_should_fail_when_model_is_not_a_valid_choice(monkeypatch):
    # Arrange
    _patch_lifecycle_with_noop(monkeypatch)
    runner = CliRunner()

    # Act
    result = runner.invoke(use_module.use, ["unknown"])

    # Assert
    assert result.exit_code != 0
    assert len(result.output) > 0
