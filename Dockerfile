# Dockerfile
FROM python:3.5.2
WORKDIR /app
COPY hashtagsv2 hashtagsv2
COPY manage.py requirements.txt /app/

RUN mkdir logs

RUN pip install -r requirements.txt && \
        python manage.py collectstatic --noinput
RUN pip install gunicorn

WORKDIR /app
COPY ./gunicorn.sh /

ENTRYPOINT ["/gunicorn.sh"]
