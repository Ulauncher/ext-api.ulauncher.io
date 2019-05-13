import re
import json
from urllib.request import urlopen
from urllib.error import HTTPError


def get_project_path(github_url):
    match = re.match(r'^http(s)?:\/\/github.com\/([\w-]+\/[\w-]+)(\/)?$',
                     github_url, re.I)
    if not match:
        raise InvalidGithubUrlError('Invalid GithubUrl: %s' % github_url)

    return match.group(2)


def get_json(repo_path, commit, blob_path):
    """
    Raises urllib.error.HTTPError
    Raises ProjectValidationError
    """
    url = 'https://raw.githubusercontent.com/%s/%s/%s.json' % (repo_path, commit, blob_path)
    try:
        response = urlopen(url)
    except HTTPError as e:
        if e.status == 404:
            raise ProjectValidationError('Unable to find file "%s.json" in branch "%s"' % (blob_path, commit))
        raise
    return json.load(response)


def validate_manifest(manifest):
    try:
        assert manifest.get('name'), 'name is empty'
        assert manifest.get('description'), 'description is empty'
        assert manifest.get('developer_name'), 'developer_name is empty'
    except AssertionError as e:
        raise ManifestValidationError(e)


def validate_versions(versions):
    """
    versions.json example https://github.com/Ulauncher/ulauncher-demo-ext/blob/master/versions.json
    """
    supported = []
    if not isinstance(versions, list):
        raise VersionsValidationError('Invalid versions.json format. It must be a list of objects')

    for ver in versions:
        try:
            assert ver['required_api_version']
            assert ver['commit']
        except (KeyError, AssertionError):
            continue
        supported.append(ver)
    if not supported:
        raise VersionsValidationError('Invalid versions.json. It must define at least one supported version')
    return supported


def get_latest_version_commit(versions):
    valid_versions = validate_versions(versions)
    # todo: it's not the best algorithm to determine the latest version, but it's good for now
    commits_by_clean_ver = {re.sub(r'[^0-9.]+', '', v['required_api_version']): v['commit'] for v in valid_versions}
    versions = sorted(commits_by_clean_ver.keys(), reverse=True)
    latest_ver = versions[0]
    return commits_by_clean_ver[latest_ver]


class InvalidGithubUrlError(Exception):
    pass


class ProjectValidationError(Exception):
    pass


class ManifestValidationError(ProjectValidationError):
    pass


class VersionsValidationError(ProjectValidationError):
    pass
