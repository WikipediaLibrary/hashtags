from .base import *

ALLOWED_HOSTS += ["172.16.1.222", "hashtags.wmflabs.org", "hashtags.wmcloud.org"]

DEBUG = False

# Redirect HTTP to HTTPS
# SECURE_PROXY_SSL_HEADER is required because we're behind a proxy
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
