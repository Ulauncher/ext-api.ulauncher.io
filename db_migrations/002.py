from datetime import datetime  # noqa: N999

from ext_api.db import db

__version__ = 2


def run_migration():
    db.Extensions.create_index([("Published", 1), ("GithubStars", -1)])
    db.Migrations.insert({"Version": __version__, "CreatedAt": datetime.now(datetime.timezone.utc)})
