# Dockerfile
FROM quay.io/wikipedialibrary/python:3.11-bullseye-updated AS base
ENV PYTHONUNBUFFERED=1
RUN apt update && apt install -y default-mysql-client && rm -rf /var/lib/apt/lists/* && rm -f /var/log/apt/*
COPY requirements/* .
RUN pip install -r base.txt
# This file only exists once the code directory is mounted by docker-compose.
ENTRYPOINT ["python", "wait_for_db.py"]

FROM base AS django
ENV DJANGO_SETTINGS_MODULE=hashtagsv2.settings.production PATH=/app:$PATH
ARG REQUIREMENTS_FILE
ENV REQUIREMENTS_FILE=${REQUIREMENTS_FILE:-django.txt}
RUN pip install -r $REQUIREMENTS_FILE
WORKDIR /app

FROM django AS app
RUN pip install gunicorn

FROM django AS cron
RUN apt update && apt install -y cron && rm -rf /var/lib/apt/lists/* && rm -f /var/log/apt/*

FROM base AS scripts
ENV PATH=/scripts:$PATH
RUN pip install -r scripts.txt
WORKDIR /scripts
