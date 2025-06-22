#!/usr/bin/env python
import argparse
import sys

from ext_api.db import init_db
from ext_api.helpers.logging_utils import setup_logging
from ext_api.server import http_server
from ext_api.sync_extensions import sync_extensions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application commands")
    tasks = {
        "http_server": (http_server, "Start the API server"),
        "init_db": (init_db, "Initialize the database"),
        "sync_extensions": (sync_extensions, "Sync extensions from Github"),
    }
    parser.add_argument(
        "cmd",
        type=str,
        choices=tasks.keys(),
        help="Command to run. Available commands: "
        + "\n".join([f"{cmd} - {desc}" for cmd, (_, desc) in tasks.items()]),
    )

    # Show help if no arguments are provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    setup_logging()
    tasks[args.cmd][0]()
