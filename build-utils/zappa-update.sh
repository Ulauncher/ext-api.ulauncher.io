#!/bin/bash

cd `dirname $0`
cd ..

sed -i "s/commit =.*/commit = '$TRAVIS_COMMIT'/g" ext_api/config.py
sed -i "s/deployed_on =.*/deployed_on = '`date`'/g" ext_api/config.py

notify_deploy() {
    echo
    echo "====================="
    echo "Deploying to $1"
    echo "====================="
    echo
}

cmd="./test tests"
deploy="virtualenv /var/docker_env"
deploy="$deploy && source /var/docker_env/bin/activate"
if [ "$TRAVIS_BRANCH" == "master" ]; then
    notify_deploy prod
    cmd="$cmd && $deploy && zappa update prod"
elif [ "$TRAVIS_BRANCH" == "stg" ]; then
    notify_deploy staging
    cmd="$cmd && $deploy && zappa update stg"
elif [ "$TRAVIS_BRANCH" == "dev" ]; then
    notify_deploy dev
    cmd="$cmd && $deploy && zappa update dev"
else
    echo "Run without deploy"
fi

docker run \
    -v $(pwd):/var/task \
    --rm \
    --env-file .aws \
    ulauncher/ext-api \
    bash -c "$cmd"
