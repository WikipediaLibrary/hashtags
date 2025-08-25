import csv
import mysql.connector

from common import EXCLUDED

hashtag_db = mysql.connector.connect(
    host="localhost", user="hashtag", passwd="hashtag", database="hashtag"
)


def generate_csv():
    cursor = hashtag_db.cursor()

    # For some reason ClueBot NG was not correctly bot flagged, accounting
    # for ~500,000 entries, and InternetArchiveBot has ~1500 incorrectly
    # flagged entries.
    # This also skips all purely numeric hashtags, and filters automated
    # edit summaries (WP:AES)
    query = """
		SELECT ht_text, htrc_lang, rc_timestamp, rc_user_text, rc_title, rc_comment, rc_id, rc_bot
		FROM recentchanges as rc
		JOIN hashtag_recentchanges AS htrc
		ON htrc.htrc_id = rc.htrc_id
		JOIN hashtags as ht
		ON ht.ht_id = htrc.ht_id
		WHERE rc.rc_bot = 0
		AND rc.rc_user_text <> "ClueBot NG"
		AND rc.rc_user_text <> "InternetArchiveBot"
		AND ht.ht_text REGEXP '[[:alpha:]]{1}[[:alnum:]]+'
		AND rc.rc_comment NOT LIKE "%WP:AES%"
		"""

    cursor.execute(query)

    print("Starting import")
    with open("hashtags_temp.csv", "w") as hashtag_csv:
        csv_writer = csv.writer(hashtag_csv)
        for row in cursor:
            try:
                x = row[0].decode()
            except UnicodeDecodeError as e:
                print(e)
                print("zero:", row[0])
                continue
            # Don't bother importing anything that was later excluded in v1
            # Also strip all bot entries.
            if row[0].decode().lower() not in EXCLUDED:
                row_dt = row[2].decode()
                formatted_dt = "{y}-{m}-{d} {h}:{M}:{s}".format(
                    y=row_dt[:4],
                    m=row_dt[4:6],
                    d=row_dt[6:8],
                    h=row_dt[8:10],
                    M=row_dt[10:12],
                    s=row_dt[12:14],
                )

                try:
                    values = (
                        row[0].decode(),
                        row[1].decode() + ".wikipedia.org",
                        formatted_dt,
                        row[3].decode(),
                        row[4].decode(),
                        row[5].decode(),
                        row[6],
                    )
                # Some entries are corrupted, likely due to
                # character limits on extremely long edit
                # summaries.
                except UnicodeDecodeError as e:
                    # print("Failed to decode entry.")
                    # print(row)
                    continue

                csv_writer.writerow(values)


# The intermediate csv step is required to prevent having to load all
# the data into memeory, and mysql.connector can't loop through while
# also inserting values.
def csv_to_db():
    with open("hashtags_temp.csv", "r") as hashtag_csv:
        csv_reader = csv.reader(hashtag_csv)
        counter = 0

        cursor = hashtag_db.cursor()
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        for row in csv_reader:

            query = """
			    INSERT INTO hashtags_hashtag
			    (hashtag, domain, timestamp, username, page_title,
			    edit_summary, rc_id)
			    VALUES
			    (%s, %s, %s, %s, %s, %s, %s)
			    """

            cursor.execute(query, row)

            hashtag_db.commit()
            counter += 1

    print("Imported {num} entries.".format(num=counter))


# generate_csv()
csv_to_db()
