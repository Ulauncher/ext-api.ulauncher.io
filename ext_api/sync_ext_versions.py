import sys
import logging
import traceback
from time import sleep

from ext_api.models.extensions import get_extensions, update_extension
from ext_api.github import (get_project_path, get_json, validate_versions,
                            JsonFileNotFoundError, VersionsValidationError)

logger = logging.getLogger(__name__)


def sync_ext_versions():
    for ext in get_extensions():
        update_ext_versions(ext)
    one_hour = 3600  # sec
    sleep(one_hour)


def update_ext_versions(ext):
    project_path = get_project_path(ext['GithubUrl'])
    try:
        versions = get_json(project_path, 'master', 'versions')
        valid_versions = validate_versions(versions)
        versions_only = [v['required_api_version'] for v in valid_versions]
    except JsonFileNotFoundError:
        versions_only = ['^1.0.0']
    except VersionsValidationError:
        versions_only = []

    try:
        update_extension(ext['ID'], SupportedVersions=versions_only)
    except Exception as e:
        logger.error('%s: %s', type(e).__name__, e)
        traceback.print_exc(file=sys.stderr)

    logger.info('Extension %s is synced. SupportedVersions: %s', ext['ID'], versions_only)
