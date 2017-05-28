#!/bin/bash

cd `dirname $0`
cd ..

IMAGE_NAME=ulauncher/ext-api

docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME
