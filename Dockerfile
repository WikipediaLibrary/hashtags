# Dockerfile
FROM python:3.5.2

ENV DJANGO_SETTINGS_MODULE=hashtagsv2.settings.development

WORKDIR /app
COPY . hashtagsv2
COPY manage.py requirements/django_app.txt /app/

RUN mkdir logs

RUN pip install -r django_app.txt
RUN pip install gunicorn

WORKDIR /app
COPY ./gunicorn.sh /

ENTRYPOINT ["/gunicorn.sh"]
