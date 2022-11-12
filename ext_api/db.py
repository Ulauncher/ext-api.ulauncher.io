import re
import importlib
import os
import sys
import logging
import traceback
from datetime import datetime
from pymongo import MongoClient

from ext_api.config import mongodb_connection, db_name


client = MongoClient(mongodb_connection)
db = client[db_name]
logger = logging.getLogger(__name__)

__version__ = 3


class DbMigrationError(Exception):
    pass


class MigrationsConsistencyError(Exception):
    pass


def check_migration_consistency():
    for version, _ in list_migrations():
        if version > __version__:
            logger.warning('Version in db.py cannot be lower than the highest version in ./migrations')
            sys.exit(1)

    db_ver = get_last_version()
    if db_ver > __version__:
        logger.warning("Version in the DB is > version in db.py. Downgrading code to previous version is not possible")
        sys.exit(1)
    elif db_ver != __version__:
        logger.warning("Version in the DB doesn't match version in db.py. Did you forget to run migrations?")
        sys.exit(1)


def init_db():
    if 'Migrations' in db.collection_names():
        db_ver = get_last_version()
        if db_ver < __version__:
            run_migrations(db_ver, __version__)
            logger.info("DB schema updated")
        else:
            logger.info("DB schema is up-to-date")
    else:
        create_indexes()
        db.Migrations.insert({'Version': __version__, 'CreatedAt': datetime.utcnow()})
        logger.info("DB schema updated")


def list_migrations():
    """
    Returns list of tuples (version_int, version_file_str)
    """
    versions = []
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for migration in os.listdir(os.path.join(path, 'db_migrations')):
        if re.match(r'\d+\.py$', migration):
            ver = int(migration[:-3])
            versions.append((ver, migration))
    versions.sort()
    return versions


def run_migrations(db_ver, code_ver):
    logger.info('Start applying migrations')
    for ver, migration in list_migrations():
        if ver <= db_ver or ver > code_ver:
            continue
        try:
            m = importlib.import_module('db_migrations.%s' % migration[:-3])
            logger.info('Migrating DB to v%s...', ver)
            m.run_migration()
            logger.info('Migration v%s is completed', ver)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            raise DbMigrationError(str(e))


def get_last_version():
    results = db.Migrations.find({}).sort('CreatedAt', -1).limit(1)
    for result in results:
        return result['Version']

    return 0


def create_indexes():
    db.Migrations.create_index('CreatedAt')
    db.Migrations.create_index('Version', unique=True)

    db.Extensions.create_index('ID', unique=True)
    db.Extensions.create_index('User')
    db.Extensions.create_index([('Published', 1), ('CreatedAt', -1)])
    db.Extensions.create_index([('Published', 1), ('GithubStars', -1)])
