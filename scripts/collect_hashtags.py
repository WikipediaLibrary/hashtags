import datetime
import functools
import json
from sseclient import SSEClient as EventSource
import sys

from common import valid_hashtag, valid_edit, hashtag_match
import db

import mwapi

@functools.lru_cache(maxsize=None)
def get_wiki_session(domain):
    return mwapi.Session(
        'https://{}/'.format(domain), 'hashtags')

def query_media_in_revision(session, rev_id):
    images_args = {
        'action': 'parse',
        'prop': 'images',
        'oldid': rev_id,
    }
    try:
        media_filenames = set(session.get(**images_args)['parse']['images'])
    except mwapi.errors.APIError as e:
        if e.code == 'nosuchrevid':
            # Deleted page?
            pass
        raise
    return media_filenames

def query_media_types(session, media_filenames):
    def query_imageinfo(titles, iistart = None):
        imageinfo_args = {
            'action': 'query',
            'prop': 'imageinfo',
            'titles': '|'.join(titles),
            'iiprop': 'mediatype|url',
        }
        if iistart is not None:
            imageinfo_args['iistart'] = iistart
        return session.get(**imageinfo_args)

    media_types = set()
    media_filenames = list(media_filenames)
    while media_filenames:
        iistart = None
        # Query the API 50 files at a time.
        # See https://www.mediawiki.org/wiki/API:Query for this limit.
        titles = ['File:' + f for f in media_filenames[:50]]
        while True:
            result = query_imageinfo(titles, iistart)
            for m in result['query']['pages'].values():
                if 'imageinfo' not in m:
                    # Broken link
                    continue
                if 'mediatype' not in m['imageinfo'][0]:
                    # Probably filehidden?
                    continue
                media_types.add(m['imageinfo'][0]['mediatype'])
            if 'continue' in result:
                iistart = result['continue']['iistart']
            else:
                break
        media_filenames = media_filenames[50:]
    return media_types

def populate_media_information(change):
    change['has_image'] = False
    change['has_video'] = False
    if 'revision' not in change:
        return
    new_rev = change['revision']['new']
    old_rev = change['revision'].get('old', None)

    try:
        session = get_wiki_session(change['meta']['domain'])
        new_media = query_media_in_revision(session, new_rev)
        old_media = set()
        if new_media and old_rev is not None:
            old_media = query_media_in_revision(session, old_rev)

        added_media = new_media - old_media
        if added_media:
            added_media_types = query_media_types(session, added_media)
            change['has_image'] = bool(
                    set(['DRAWING', 'BITMAP']) & added_media_types)
            change['has_video'] = 'VIDEO' in added_media_types
    except Exception as e:
        print('Failed to query media: {}. Change: {}'.format(e, change))


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
                    continue
                if not valid_hashtag(hashtag):
                    continue
                # Check edit_summary length, truncate if necessary
                if len(change['comment']) > 800:
                    change['comment'] = change['comment'][:799]
                populate_media_information(change)
                db.insert_db(hashtag, change)
