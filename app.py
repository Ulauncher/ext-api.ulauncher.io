#!/usr/bin/env python
import argparse

from ext_api.db import init_db
from ext_api.helpers.logging_utils import setup_logging
from ext_api.server import run_server
from ext_api.sync_extensions import sync_extensions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Application commands")
    tasks = {"run_server": run_server, "init_db": init_db, "sync_extensions": sync_extensions}
    parser.add_argument("cmd", type=str, choices=tasks.keys(), help="Command")
    args = parser.parse_args()

    setup_logging()
    tasks[args.cmd]()
