import mysql.connector

from project_settings import (
        DB_HOST,
        DB_USER,
        DB_PASSWORD,
        DB_NAME
    )

hashtag_db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    passwd=DB_PASSWORD,
    database=DB_NAME
)


def insert_db(hashtag, change):
    cursor = hashtag_db.cursor()
    query = """
        INSERT INTO hashtags_hashtag
        (hashtag, domain, timestamp, username, page_title,
        edit_summary, diff_id)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s)
        """

    dt_without_plus = change['meta']['dt'].split("+")[0]
    change_dt = dt_without_plus.replace("T", " ")
    values = (
        hashtag,
        change['meta']['domain'],
        change_dt,
        change['user'],
        change['title'],
        change['comment'],
        change['id'])

    cursor.execute(query, values)

    hashtag_db.commit()


def get_latest_datetime():
    """
    Find the most recent logged hashtag, for use when collecting hashtags
    from historical EventStream following downtime.
    """
    cursor = hashtag_db.cursor()
    query = "SELECT MAX(timestamp) FROM hashtags_hashtag"

    cursor.execute(query)

    return cursor.fetchone()

def is_duplicate(hashtag, diff_id):
    """
    We can't make diff or event id a unique key, because we're creating
    a db row per hashtag use, not per diff. As such, we need to check if
    this hashtag + diff combo has been logged already.
    """
    cursor = hashtag_db.cursor()
    query = """
        SELECT COUNT(*) FROM hashtags_hashtag
        WHERE hashtag = %s
        AND diff_id = %s
        """

    cursor.execute(query, (hashtag, diff_id))

    if cursor.fetchone()[0] == 0:
        return False
    else:
        return True