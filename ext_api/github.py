import base64
import json
import logging
import re
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ext_api.config import github_api_token, github_api_user
from ext_api.entities import CompatibleVersion, Manifest, RepoInfo

logger = logging.getLogger(__name__)


def create_authenticated_request(url: str):
    req = Request(url)
    credentials = f"{github_api_user}:{github_api_token}"
    encoded_credentials = base64.b64encode(credentials.encode("ascii"))
    req.add_header("Authorization", "Basic {}".format(encoded_credentials.decode("ascii")))
    return req


def get_project_path(github_url: str) -> str:
    match = re.match(r"^http(s)?:\/\/github.com\/([\w-]+\/[\w-]+)(\/)?$", github_url, re.IGNORECASE)
    if not match:
        raise InvalidGithubUrlError(f"Invalid GithubUrl: {github_url}")

    return match.group(2)


HTTP_NOT_FOUND = 404


def get_json(repo_path: str, commit: str, blob_path: str):
    """
    Raises urllib.error.HTTPError
    Raises ProjectValidationError
    """
    url = f"https://raw.githubusercontent.com/{repo_path}/{commit}/{blob_path}.json"
    req = create_authenticated_request(url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        if e.status == HTTP_NOT_FOUND:
            raise JsonFileNotFoundError(f'Unable to find file "{blob_path}.json" in branch "{commit}"') from e
        raise
    logger.debug("X-RateLimit-Remaining: %s", response.headers.get("X-RateLimit-Remaining"))
    return json.load(response)


def get_repo_info(repo_path: str) -> RepoInfo:
    """
    Raises urllib.error.HTTPError
    Raises ProjectValidationError
    """
    url = f"https://api.github.com/repos/{repo_path}"
    req = create_authenticated_request(url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        if e.status == HTTP_NOT_FOUND:
            raise ProjectNotFoundError(f"Github project not found: https://github.com/{repo_path}") from e
        raise
    logger.debug("X-RateLimit-Remaining: %s", response.headers.get("X-RateLimit-Remaining"))
    return json.load(response)


def validate_manifest(manifest: Manifest):
    try:
        assert manifest.get("name"), "name is empty"
        assert manifest.get("description"), "description is empty"
        assert manifest.get("developer_name"), "developer_name is empty"
    except AssertionError as e:
        raise ManifestValidationError(e) from e


def validate_versions(versions: Any) -> list[CompatibleVersion]:
    """
    versions.json example https://github.com/Ulauncher/ulauncher-demo-ext/blob/master/versions.json
    """
    supported: list[CompatibleVersion] = []
    if not isinstance(versions, list):
        msg = "Invalid versions.json format. It must be a list of objects"
        raise VersionsValidationError(msg)

    for ver in versions:  # type: ignore
        try:
            assert ver["required_api_version"], str
            assert ver["commit"], str
        except (KeyError, AssertionError):
            continue
        supported.append(ver)  # type: ignore
    if not supported:
        msg = "Invalid versions.json. It must define at least one supported version"
        raise VersionsValidationError(msg)
    return supported


def get_latest_version_commit(versions: Any) -> str:
    valid_versions = validate_versions(versions)
    # TODO: it's not the best algorithm to determine the latest version, but it's good for now
    commits_by_clean_ver = {re.sub(r"[^0-9.]+", "", v["required_api_version"]): v["commit"] for v in valid_versions}
    versions = sorted(commits_by_clean_ver.keys(), reverse=True)
    latest_ver = versions[0]
    return commits_by_clean_ver[latest_ver]


class InvalidGithubUrlError(Exception):
    pass


class ProjectValidationError(Exception):
    pass


class ProjectNotFoundError(ProjectValidationError):
    pass


class JsonFileNotFoundError(ProjectValidationError):
    pass


class ManifestValidationError(ProjectValidationError):
    pass


class VersionsValidationError(ProjectValidationError):
    pass
