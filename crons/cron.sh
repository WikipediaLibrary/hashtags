#!/usr/bin/env bash
# copy crontab, set permissions, and start cron
set -eo pipefail
PATH=/app/crons:/app:/usr/local/bin:/usr/bin:/bin:/sbin:$PATH
cp /app/crons/crontab /etc/crontab
# `root:wikidev` only; using IDs instead of names to avoid problems in localdev
chown 0:500 /etc/crontab
chmod 640 /etc/crontab
echo "Starting cron."
cron -f -L 8
