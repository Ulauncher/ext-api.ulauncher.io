#!/bin/bash


cd `dirname $0`
cd ..

docker run \
    -v $(pwd):/var/task \
    -v $HOME/.bash_history:/root/.bash_history \
    -p 8000:8000 \
    -it \
    --rm \
    --env-file .env \
    --name ext-api \
    ulauncher/ext-api \
    bash
