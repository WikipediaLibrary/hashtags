import re

# From https://github.com/hatnote/hashtag-search/blob/1e02506a732b3e018521c431c4b5c3f3c0618215/common.py
EXCLUDED_LITERAL = ('redirect',
            'weiterleitung',
            'redirection',
            'ifexist',
            'switch',
            'ifexpr',
            'if',
            'rs',
            'default',
            'mw',
            # Too many edits & easily trackable via tags on Commons
            'flickr2commons',
            # T361675
            'quickstatements',
)

EXCLUDED_RE = (
        # T361675
        re.compile("^temporary_batch_[0-9]{13}$"),
)


# exclude tags based on pattern match
def __excluded_re(hashtag):
    for pattern in EXCLUDED_RE:
        if pattern.fullmatch(hashtag):
            return True
    return False


def hashtag_match(comment):
    # Save some time by discarding this edit if it doesn't have
    # a hashtag symbol at all
    if "#" not in comment and "＃" not in comment:
        return None

    # Now do regex to see if it's a valid hashtag
    # From https://gist.github.com/mahmoud/237eb20108b5805aed5f
    hashtag_re = re.compile("(?:^|\s)[＃#]{1}(\w+)")

    return hashtag_re.findall(comment)


def valid_hashtag(hashtag):

    # not a string
    if type(hashtag) is not str:
        return False

    # only numbers
    if hashtag.isdigit():
        return False

    # too short
    if len(hashtag) < 2:
        return False

    # exluded literal
    if hashtag.lower() in EXCLUDED_LITERAL:
        return False

    # excluded pattern
    if __excluded_re(hashtag.lower()):
        return False

    # Otherwise valid
    return True


def valid_edit(change):

    # Exclude Wikidata for now, just far too much data
    project_match = change['meta']['domain'] != "www.wikidata.org"

    # Excluding bots, mostly because of IABot. Lots of data, not very useful.
    not_bot = not change['bot']

    return all([project_match, not_bot])
