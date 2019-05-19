#!/usr/bin/env python
import argparse
from ext_api.helpers.logging_utils import setup_logging
from ext_api.server import run_server
from ext_api.db import init_db
from ext_api.sync_ext_versions import sync_ext_versions
from ext_api.sync_github_stars import sync_github_stars


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Application commands')
    tasks = {
        'run_server': run_server,
        'init_db': init_db,
        'sync_ext_versions': sync_ext_versions,
        'sync_github_stars': sync_github_stars
    }
    parser.add_argument('cmd', type=str, choices=tasks.keys(), help='Command')
    args = parser.parse_args()

    setup_logging()
    tasks[args.cmd]()
