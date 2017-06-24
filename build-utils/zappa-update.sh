#!/bin/bash

cd `dirname $0`
cd ..

sed -i "s/commit =.*/commit = '$TRAVIS_COMMIT'/g" ext_api/config.py
sed -i "s/deployed_on =.*/deployed_on = '`date`'/g" ext_api/config.py

cmd="./test tests"
cmd="$cmd && virtualenv /var/docker_env"
cmd="$cmd && source /var/docker_env/bin/activate"
cmd="$cmd && zappa update dev"
if [ "$TRAVIS_BRANCH" == "master" ]; then
    cmd="$cmd && zappa update stg"
fi

docker run \
    -v $(pwd):/var/task \
    --rm \
    --env-file .aws \
    ulauncher/ext-api \
    bash -c "$cmd"
