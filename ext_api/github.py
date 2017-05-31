import re
import json
from urllib.request import urlopen


def get_project_path(github_url):
    match = re.match(r'^http(s)?:\/\/github.com\/([\w-]+\/[\w-]+)(\/)?$',
                     github_url, re.I)
    if not match:
        raise InvalidGithubUrlError('Invalid GithubUrl: %s' % github_url)

    return match.group(2)


def get_manifest(repo_path):
    """
    Raises urllib.error.HTTPError
    """
    url = 'https://raw.githubusercontent.com/%s/master/manifest.json' % repo_path
    response = urlopen(url)
    return json.load(response)


def validate_manifest(manifest):
    try:
        assert str(manifest.get('manifest_version')) == '1', 'manifest_version should be "1"'
        assert str(manifest.get('api_version')) == '1', 'api_version should be "1"'
        assert manifest.get('name'), 'name is empty'
        assert manifest.get('description'), 'description is empty'
        assert manifest.get('developer_name'), 'developer_name is empty'
    except AssertionError as e:
        raise ManifestValidationError(e)


class InvalidGithubUrlError(Exception):
    pass


class ManifestValidationError(Exception):
    pass
