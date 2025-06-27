import base64
import json
import logging
import re
from typing import Any, TypedDict
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ext_api.config import github_api_token, github_api_user
from ext_api.entities import Manifest, RepoInfo

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


def _get_json(repo_path: str, commit: str, blob_path: str):
    """
    Fetches {blob_path}.json from the given repo_path at the specified commit.
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
    Fetches repository information from the GitHub API.
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


class SupportedVersion(TypedDict):
    api_version: str
    commit: str


class ExtensionVersions(TypedDict):
    versions: list[SupportedVersion]
    latest_supported: str
    commit_or_branch: str


def _read_versions_file(versions_file_content: Any | list[dict[str, str]]) -> ExtensionVersions:
    """
    versions.json example https://github.com/Ulauncher/ulauncher-demo-ext/blob/master/versions.json
    """
    valid_only: list[SupportedVersion] = []
    if not isinstance(versions_file_content, list):
        msg = "Invalid versions.json format. It must be a list of objects"
        raise VersionsValidationError(msg)

    for ver in versions_file_content:  # type: ignore
        commit = ver.get("commit")  # type: ignore
        # read api_version and required_api_version (for backward compatibility)
        version = ver.get("api_version") or ver.get("required_api_version")  # type: ignore

        if not commit or not isinstance(version, str):
            continue

        api_version = extract_major(version)

        if not api_version:
            continue

        valid_only.append(
            {
                "commit": commit,
                "api_version": api_version,
            }
        )
    if not valid_only:
        msg = "Invalid versions.json. It must define at least one supported version"
        raise VersionsValidationError(msg)

    valid_only.sort(key=lambda v: v["api_version"], reverse=True)
    latest = valid_only[0]["api_version"]
    commit_or_branch = valid_only[0]["commit"]

    return ExtensionVersions(
        versions=valid_only,
        latest_supported=latest,
        commit_or_branch=commit_or_branch,
    )


def get_manifest(project_path: str, repo_info: RepoInfo | None = None) -> Manifest:
    """
    Reads manifest.json from the given project path.
    Example: https://github.com/Ulauncher/ulauncher-demo-ext/blob/master/manifest.json
    Raises:
        ManifestValidationError: If the manifest is invalid.
        JsonFileNotFoundError: If the manifest file is not found.
    """
    if not repo_info:
        repo_info = get_repo_info(project_path)

    try:
        manifest_json = _get_json(project_path, repo_info["default_branch"], "manifest")
    except Exception as e:
        raise ManifestValidationError(f"manifest.json validation error: {e}") from e

    manifest = manifest_json
    api_version = extract_major(manifest.get("api_version") or manifest.get("required_api_version") or "")
    name = manifest.get("name")
    description = manifest.get("description")
    authors = manifest.get("authors") or manifest.get("developer_name")

    try:
        assert api_version, "api_version cannot be empty and should contain a version number"
        assert name, "name is empty"
        assert description, "description is empty"
        assert authors, "authors is empty"
    except AssertionError as e:
        raise ManifestValidationError(e) from e

    return Manifest(
        api_version=api_version,
        name=name,
        description=description,
        authors=authors,
    )


def get_versions(project_path: str, repo_info: RepoInfo | None = None) -> ExtensionVersions:
    """
    Reads versions.json frm the given project path.
    Example: https://github.com/Ulauncher/ulauncher-demo-ext/blob/master/versions.json
    Raises:
        VersionsValidationError: If the versions file is invalid.
        JsonFileNotFoundError: If the versions file is not found.
    """
    if not repo_info:
        repo_info = get_repo_info(project_path)

    try:
        versions_file_content = _get_json(project_path, repo_info["default_branch"], "versions")
    except Exception as e:
        raise VersionsValidationError(f"versions.json validation error: {e}") from e
    return _read_versions_file(versions_file_content)


def extract_major(version: str) -> str | None:
    match = re.match(r"^[^\d]?(\d+)", version)
    return match.group(1) if match else None


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
