FROM python:3.6

MAINTAINER Aleksandr Gornostal <sanya.gornostal@gmail.com>

WORKDIR /var/task

COPY [ "requirements-dev.txt", "requirements.txt", "./" ]

RUN pip install -r requirements-dev.txt && \
    pip install -r requirements.txt
