# Dockerfile
FROM python:3.5.2
WORKDIR /app
COPY hashtagsv2 hashtagsv2
COPY manage.py requirements.txt /app/
RUN pip install -r requirements.txt && \
        python manage.py collectstatic --noinput
EXPOSE 8001
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
