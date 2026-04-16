import asyncio
from pathlib import Path

import click

from margarita.agent.app.container import container
from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.entities.prompt_integrity import (
    DEFAULT_PROMPT_MANIFEST_CONTENT,
    PROMPT_LOCK_FILE_NAME,
    PROMPT_MANIFEST_FILE_NAME,
    PromptIntegrityError,
)

PROMPT_MANIFEST_PATH = Path(PROMPT_MANIFEST_FILE_NAME)
PROMPT_LOCK_PATH = Path(PROMPT_LOCK_FILE_NAME)


def _resolve_prompt_integrity_service() -> PromptIntegrity:
    return asyncio.run(container.get(PromptIntegrity))


@click.group()
def prompts():
    """Manage prompt integrity manifests and lock files."""


@prompts.command("init")
@click.option("--force", is_flag=True, default=False)
def init_prompts(force: bool):
    """Create the default prompts.toml manifest."""
    if PROMPT_MANIFEST_PATH.exists() and not force:
        raise click.ClickException(
            f"Manifest '{PROMPT_MANIFEST_PATH}' already exists. Use --force to overwrite it."
        )

    PROMPT_MANIFEST_PATH.write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    click.echo(f"Created '{PROMPT_MANIFEST_PATH}'.")


@prompts.command("lock")
def lock_prompts():
    """Generate prompts.lock.json from prompts.toml."""
    service = _resolve_prompt_integrity_service()

    try:
        lock = service.scan_and_lock()
    except PromptIntegrityError as error:
        raise click.ClickException(str(error)) from error

    click.echo(f"Generated '{PROMPT_LOCK_PATH}' with {len(lock.files)} tracked prompt files.")


@prompts.command("check")
def check_prompts():
    """Verify prompt files against prompts.lock.json."""
    service = _resolve_prompt_integrity_service()

    try:
        service.load_policy(manifest_path=PROMPT_MANIFEST_PATH, lock_path=PROMPT_LOCK_PATH)
        service.check_against_lock()
    except PromptIntegrityError as error:
        raise click.ClickException(str(error)) from error

    click.echo("Prompt integrity check passed.")
