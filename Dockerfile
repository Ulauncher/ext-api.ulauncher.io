FROM python:3.6

MAINTAINER Aleksandr Gornostal <sanya.gornostal@gmail.com>

WORKDIR /var/task

COPY [ "requirements-dev.txt", "requirements.txt", "./" ]

RUN pip install -r requirements-dev.txt && \
    pip install -r requirements.txt && \
    bash -c "virtualenv /var/docker_env && source /var/docker_env/bin/activate && pip install -r requirements.txt"

ENV PYTHONPATH=/var/task
