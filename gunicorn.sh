#!/bin/bash

# Prepare log files and start outputting logs to stdout
touch ./gunicorn.log
touch ./gunicorn-access.log
tail -n 0 -f ./gunicorn*.log &

exec gunicorn hashtagsv2.wsgi:application \
    --name hashtagsv2_django \
    --bind 0.0.0.0:8000 \
    --workers 5 \
    --log-level=info \
    --log-file=./gunicorn.log \
    --access-logfile=./gunicorn-access.log \
"$@"
