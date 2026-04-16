import hashlib
import json
from pathlib import Path

import tomllib
from wireup import injectable

from margarita.agent.core.interfaces.prompt_integrity import PromptIntegrity
from margarita.agent.entities.prompt_integrity import (
    PROMPT_HASH_ALGORITHM,
    PROMPT_LOCK_FILE_NAME,
    PROMPT_LOCK_VERSION,
    PROMPT_MANIFEST_FILE_NAME,
    PROMPT_MANIFEST_VERSION,
    TRACKED_PROMPT_EXTENSIONS,
    PromptHashMismatchError,
    PromptIntegrityError,
    PromptLock,
    PromptManifest,
    PromptMissingLockError,
    PromptUnverifiedPathError,
)


@injectable(as_type=PromptIntegrity)
class FilesystemPromptIntegrity(PromptIntegrity):
    """Verify prompt files against a manifest+lock policy on the local filesystem."""

    # Contract guards for deterministic verification.
    # Version fields fail fast on schema drift (future v2 manifest/lock formats),
    # and HASH_ALGORITHM prevents silent algorithm mismatches across environments.
    MANIFEST_VERSION = PROMPT_MANIFEST_VERSION
    LOCK_VERSION = PROMPT_LOCK_VERSION
    HASH_ALGORITHM = PROMPT_HASH_ALGORITHM

    def __init__(self):
        """Initialize policy file paths, parsed policy state, and in-run hash cache."""
        self._manifest_path = Path(PROMPT_MANIFEST_FILE_NAME)
        self._lock_path = Path(PROMPT_LOCK_FILE_NAME)
        self._manifest: PromptManifest | None = None
        self._lock: PromptLock | None = None
        self._trusted_root: Path | None = None
        self._verified_cache: dict[str, str] = {}

    def load_policy(self, manifest_path: Path, lock_path: Path):
        """Load manifest+lock files and validate policy compatibility."""
        self._manifest_path = Path(manifest_path).resolve(strict=False)
        self._lock_path = Path(lock_path).resolve(strict=False)
        self._manifest = self._read_manifest()
        self._trusted_root = (self._manifest_path.parent / self._manifest.root).resolve(
            strict=False
        )
        self._ensure_trusted_root_exists()

        self._lock = self._read_lock()
        self._validate_manifest_hash()
        self._validated_lock_metadata()
        self._verified_cache.clear()

    def verify_trusted_path(self, path: Path):
        """Reject include paths that resolve outside the trusted prompt root."""
        self._ensure_loaded(require_lock=True)
        candidate = Path(path).resolve(strict=False)
        if not self._is_under_trusted_root(candidate):
            raise PromptUnverifiedPathError(
                f"Include path '{candidate}' is outside trusted prompt root '{self._trusted_root}'."
            )

    def verify_bytes(self, path: Path, content_bytes: bytes):
        """Verify tracked prompt bytes against the lock entry for the resolved path."""
        self._ensure_loaded(require_lock=True)
        candidate = Path(path).resolve(strict=False)
        self.verify_trusted_path(candidate)

        if candidate.suffix not in TRACKED_PROMPT_EXTENSIONS:
            return

        relative_path = candidate.relative_to(self._trusted_root).as_posix()
        if not self._lock:
            raise PromptIntegrityError("Prompt lock is not loaded.")

        expected_hash = self._lock.files.get(relative_path)
        if expected_hash is None:
            raise PromptMissingLockError(
                f"Prompt '{relative_path}' is missing from '{self._lock_path.name}'."
            )

        actual_hash = self._hash_bytes(content_bytes)
        cache_key = str(candidate)
        if self._verified_cache.get(cache_key) == actual_hash:
            return

        if expected_hash != actual_hash:
            raise PromptHashMismatchError(
                f"Prompt hash mismatch for '{relative_path}'. Expected {expected_hash}, got {actual_hash}."
            )

        self._verified_cache[cache_key] = actual_hash

    def scan_and_lock(self) -> PromptLock:
        """Scan tracked prompts, hash them deterministically, and write lock file."""
        # Re-read manifest/root every lock run to avoid stale cached state when one service
        # instance is reused across different command invocations or working directories.
        self._manifest = self._read_manifest()
        self._trusted_root = (self._manifest_path.parent / self._manifest.root).resolve(
            strict=False
        )
        self._ensure_trusted_root_exists()
        tracked_files = self._scan_tracked_files()
        file_hashes = {
            relative_path: self._hash_bytes(path.read_bytes())
            for relative_path, path in tracked_files.items()
        }

        if not self._manifest:
            raise PromptIntegrityError("Prompt manifest is not loaded.")

        lock = PromptLock(
            version=self.LOCK_VERSION,
            algorithm=self.HASH_ALGORITHM,
            manifest_sha256=self._hash_bytes(self._manifest_path.read_bytes()),
            root=self._manifest.root,
            files=dict(sorted(file_hashes.items())),
        )

        payload = {
            "algorithm": lock.algorithm,
            "files": lock.files,
            "manifest_sha256": lock.manifest_sha256,
            "root": lock.root,
            "version": lock.version,
        }
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

        self._lock = lock
        self._verified_cache.clear()
        return lock

    def check_against_lock(self):
        """Fail when tracked files drift from lock or lock contains stale entries."""
        self._ensure_loaded(require_lock=True)
        if not self._lock:
            raise PromptIntegrityError("Prompt lock is not loaded.")

        tracked_files = self._scan_tracked_files()
        tracked_keys = set(tracked_files.keys())
        locked_keys = set(self._lock.files.keys())

        missing_in_lock = sorted(tracked_keys - locked_keys)
        if missing_in_lock:
            raise PromptMissingLockError(
                f"Lock file '{self._lock_path.name}' is missing tracked prompts: {', '.join(missing_in_lock)}."
            )

        stale_entries = sorted(locked_keys - tracked_keys)
        if stale_entries:
            raise PromptIntegrityError(
                f"Lock file '{self._lock_path.name}' has stale entries: {', '.join(stale_entries)}."
            )

        for relative_path in sorted(tracked_files.keys()):
            path = tracked_files[relative_path]
            self.verify_bytes(path=path, content_bytes=path.read_bytes())

    def _ensure_loaded(self, require_lock: bool):
        """Lazily load manifest/lock policy and validate root before verification."""
        if self._manifest is None or self._trusted_root is None:
            self._manifest = self._read_manifest()
            self._trusted_root = (self._manifest_path.parent / self._manifest.root).resolve(
                strict=False
            )

        self._ensure_trusted_root_exists()

        if require_lock and self._lock is None:
            self._lock = self._read_lock()
            self._validate_manifest_hash()
            self._validated_lock_metadata()

    def _ensure_trusted_root_exists(self):
        """Validate trusted root path exists and is a directory."""
        if (
            not self._trusted_root
            or not self._trusted_root.exists()
            or not self._trusted_root.is_dir()
        ):
            raise PromptIntegrityError(
                f"Prompt root '{self._trusted_root}' does not exist or is not a directory."
            )

    def _read_manifest(self) -> PromptManifest:
        """Read and validate manifest schema from prompts.toml."""
        if not self._manifest_path.exists():
            raise PromptIntegrityError(
                f"Prompt manifest '{self._manifest_path.name}' was not found."
            )

        raw = self._manifest_path.read_bytes()
        try:
            data = tomllib.loads(raw.decode("utf-8"))
        except Exception as error:
            raise PromptIntegrityError(
                f"Failed to parse manifest '{self._manifest_path.name}': {error}"
            ) from error

        version = data.get("version")
        root = data.get("root")
        include = data.get("include")
        exclude = data.get("exclude", [])

        if version != self.MANIFEST_VERSION:
            raise PromptIntegrityError(
                f"Unsupported manifest version '{version}'. Expected {self.MANIFEST_VERSION}."
            )
        if not isinstance(root, str) or not root:
            raise PromptIntegrityError("Manifest field 'root' must be a non-empty string.")
        if not isinstance(include, list) or not all(
            isinstance(item, str) and item for item in include
        ):
            raise PromptIntegrityError("Manifest field 'include' must be a list of strings.")
        if not isinstance(exclude, list) or not all(
            isinstance(item, str) and item for item in exclude
        ):
            raise PromptIntegrityError("Manifest field 'exclude' must be a list of strings.")

        return PromptManifest(
            version=version,
            root=root,
            include=include,
            exclude=exclude,
        )

    def _read_lock(self) -> PromptLock:
        """Read and minimally validate lock schema from prompts.lock.json."""
        if not self._lock_path.exists():
            raise PromptMissingLockError(f"Prompt lock '{self._lock_path.name}' was not found.")

        try:
            data = json.loads(self._lock_path.read_text())
        except json.JSONDecodeError as error:
            raise PromptIntegrityError(
                f"Failed to parse lock file '{self._lock_path.name}': {error}"
            ) from error

        files = data.get("files")
        if not isinstance(files, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in files.items()
        ):
            raise PromptIntegrityError("Lock field 'files' must be a mapping of string hashes.")

        return PromptLock(
            version=data.get("version"),
            algorithm=data.get("algorithm"),
            manifest_sha256=data.get("manifest_sha256"),
            root=data.get("root"),
            files=files,
        )

    def _scan_tracked_files(self) -> dict[str, Path]:
        """Resolve and filter manifest-matched prompt files under trusted root."""
        if not self._manifest or not self._trusted_root:
            raise PromptIntegrityError("Manifest is not loaded.")

        tracked: dict[str, Path] = {}
        for pattern in self._manifest.include:
            for candidate in self._trusted_root.glob(pattern):
                if not candidate.is_file():
                    continue

                resolved_candidate = candidate.resolve(strict=False)
                if not self._is_under_trusted_root(resolved_candidate):
                    raise PromptUnverifiedPathError(
                        f"Manifest pattern '{pattern}' resolved outside trusted prompt root "
                        f"'{self._trusted_root}': '{resolved_candidate}'."
                    )
                if resolved_candidate.suffix not in TRACKED_PROMPT_EXTENSIONS:
                    continue

                relative_path = resolved_candidate.relative_to(self._trusted_root).as_posix()
                if self._matches_any(relative_path, self._manifest.exclude):
                    continue
                tracked[relative_path] = resolved_candidate

        return dict(sorted(tracked.items()))

    @staticmethod
    def _hash_bytes(content: bytes) -> str:
        """Return normalized sha256 digest string for content bytes."""
        return f"sha256:{hashlib.sha256(content).hexdigest()}"

    def _is_under_trusted_root(self, candidate: Path) -> bool:
        """Return True when candidate path is within trusted root."""
        if not self._trusted_root:
            return False
        try:
            candidate.relative_to(self._trusted_root)
            return True
        except ValueError:
            return False

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        """Match glob pattern with fallback for '**/' compatibility behavior."""
        candidate = Path(path)
        if candidate.match(pattern):
            return True
        if pattern.startswith("**/"):
            return candidate.match(pattern[3:])
        return False

    def _matches_any(self, path: str, patterns: list[str]) -> bool:
        """Return True when path matches any manifest exclude pattern."""
        return any(self._match_pattern(path, pattern) for pattern in patterns)

    def _validate_manifest_hash(self):
        """Ensure lock references the exact manifest bytes loaded for this run."""
        if not self._lock:
            raise PromptIntegrityError("Prompt lock is not loaded.")

        actual_manifest_hash = self._hash_bytes(self._manifest_path.read_bytes())
        if self._lock.manifest_sha256 != actual_manifest_hash:
            raise PromptIntegrityError(
                f"Manifest hash mismatch between '{self._manifest_path.name}' and "
                f"'{self._lock_path.name}'. Re-run prompt lock generation."
            )

    def _validated_lock_metadata(self):
        """Validate lock metadata consistency with expected versions and manifest root."""
        if not self._lock or not self._manifest:
            raise PromptIntegrityError("Prompt policy files are not loaded.")

        if self._lock.version != self.LOCK_VERSION:
            raise PromptIntegrityError(
                f"Unsupported lock version '{self._lock.version}'. Expected {self.LOCK_VERSION}."
            )
        if self._lock.algorithm != self.HASH_ALGORITHM:
            raise PromptIntegrityError(
                f"Unsupported hash algorithm '{self._lock.algorithm}'. Expected '{self.HASH_ALGORITHM}'."
            )
        if self._lock.root != self._manifest.root:
            raise PromptIntegrityError(
                f"Lock root '{self._lock.root}' does not match manifest root '{self._manifest.root}'."
            )
