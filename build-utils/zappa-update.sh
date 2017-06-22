#!/bin/bash

cd `dirname $0`
cd ..

sed -i "s/commit =.*/commit = '$TRAVIS_COMMIT'/g" ext_api/config.py
sed -i "s/deployed_on =.*/deployed_on = '`date`'/g" ext_api/config.py

step1="virtualenv /var/docker_env"
step2="source /var/docker_env/bin/activate"
step3="zappa update dev"

docker run \
    -v $(pwd):/var/task \
    --rm \
    --env-file .aws \
    ulauncher/ext-api \
    bash -c "$step1 && $step2 && $step3"
