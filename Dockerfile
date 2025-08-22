# Dockerfile
FROM quay.io/wikipedialibrary/python:3.11-bullseye-updated AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt update && apt install -y default-mysql-client && rm -rf /var/lib/apt/lists/* && rm -f /var/log/apt/*
# This file only exists once the code directory is mounted by docker-compose.

FROM base AS django
COPY requirements/django.txt requirements.txt
RUN pip install -r requirements.txt
ENV DJANGO_SETTINGS_MODULE=hashtagsv2.settings.production
ENTRYPOINT ["python", "wait_for_db.py"]

FROM django AS app
RUN pip install gunicorn

FROM base AS scripts
WORKDIR /scripts
COPY requirements/scripts.txt requirements.txt
RUN pip install -r requirements.txt
