import sys
import logging
import traceback

from ext_api.models.extensions import get_extensions, update_extension
from ext_api.github import (get_project_path, get_repo_info, ProjectNotFoundError)

logger = logging.getLogger(__name__)


def sync_github_stars():
    for ext in get_extensions():
        update_ext_stars(ext)


def update_ext_stars(ext):
    project_path = get_project_path(ext['GithubUrl'])
    try:
        info = get_repo_info(project_path)
        stars = info['stargazers_count']
    except ProjectNotFoundError:
        stars = 0

    try:
        update_extension(ext['ID'], GithubStars=stars)
    except Exception as e:
        logger.error('%s: %s', type(e).__name__, e)
        traceback.print_exc(file=sys.stderr)

    logger.info('Extension %s is synced. GithubStars: %s', ext['ID'], stars)
