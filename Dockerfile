# Dockerfile
FROM python:3.5.2

ENV DJANGO_SETTINGS_MODULE=hashtagsv2.settings.development

WORKDIR /app
COPY hashtagsv2 hashtagsv2
COPY manage.py requirements.txt /app/

RUN mkdir logs

RUN pip install -r requirements.txt
RUN pip install gunicorn

WORKDIR /app
COPY ./gunicorn.sh /

ENTRYPOINT ["/gunicorn.sh"]
