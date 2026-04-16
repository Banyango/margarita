from dataclasses import dataclass

TRACKED_PROMPT_EXTENSIONS = frozenset({".mg", ".mgx"})
PROMPT_MANIFEST_FILE_NAME = "prompts.toml"
PROMPT_LOCK_FILE_NAME = "prompts.lock.json"
PROMPT_MANIFEST_VERSION = 1
PROMPT_LOCK_VERSION = 1
PROMPT_HASH_ALGORITHM = "sha256"
DEFAULT_PROMPT_ROOT = "prompts"
DEFAULT_PROMPT_INCLUDE_PATTERNS = ("**/*.mg", "**/*.mgx")
DEFAULT_PROMPT_EXCLUDE_PATTERNS = ()
_DEFAULT_PROMPT_INCLUDE_SERIALIZED = ", ".join(
    f'"{pattern}"' for pattern in DEFAULT_PROMPT_INCLUDE_PATTERNS
)
_DEFAULT_PROMPT_EXCLUDE_SERIALIZED = ", ".join(
    f'"{pattern}"' for pattern in DEFAULT_PROMPT_EXCLUDE_PATTERNS
)
DEFAULT_PROMPT_MANIFEST_CONTENT = (
    f"version = {PROMPT_MANIFEST_VERSION}\n"
    f'root = "{DEFAULT_PROMPT_ROOT}"\n'
    f"include = [{_DEFAULT_PROMPT_INCLUDE_SERIALIZED}]\n"
    f"exclude = [{_DEFAULT_PROMPT_EXCLUDE_SERIALIZED}]\n"
)


@dataclass(frozen=True)
class PromptManifest:
    """Metadata manifest describing a prompt file included in execution.

    Attributes:
        path: Filesystem path of the prompt file.
        hash: Content hash used for integrity verification.
    """

    version: int
    root: str
    include: list[str]
    exclude: list[str]


@dataclass(frozen=True)
class PromptLock:
    """Represents a lock placed on a prompt to prevent concurrent modification.

    Attributes:
        owner: Identifier of the entity holding the lock.
        timestamp: Time when the lock was acquired.
    """

    version: int
    algorithm: str
    manifest_sha256: str
    root: str
    files: dict[str, str]


class PromptIntegrityError(Exception):
    """Base exception for prompt integrity verification failures."""


class PromptHashMismatchError(PromptIntegrityError):
    """Raised when a prompt file hash does not match the lock file."""


class PromptMissingLockError(PromptIntegrityError):
    """Raised when verification is required but the lock file is missing."""


class PromptUnverifiedPathError(PromptIntegrityError):
    """Raised when a file path is outside the trusted prompt root."""
