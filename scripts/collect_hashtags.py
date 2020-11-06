import json
from sseclient import SSEClient as EventSource
import sys

from common import valid_hashtag, valid_edit, hashtag_match
import db

base_stream_url = 'https://stream.wikimedia.org/v2/stream/recentchange'

# Every time this script is started, find the latest entry in the database,
# and start the eventstream from there. This ensures that in the event of
# any downtime, we always maintain 100% data coverage (up to the ~30 days
# that the EventStream historical data is kept anyway).
latest_datetime = db.get_latest_datetime()

if latest_datetime[0]:
    latest_date_formatted = latest_datetime[0].strftime('%Y-%m-%dT%H:%M:%SZ')

    url = base_stream_url + '?since={date}'.format(
        date=latest_date_formatted)
else:
    url = base_stream_url

if len(sys.argv) > 1 and sys.argv[1] == 'nohistorical':
    url = base_stream_url

for event in EventSource(
        url,
        # The retry argument sets the delay between retries in milliseconds.
        # We're setting this to 5 minutes.
        # There's no way to set the max_retries value with this library,
        # but since it depends upon requests, which in turn uses urllib3
        # by default, we get a default max_retries value of 3.
        retry=300000,
        # The timeout argument gets passed to requests.get.
        # An integer value sets connect (socket connect) and
        # read (time to first byte / since last byte) timeout values.
        # A tuple value sets each respective value independently.
        # https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
        timeout=(3.05, 30)):
    if event.event == 'message':
        try:
            change = json.loads(event.data)
        except ValueError:
            continue

        hashtag_matches = hashtag_match(change['comment'])
        if hashtag_matches and valid_edit(change):
            for hashtag in hashtag_matches:
                if 'id' not in change:
                    print("Couldn't find recent changes ID in data. Skipping.")
                    continue
                if db.is_duplicate(hashtag, change['id']):
                    print("Skipped duplicate {hashtag} (rc_id = {id})".format(
                        hashtag=hashtag, id=change['id']))

                elif valid_hashtag(hashtag):
                    # Check edit_summary length, truncate if necessary
                    if len(change['comment']) > 800:
                        change['comment'] = change['comment'][:799]
                    db.insert_db(hashtag, change)
