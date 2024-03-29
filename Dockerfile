FROM python:3.7.15-slim

MAINTAINER Aleksandr Gornostal <ulauncher.app@gmail.com>

ARG COMMIT_SHA1
ARG BUILD_DATE
ENV COMMIT_SHA1 $COMMIT_SHA1
ENV BUILD_DATE $BUILD_DATE

WORKDIR /var/app
ENV PYTHONPATH=/var/app
EXPOSE 8080

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "./bin/entrypoint.sh" ]
