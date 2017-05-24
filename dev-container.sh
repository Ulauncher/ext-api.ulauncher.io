#!/bin/bash

docker run \
    -v $(pwd):/var/task \
    -p 8080:8080 \
    -it \
    --rm \
    --env-file .env \
    mcrowson/zappa-builder \
    bash -c "virtualenv docker_env && source docker_env/bin/activate && pip install -r requirements.txt && bash"
