from datetime import datetime

from ext_api.db import db

__version__ = 1


def run_migration():
    """
    Initial migration
    """
    db.Migrations.insert({"Version": __version__, "CreatedAt": datetime.now(datetime.timezone.utc)})
