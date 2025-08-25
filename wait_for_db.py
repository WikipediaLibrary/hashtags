import os
import sys
import time
from mysql.connector import connect


def has_connection(timeout=5, attempt_every=10):
    start_time = time.monotonic()
    connected = False
    wait = False
    while not connected:
        if wait is True:
            print("Waiting for DB.")
            time.sleep(attempt_every)
        if wait is False:
            wait = True
        if (time.monotonic() - start_time) > timeout:
            raise TimeoutError("Connection timed out.")
        with connect(
            user="root",
            password=os.environ["MYSQL_ROOT_PASSWORD"],
            host="db",
            database=os.environ["MYSQL_DATABASE"],
        ) as cnx:
            with cnx.cursor() as cursor:
                cursor.close()
            cnx.close()
        connected = True
        print("Connected to DB.")


has_connection()

prog = sys.argv[1]
args = sys.argv[2:]

try:
    os.execvp(prog, [prog] + args)
except Exception as e:
    raise Exception(
        "Error running {prog} {args}:\n{e}".format(prog=prog, args=args, e=e)
    )
