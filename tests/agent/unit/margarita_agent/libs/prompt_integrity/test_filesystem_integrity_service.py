import json

import pytest

from margarita.agent.entities.prompt_integrity import (
    DEFAULT_PROMPT_MANIFEST_CONTENT,
    PromptHashMismatchError,
    PromptIntegrityError,
    PromptMissingLockError,
    PromptUnverifiedPathError,
)
from margarita.agent.libs.prompt_integrity.filesystem_integrity_service import (
    FilesystemPromptIntegrity,
)


def _write_default_project(tmp_path):
    """Create a minimal prompts project with tracked and untracked file types."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "prompts.toml").write_text(DEFAULT_PROMPT_MANIFEST_CONTENT)
    (prompts_dir / "setup.mg").write_text("<<hello>>")
    (prompts_dir / "setup.md").write_text("# hello")
    (prompts_dir / "ignored.txt").write_text("ignore")
    (prompts_dir / "included.mgx").write_text("included")
    nested = prompts_dir / "salt"
    nested.mkdir(parents=True, exist_ok=True)
    (nested / "template.mg").write_text("<<nested>>")


def _create_service_in_project_dir(tmp_path, monkeypatch):
    """Create the integrity service after setting up and switching to a temp project."""
    _write_default_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    return FilesystemPromptIntegrity()


def test_scan_and_lock_should_track_only_prompt_templates_when_manifest_is_default(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)

    # Act
    lock = sut.scan_and_lock()

    # Assert
    assert set(lock.files.keys()) == {"salt/template.mg", "setup.mg", "included.mgx"}


def test_scan_and_lock_should_write_stable_lock_content_when_called_twice_without_changes(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)

    # Act
    sut.scan_and_lock()
    lock_file_content_one = (tmp_path / "prompts.lock.json").read_text()
    sut.scan_and_lock()
    lock_file_content_two = (tmp_path / "prompts.lock.json").read_text()

    # Assert
    assert lock_file_content_one == lock_file_content_two


def test_load_policy_should_raise_prompt_integrity_error_when_manifest_hash_differs_from_lock(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()

    (tmp_path / "prompts.toml").write_text(
        'version = 1\nroot = "prompts"\ninclude = ["**/*.mg"]\nexclude = []\n'
    )

    reloaded_sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match="Manifest hash mismatch"):
        reloaded_sut.load_policy(
            manifest_path=tmp_path / "prompts.toml",
            lock_path=tmp_path / "prompts.lock.json",
        )


def test_check_against_lock_should_raise_hash_mismatch_error_when_tracked_prompt_content_changes(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()

    (tmp_path / "prompts" / "setup.mg").write_text("<<tampered>>")

    reloaded_sut = FilesystemPromptIntegrity()
    reloaded_sut.load_policy(
        manifest_path=tmp_path / "prompts.toml",
        lock_path=tmp_path / "prompts.lock.json",
    )

    # Act
    # Assert
    with pytest.raises(PromptHashMismatchError):
        reloaded_sut.check_against_lock()


def test_check_against_lock_should_raise_missing_lock_error_when_tracked_prompt_is_not_in_lock(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()

    lock_path = tmp_path / "prompts.lock.json"
    payload = json.loads(lock_path.read_text())
    payload["files"].pop("setup.mg")
    lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    reloaded_sut = FilesystemPromptIntegrity()
    reloaded_sut.load_policy(
        manifest_path=tmp_path / "prompts.toml",
        lock_path=tmp_path / "prompts.lock.json",
    )

    # Act
    # Assert
    with pytest.raises(PromptMissingLockError):
        reloaded_sut.check_against_lock()


def test_check_against_lock_should_raise_prompt_integrity_error_when_lock_contains_stale_entries(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()

    lock_path = tmp_path / "prompts.lock.json"
    payload = json.loads(lock_path.read_text())
    payload["files"]["obsolete/stale.mg"] = "sha256:deadbeef"
    lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    reloaded_sut = FilesystemPromptIntegrity()
    reloaded_sut.load_policy(
        manifest_path=tmp_path / "prompts.toml",
        lock_path=tmp_path / "prompts.lock.json",
    )

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match="stale entries"):
        reloaded_sut.check_against_lock()


def test_scan_and_lock_should_raise_unverified_path_error_when_manifest_pattern_traverses_outside_prompt_root(
    tmp_path, monkeypatch
):
    # Arrange
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "escape.mg").write_text("<<escape>>")
    (tmp_path / "prompts.toml").write_text(
        'version = 1\nroot = "prompts"\ninclude = ["../**/*.mg"]\nexclude = []\n'
    )

    monkeypatch.chdir(tmp_path)
    sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptUnverifiedPathError, match="outside trusted prompt root"):
        sut.scan_and_lock()


def test_scan_and_lock_should_raise_unverified_path_error_when_prompt_symlink_targets_outside_prompt_root(
    tmp_path, monkeypatch
):
    # Arrange
    _write_default_project(tmp_path)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "escape.mg").write_text("<<escape>>")
    (tmp_path / "prompts" / "escape-link.mg").symlink_to(outside_dir / "escape.mg")

    monkeypatch.chdir(tmp_path)
    sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptUnverifiedPathError, match="outside trusted prompt root"):
        sut.scan_and_lock()


def test_scan_and_lock_should_raise_prompt_integrity_error_when_manifest_toml_is_malformed(
    tmp_path, monkeypatch
):
    # Arrange
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "prompts.toml").write_text('version = 1\nroot = "prompts"\ninclude = [')

    monkeypatch.chdir(tmp_path)
    sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match="Failed to parse manifest"):
        sut.scan_and_lock()


def test_load_policy_should_raise_prompt_integrity_error_when_lock_json_is_malformed(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()
    (tmp_path / "prompts.lock.json").write_text("{")

    reloaded_sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match="Failed to parse lock file"):
        reloaded_sut.load_policy(
            manifest_path=tmp_path / "prompts.toml",
            lock_path=tmp_path / "prompts.lock.json",
        )


def test_load_policy_should_raise_prompt_integrity_error_when_lock_files_mapping_is_invalid(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()

    lock_path = tmp_path / "prompts.lock.json"
    payload = json.loads(lock_path.read_text())
    payload["files"] = ["not-a-mapping"]
    lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    reloaded_sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(
        PromptIntegrityError, match="Lock field 'files' must be a mapping of string hashes"
    ):
        reloaded_sut.load_policy(
            manifest_path=tmp_path / "prompts.toml",
            lock_path=tmp_path / "prompts.lock.json",
        )


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_error"),
    [
        ("version", 999, "Unsupported lock version"),
        ("algorithm", "sha1", "Unsupported hash algorithm"),
        ("root", "different-prompts", "does not match manifest root"),
    ],
)
def test_load_policy_should_raise_prompt_integrity_error_when_lock_metadata_is_invalid(
    tmp_path, monkeypatch, field_name, field_value, expected_error
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()

    lock_path = tmp_path / "prompts.lock.json"
    payload = json.loads(lock_path.read_text())
    payload[field_name] = field_value
    lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    reloaded_sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match=expected_error):
        reloaded_sut.load_policy(
            manifest_path=tmp_path / "prompts.toml",
            lock_path=tmp_path / "prompts.lock.json",
        )


@pytest.mark.parametrize(
    ("manifest_payload", "expected_error"),
    [
        (
            'version = 2\nroot = "prompts"\ninclude = ["**/*.mg"]\nexclude = []\n',
            "Unsupported manifest version",
        ),
        (
            'version = 1\nroot = ""\ninclude = ["**/*.mg"]\nexclude = []\n',
            "Manifest field 'root' must be a non-empty string",
        ),
        (
            'version = 1\nroot = "prompts"\ninclude = "bad"\nexclude = []\n',
            "Manifest field 'include' must be a list of strings",
        ),
        (
            'version = 1\nroot = "prompts"\ninclude = ["**/*.mg"]\nexclude = "bad"\n',
            "Manifest field 'exclude' must be a list of strings",
        ),
    ],
)
def test_scan_and_lock_should_raise_prompt_integrity_error_when_manifest_fields_are_invalid(
    tmp_path, monkeypatch, manifest_payload, expected_error
):
    # Arrange
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "prompts.toml").write_text(manifest_payload)
    monkeypatch.chdir(tmp_path)
    sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match=expected_error):
        sut.scan_and_lock()


def test_scan_and_lock_should_raise_prompt_integrity_error_when_trusted_root_directory_is_missing(
    tmp_path, monkeypatch
):
    # Arrange
    (tmp_path / "prompts.toml").write_text(
        'version = 1\nroot = "prompts"\ninclude = ["**/*.mg"]\nexclude = []\n'
    )
    monkeypatch.chdir(tmp_path)
    sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match="does not exist or is not a directory"):
        sut.scan_and_lock()


def test_scan_and_lock_should_raise_prompt_integrity_error_when_trusted_root_path_is_not_directory(
    tmp_path, monkeypatch
):
    # Arrange
    (tmp_path / "prompts").write_text("not a directory")
    (tmp_path / "prompts.toml").write_text(
        'version = 1\nroot = "prompts"\ninclude = ["**/*.mg"]\nexclude = []\n'
    )
    monkeypatch.chdir(tmp_path)
    sut = FilesystemPromptIntegrity()

    # Act
    # Assert
    with pytest.raises(PromptIntegrityError, match="does not exist or is not a directory"):
        sut.scan_and_lock()


def test_verify_bytes_should_return_without_error_when_file_extension_is_not_tracked(
    tmp_path, monkeypatch
):
    # Arrange
    sut = _create_service_in_project_dir(tmp_path, monkeypatch)
    sut.scan_and_lock()
    untracked_file = tmp_path / "prompts" / "ignored.txt"

    reloaded_sut = FilesystemPromptIntegrity()
    reloaded_sut.load_policy(
        manifest_path=tmp_path / "prompts.toml",
        lock_path=tmp_path / "prompts.lock.json",
    )

    def _raise_if_hashing_is_used(_content: bytes) -> str:
        raise AssertionError("_hash_bytes should not be called for untracked file extensions.")

    monkeypatch.setattr(reloaded_sut, "_hash_bytes", _raise_if_hashing_is_used)

    # Act
    result = reloaded_sut.verify_bytes(
        path=untracked_file, content_bytes=untracked_file.read_bytes()
    )

    # Assert
    assert result is None
