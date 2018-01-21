#!/bin/bash -e

cd `dirname $0`/..

./app.py init_db
./app.py run_server
