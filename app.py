#!/usr/bin/env python
import argparse
from ext_api.helpers.logging import setup_logging
from ext_api.server import run_server
from ext_api.db import init_db


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Application management commands')
    tasks = {
        'run_server': run_server,
        'init_db': init_db
    }
    parser.add_argument('cmd', type=str, choices=tasks.keys(), help='Command')
    args = parser.parse_args()

    setup_logging()
    tasks[args.cmd]()
