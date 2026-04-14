import datetime

from ext_api.db import extension_collection, migration_collection

__version__ = 4


def run_migration():
    extension_collection.create_index([("ProjectPath", "text"), ("Description", "text")])
    migration_collection.insert_one({"Version": __version__, "CreatedAt": datetime.datetime.now(datetime.UTC)})
