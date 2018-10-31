# Dockerfile
FROM python:3.5.2

ADD . /scripts
WORKDIR /scripts

COPY requirements/scripts.txt /scripts/

RUN pip install -r requirements/scripts.txt

CMD ["python", "scripts/collect_hashtags.py", "nohistorical"]
