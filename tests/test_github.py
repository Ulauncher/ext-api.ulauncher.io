import pytest

from ext_api.github import (
    InvalidGithubUrlError,
    VersionsValidationError,
    _read_versions_file,  # type: ignore
    extract_major,
    get_project_path,
)


def test_get_project_path__returns_path():
    assert get_project_path("https://github.com/owner_name/repo-name") == "owner_name/repo-name"
    assert get_project_path("https://github.com/owner_name/repo-name/") == "owner_name/repo-name"


def test_get_project_path__raises_invalidgithuburlerror():
    with pytest.raises(InvalidGithubUrlError):
        assert get_project_path("") == "owner_name/repo-name"
    with pytest.raises(InvalidGithubUrlError):
        assert get_project_path("https://github.coms/owner_name/repo-name/")


# versions.json
def test_read_versions_file__valid():
    versions = [
        {"api_version": "^1.0.0", "commit": "python2"},
        {"required_api_version": "^2.0.0", "commit": "master"},
    ]
    result = _read_versions_file(versions)

    assert result["versions"][0]["api_version"] == "2"
    assert result["versions"][0]["commit"] == "master"
    assert result["versions"][1]["api_version"] == "1"
    assert result["versions"][1]["commit"] == "python2"
    assert result["latest_supported"] == "2"


def test_read_versions_file__invalid_type__raises():
    versions = {"invalid": "type"}
    with pytest.raises(VersionsValidationError):
        assert _read_versions_file(versions)


def test_read_versions_file__no_valid_versions__raises():
    versions = [
        {"required_api_version_typo": "^1.0.0", "commit": "python2"},
        {"required_api_version": "", "commit": "empty"},
    ]
    with pytest.raises(VersionsValidationError):
        assert _read_versions_file(versions)


def test_extract_major():
    assert extract_major("1.0.0") == "1"
    assert extract_major("~2.3.0") == "2"
    assert extract_major("^2.3.0") == "2"
    assert extract_major("v2.3.0") == "2"
    assert extract_major("123") == "123"
    assert extract_major("abc") is None
