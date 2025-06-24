import pytest

from ext_api.entities import Manifest
from ext_api.github import (
    InvalidGithubUrlError,
    ManifestValidationError,
    VersionsValidationError,
    get_latest_version_commit,
    get_project_path,
    validate_manifest,
    validate_versions,
)


def test_get_project_path__returns_path():
    assert get_project_path("https://github.com/owner_name/repo-name") == "owner_name/repo-name"
    assert get_project_path("https://github.com/owner_name/repo-name/") == "owner_name/repo-name"


def test_get_project_path__raises_invalidgithuburlerror():
    with pytest.raises(InvalidGithubUrlError):
        assert get_project_path("") == "owner_name/repo-name"
    with pytest.raises(InvalidGithubUrlError):
        assert get_project_path("https://github.coms/owner_name/repo-name/")


def test_validate_manifest():
    manifest = Manifest(
        {
            "required_api_version": "1",
            "name": "name",
            "description": "description",
            "developer_name": "developer_name",
        }
    )

    validate_manifest(manifest)
    with pytest.raises(ManifestValidationError):  # noqa: PT012
        del manifest["developer_name"]
        validate_manifest(manifest)


def test_validate_versions__valid():
    versions = [
        {"required_api_version": "^1.0.0", "commit": "python2"},
        {"required_api_version": "^2.0.0", "commit": "master"},
    ]
    assert validate_versions(versions) == versions


def test_validate_versions__invalid_type__raises():
    versions = {"invalid": "type"}
    with pytest.raises(VersionsValidationError):
        assert validate_versions(versions)


def test_validate_versions__no_valid_versions__raises():
    versions = [
        {"required_api_version_typo": "^1.0.0", "commit": "python2"},
        {"required_api_version": "", "commit": "empty"},
    ]
    with pytest.raises(VersionsValidationError):
        assert validate_versions(versions)


def test_get_latest_version_commit():
    versions = [
        {"required_api_version": "^1.0.0", "commit": "python2"},
        {"required_api_version": "2.3.0", "commit": "python3"},
        {"required_api_version": "^2.0.0", "commit": "master"},
    ]
    assert get_latest_version_commit(versions) == "python3"
