import re
import json
from urllib.request import urlopen


def get_project_path(github_url):
    match = re.match(r'^http(s)?:\/\/github.com\/([\w-]+\/[\w-]+)(\/)?$',
                     github_url, re.I)
    if not match:
        raise InvalidGithubUrlError('Invalid GithubUrl: %s' % github_url)

    return match.group(2)


def get_master_json(repo_path, blob_path):
    """
    Raises urllib.error.HTTPError
    """
    url = 'https://raw.githubusercontent.com/%s/master/%s.json' % (repo_path, blob_path)
    response = urlopen(url)
    return json.load(response)


def validate_manifest(manifest):
    try:
        assert manifest.get('name'), 'name is empty'
        assert manifest.get('description'), 'description is empty'
        assert manifest.get('developer_name'), 'developer_name is empty'
    except AssertionError as e:
        raise ManifestValidationError(e)


def validate_versions(versions):
    supported = []
    for ver in versions:
        try:
            req_ver = ver['required_api_version']
        except KeyError:
            continue
        supported.append(req_ver)
    if not supported:
        raise VersionsValidationError('Invalid versions.json. It must define at least one supported version')
    return supported


class InvalidGithubUrlError(Exception):
    pass


class ManifestValidationError(Exception):
    pass


class VersionsValidationError(Exception):
    pass
