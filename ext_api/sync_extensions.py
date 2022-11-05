import logging
from time import sleep

from ext_api.sync_ext_versions import sync_ext_versions
from ext_api.sync_github_stars import sync_github_stars

logger = logging.getLogger(__name__)


def sync_extensions():
    while True:
        logger.info('Sync github stars...')
        sync_github_stars()

        logger.info('Sync versions...')
        sync_ext_versions()

        five_hours = 18000  # sec
        logger.info('Wait five hours...')
        sleep(five_hours)
