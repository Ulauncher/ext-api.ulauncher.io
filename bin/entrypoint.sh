#!/bin/bash

set -ex

cd `dirname $0`/..

if [[ -z "$@" ]]; then
    exec ./app.py run_server
fi

exec ./app.py $@
