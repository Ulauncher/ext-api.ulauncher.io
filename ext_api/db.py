import datetime
import importlib
import logging
import os
import re
import sys
import traceback

from pymongo import MongoClient
from pymongo.collection import Collection

from ext_api.config import db_name, mongodb_connection
from ext_api.entities import Extension, Migration

client = MongoClient(mongodb_connection)  #  type: ignore
db = client[db_name]  #  type: ignore
logger: logging.Logger = logging.getLogger(__name__)
migration_collection: Collection[Migration] = db.Migrations  # type: ignore
extension_collection: Collection[Extension] = db.Extensions  # type: ignore

__version__: int = 3


class DbMigrationError(Exception):
    pass


class MigrationsConsistencyError(Exception):
    pass


def check_migration_consistency() -> None:
    for version, _ in list_migrations():
        if version > __version__:
            logger.warning("Version in db.py cannot be lower than the highest version in ./migrations")

    db_ver = get_last_version()
    if db_ver > __version__:
        logger.warning("Version in the DB is > version in db.py. Downgrading code to previous version is not possible")
    elif db_ver != __version__:
        logger.warning("Version in the DB doesn't match version in db.py. Did you forget to run migrations?")


def init_db() -> None:
    if "Migrations" in db.list_collection_names():
        db_ver = get_last_version()
        if db_ver < __version__:
            run_migrations(db_ver, __version__)
            logger.info("DB schema updated")
        else:
            logger.info("DB schema is up-to-date")
    else:
        create_indexes()
        migration_collection.insert({"Version": __version__, "CreatedAt": datetime.datetime.now(datetime.UTC)})
        logger.info("DB schema updated")


def list_migrations() -> list[tuple[int, str]]:
    """
    Returns list of tuples (version_int, version_file_str)
    """
    versions: list[tuple[int, str]] = []
    path: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for migration in os.listdir(os.path.join(path, "db_migrations")):
        if re.match(r"\d+\.py$", migration):
            ver: int = int(migration[:-3])
            versions.append((ver, migration))
    versions.sort()
    return versions


def run_migrations(db_ver: int, code_ver: int) -> None:
    logger.info("Start applying migrations")
    for ver, migration in list_migrations():
        if ver <= db_ver or ver > code_ver:
            continue
        try:
            m = importlib.import_module(f"db_migrations.{migration[:-3]}")
            logger.info("Migrating DB to v%s...", ver)
            m.run_migration()
            logger.info("Migration v%s is completed", ver)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            raise DbMigrationError(str(e)) from e


def get_last_version() -> int:
    results = migration_collection.find({}).sort("CreatedAt", -1).limit(1)
    for result in results:
        return result["Version"]

    return 0


def create_indexes() -> None:
    migration_collection.create_index("CreatedAt")
    migration_collection.create_index("Version", unique=True)

    extension_collection.create_index("ID", unique=True)
    extension_collection.create_index("User")
    extension_collection.create_index([("Published", 1), ("CreatedAt", -1)])
    extension_collection.create_index([("Published", 1), ("GithubStars", -1)])
