#!/bin/bash

# Env Vars:
# ---------
# TAG - image tag name
# COMMIT_SHA1 - commit SHA1 hash
# PUSH (optional) - if equals to "true", run "docker push"

if [ -z "$TAG" ]; then
    echo "TAG variable is not set"
    exit 1
fi

if [ -z "$COMMIT_SHA1" ]; then
    echo "COMMIT_SHA1 variable is not set"
    exit 1
fi

cd `dirname $0`
cd ..

IMAGE_NAME=ulauncher/ext-api

set -ex

docker build \
    --build-arg "COMMIT_SHA1=$COMMIT_SHA1" \
    --build-arg "BUILD_DATE=$(date)" \
    -t \
    $IMAGE_NAME:$TAG .

if [ "$PUSH" = "true" ]; then
    echo $DOCKERHUB_PASSWORD | docker login -u $DOCKERHUB_LOGIN  --password-stdin
    docker push $IMAGE_NAME:$TAG
fi