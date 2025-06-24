import datetime

from ext_api.db import extension_collection, migration_collection

__version__ = 2


def run_migration():
    extension_collection.create_index([("Published", 1), ("GithubStars", -1)])
    migration_collection.insert({"Version": __version__, "CreatedAt": datetime.datetime.now(datetime.UTC)})
