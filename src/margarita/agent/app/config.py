import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from wireup import injectable

from margarita.agent.core.agents.models import ModelBackend

class FeatureFlags(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    is_open_ai_api_enabled: bool = False

class AppConfig(BaseModel):
    show_context: bool = True
    theme: str = "monokai"
    use_existing_system_prompt: bool = True
    system_prompt: str = ""
    backend: ModelBackend = ModelBackend.OLLAMA
    ignore_permissions: bool = False
    feature_flags: FeatureFlags = FeatureFlags()


def _default_settings_path() -> Path:
    # Windows roaming app data
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "margarita" / "settings.json"

    # Fallback to a dotdir in the user's home (cross-platform)
    return Path.home() / ".margarita" / "settings.json"


def _create_default_settings_file(path: Path) -> AppConfig:
    path.parent.mkdir(parents=True, exist_ok=True)
    default_config = AppConfig()
    with path.open("w", encoding="utf-8") as f:
        json.dump(default_config.model_dump(), f, indent=4)
    return default_config


def save_app_config(config: AppConfig) -> None:
    path = _default_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=4)


@injectable
def get_app_config() -> AppConfig:
    path = Path(str(_default_settings_path()))
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return AppConfig.model_validate_json(f.read())
    else:
        return _create_default_settings_file(path)
