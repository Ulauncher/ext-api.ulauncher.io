import datetime

from ext_api.db import migration_collection

__version__ = 1


def run_migration():
    """
    Initial migration
    """
    migration_collection.insert_one({"Version": __version__, "CreatedAt": datetime.datetime.now(datetime.UTC)})
