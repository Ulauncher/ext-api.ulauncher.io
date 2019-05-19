#!/bin/bash

set -ex

cd `dirname $0`/..

if [[ -z "$@" ]]; then
    ./app.py init_db
    exec ./app.py run_server
fi

exec ./app.py $@
