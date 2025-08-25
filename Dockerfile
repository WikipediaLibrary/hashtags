# Dockerfile
FROM quay.io/wikipedialibrary/python:3.11-bullseye-updated AS base
ENV PYTHONUNBUFFERED=1
RUN apt update && apt install -y default-mysql-client && rm -rf /var/lib/apt/lists/* && rm -f /var/log/apt/*
COPY requirements/base.txt requirements.txt
RUN pip install -r requirements.txt
# This file only exists once the code directory is mounted by docker-compose.
ENTRYPOINT ["python", "wait_for_db.py"]

FROM base AS django
ENV DJANGO_SETTINGS_MODULE=hashtagsv2.settings.production PATH=/app:$PATH
WORKDIR /app
COPY requirements/django.txt requirements.txt
RUN pip install -r requirements.txt

FROM django AS app
RUN pip install gunicorn

FROM base AS scripts
ENV PATH=/scripts:$PATH
WORKDIR /scripts
COPY requirements/scripts.txt requirements.txt
RUN pip install -r requirements.txt
