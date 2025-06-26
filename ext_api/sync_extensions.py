import logging
import sys
import traceback
from time import sleep

from ext_api.entities import Extension, RepoInfo
from ext_api.github import (
    JsonFileNotFoundError,
    ProjectNotFoundError,
    VersionsValidationError,
    get_manifest,
    get_repo_info,
    get_versions,
)
from ext_api.repositories.extensions import get_extensions, update_extension

logger = logging.getLogger(__name__)


def update_ext_stars(ext: Extension, repo_info: RepoInfo):
    update_extension(ext["ID"], {"GithubStars": repo_info["stargazers_count"]})
    logger.info("Extension %s has %s stars", ext["ID"], repo_info["stargazers_count"])


def update_ext_versions(ext: Extension, repo_info: RepoInfo):
    supported_versions = []
    try:
        versions = get_versions(ext["ProjectPath"], repo_info)
        supported_versions = [v["api_version"] for v in versions["versions"]]
    except JsonFileNotFoundError:
        # if versions.json is not found, we assume the extension supports the current latest API version
        logger.warning("Extension %s has no versions.json", ext["GithubUrl"])
    except VersionsValidationError as e:
        logger.warning("Extension %s has invalid versions.json: %s", ext["GithubUrl"], e)

    if not supported_versions:
        # if versions.json is not found or is invalid, get the version from manifest.json
        manifest = get_manifest(ext["ProjectPath"], repo_info)
        supported_versions = [manifest["api_version"]]

    update_extension(ext["ID"], {"SupportedVersions": supported_versions})
    logger.info("Extension %s supports versions %s", ext["ID"], supported_versions)


def sync_extensions():
    while True:
        try:
            extensions = get_extensions()["data"]
            total = len(extensions)
            logger.info("Found %s extensions to sync", total)
            i = 0
            for ext in extensions:
                i += 1
                try:
                    repo_info = get_repo_info(ext["ProjectPath"])
                except ProjectNotFoundError:
                    logger.warning("Project not found: %s. Unpublishing.", ext["ProjectPath"])
                    update_extension(ext["ID"], {"Published": False})
                    continue

                logger.info("🔃 (%s/%s) Sync extension: %s", i, total, ext["ProjectPath"])
                update_ext_stars(ext, repo_info)
                update_ext_versions(ext, repo_info)
        except Exception as e:
            logger.exception(type(e).__name__)
            traceback.print_exc(file=sys.stderr)

        five_hours = 18000  # sec
        logger.info("Wait five hours...")
        sleep(five_hours)
