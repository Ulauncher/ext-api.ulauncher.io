import pytest
from ext_api.github import (get_project_path, InvalidGithubUrlError, get_manifest, validate_manifest,
                            ManifestValidationError)


def test_get_project_path__returns_path():
    assert get_project_path('https://github.com/owner_name/repo-name') == 'owner_name/repo-name'
    assert get_project_path('https://github.com/owner_name/repo-name/') == 'owner_name/repo-name'


def test_get_project_path__raises_InvalidGithubUrlError():
    with pytest.raises(InvalidGithubUrlError):
        assert get_project_path('') == 'owner_name/repo-name'
    with pytest.raises(InvalidGithubUrlError):
        assert get_project_path('https://github.coms/owner_name/repo-name/')


def test_validate_manifest():
    manifest = {
        'manifest_version': 1,
        'api_version': '1',
        'name': 'name',
        'description': 'description',
        'developer_name': 'developer_name',
    }

    validate_manifest(manifest)
    with pytest.raises(ManifestValidationError):
        del manifest['developer_name']
        validate_manifest(manifest)
