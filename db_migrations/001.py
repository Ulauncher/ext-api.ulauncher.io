from ext_api.db import db
from datetime import datetime


__version__ = 1


def run_migration():
    """
    Initial migration
    """
    db.Migrations.insert({'Version': __version__, 'CreatedAt': datetime.utcnow()})
