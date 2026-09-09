import os
import sys
import time
from mysql.connector import connect, Error

# Bounds each individual connect() attempt so a stalled handshake (e.g. the
# mariadb temp-server init phase) can't block past attempt_every.
CONNECTION_ATTEMPT_TIMEOUT_S = 5


def has_connection(timeout=120, attempt_every=10):
    start_time = time.monotonic()
    while True:
        try:
            with connect(
                user="root",
                password=os.environ["MYSQL_ROOT_PASSWORD"],
                host="db",
                database=os.environ["MYSQL_DATABASE"],
                connection_timeout=CONNECTION_ATTEMPT_TIMEOUT_S,
            ) as cnx:
                with cnx.cursor():
                    pass
            print("Connected to DB.")
            return
        except Error as e:
            if (time.monotonic() - start_time) > timeout:
                raise TimeoutError("Connection timed out.") from e
            print("Waiting for DB: {}".format(e))
            time.sleep(attempt_every)


has_connection()

prog = sys.argv[1]
args = sys.argv[2:]

try:
    os.execvp(prog, [prog] + args)
except Exception as e:
    raise Exception(
        "Error running {prog} {args}:\n{e}".format(prog=prog, args=args, e=e)
    )
