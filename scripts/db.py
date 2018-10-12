import mysql.connector

hashtag_db = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    passwd='hashtag',
    database='hashtagsv2_db'
)


def insert_db(hashtag, change):
    cursor = hashtag_db.cursor()
    cursor.execute('SET NAMES utf8mb4')
    cursor.execute('SET CHARACTER SET utf8mb4')
    cursor.execute('SET character_set_connection=utf8mb4')
    query = """
        INSERT INTO hashtags_hashtag
        (hashtag, domain, timestamp, username, page_title,
        edit_summary, rc_id)
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

def is_duplicate(hashtag, rc_id):
    """
    We can't make diff or event id a unique key, because we're creating
    a db row per hashtag use, not per diff. As such, we need to check if
    this hashtag + diff combo has been logged already.
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