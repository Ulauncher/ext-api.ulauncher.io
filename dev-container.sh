#!/bin/bash

docker run \
    -v $(pwd):/var/task \
    -v $(pwd)/.bashrc:/root/.bashrc \
    -v $HOME/.bash_history:/root/.bash_history \
    -p 8080:8080 \
    -it \
    --rm \
    --env-file .env \
    ulauncher/ext-api-zappa \
    bash
