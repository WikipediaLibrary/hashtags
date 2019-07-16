import mysql.connector
import os

hashtag_db = mysql.connector.connect(
    host='db',
    user='root',
    passwd=os.environ['MYSQL_ROOT_PASSWORD'],
    database=os.environ['MYSQL_DATABASE']
)


def insert_db(hashtag, change):
    cursor = hashtag_db.cursor()
    cursor.execute('SET NAMES utf8mb4')
    cursor.execute('SET CHARACTER SET utf8mb4')
    cursor.execute('SET character_set_connection=utf8mb4')
    query = """
        INSERT INTO hashtags_hashtag
        (hashtag, domain, timestamp, username, page_title,
        edit_summary, rc_id, rev_id)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s)
        """

    dt_without_plus = change['meta']['dt'][:19]
    change_dt = dt_without_plus.replace("T", " ")

    # Log actions such as page moves and image uploads have no
    # revision ID.
    try:
        revision_id = change['revision']['new']
    except KeyError:
        revision_id = None

    values = (
        hashtag,
        change['meta']['domain'],
        change_dt,
        change['user'],
        change['title'],
        change['comment'],
        change['id'],
        revision_id
        )

    try:
        cursor.execute(query, values)
    except mysql.connector.errors.IntegrityError:
        print("Skipped rc_id {rc_id} due to integrity error".format(
            rc_id=change['id']
        ))
        return False

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


def is_duplicate(hashtag, rc_id):
    """
    We can't make diff or event id a unique key, because we're creating
    a db row per hashtag use, not per diff. As such, we need to check if
    this hashtag + diff combo has been logged already.
    We use rc_id because not all logged edits have a rev_id, such as page
    moves or image uploads.
    """
    cursor = hashtag_db.cursor()
    query = """
        SELECT COUNT(*) FROM hashtags_hashtag
        WHERE hashtag = %s
        AND rc_id = %s
        """

    cursor.execute(query, (hashtag, rc_id))

    if cursor.fetchone()[0] == 0:
        return False
    else:
        return True
