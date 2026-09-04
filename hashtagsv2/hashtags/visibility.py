"""
Check that we may still show the edits we recorded.

We copy each edit into our database when it happens, and that copy never
changes. The wiki can hide the edit summary or the username later, or delete
the page. We therefore ask the wiki about the results before we show them.
See T277832.

The check fails closed: if we cannot get an answer, we do not show the row.
It also reports whether it reached every row, so that a caller which must not
send a part of a result, such as a download, can refuse instead.
"""

import logging
import time
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)

# The API takes 50 values in a multi-value parameter for clients that do not
# have the apihighlimits right. See https://www.mediawiki.org/wiki/API:Query
API_BATCH_SIZE = 50

# Connect and read timeouts for one request.
API_TIMEOUT_S = (3.05, 5)

# The most time we spend on API calls for one page of results. Results can
# span many wikis, and we must answer well inside the gunicorn worker
# timeout. We do not show the rows that we do not reach in time.
API_TOTAL_BUDGET_S = 10.0

API_USER_AGENT = "hashtags (https://hashtags.wmcloud.org)"

# The most rows that we check for one download. A download sends all of the
# results, not one page of them. A larger search needs more API calls than we
# can make before the request times out, so we refuse it.
EXPORT_VERIFY_LIMIT = 5000

# The most time that we spend on API calls for one download. This is larger
# than the budget for a page of results, because a download has many more
# rows. It stays well inside the gunicorn worker timeout.
EXPORT_TOTAL_BUDGET_S = 45.0

# The most API calls that we make for one download. The number of calls
# depends on how many wikis the results come from, not only on how many rows
# there are, so EXPORT_VERIFY_LIMIT cannot bound the time by itself: 5000
# rows from 362 wikis need 362 calls. We refuse a download that needs more.
EXPORT_MAX_BATCHES = 150

# What we treat as "we could not check this batch". The response comes from
# another service, so we include the errors that a malformed body causes: to
# show a row that we could not read is worse than to drop it.
CHECK_FAILURES = (
    requests.RequestException,
    AttributeError,
    KeyError,
    TypeError,
    ValueError,
)


def _query_wiki(domain, rev_ids):
    """Ask one wiki about up to API_BATCH_SIZE revisions."""
    response = requests.get(
        "https://{domain}/w/api.php".format(domain=domain),
        params={
            "action": "query",
            "prop": "revisions",
            "revids": "|".join(str(rev_id) for rev_id in rev_ids),
            # We must ask for the user and the comment. The API sends the
            # "userhidden" and "commenthidden" markers only for properties
            # that we request. We do not keep the values it sends back.
            "rvprop": "ids|user|comment|flags",
            "format": "json",
            "formatversion": "2",
        },
        headers={"User-Agent": API_USER_AGENT},
        timeout=API_TIMEOUT_S,
    )
    response.raise_for_status()
    return response.json()


def _read_response(data):
    """
    Map an API response to {rev_id: may_show_row}.

    A revision that the wiki does not report is left out, so that the caller
    treats it as unsafe to show.
    """
    if "error" in data:
        # MediaWiki reports some errors with HTTP 200 and an error object.
        # Without this we would read an empty result and quietly drop every
        # row, which looks the same as "the wiki hid them all".
        raise ValueError(
            "API error: {code}".format(code=data["error"].get("code", "unknown"))
        )

    may_show = {}
    query = data.get("query", {})

    # The wiki cannot find these. The revision is gone, or its page is
    # deleted. Either way the summary is no longer public.
    for rev_id in query.get("badrevids", {}):
        may_show[int(rev_id)] = False

    for page in query.get("pages", []):
        for revision in page.get("revisions", []):
            # We drop the whole row rather than redact one field. The hashtag
            # itself comes from the edit summary, and a blanked username can
            # still be confirmed with the user search filter.
            hidden = (
                revision.get("commenthidden", False)
                or revision.get("userhidden", False)
                or revision.get("suppressed", False)
            )
            may_show[int(revision["revid"])] = not hidden

    return may_show


def _count_batches(rev_ids_by_domain):
    """Count the API calls that a check of these revisions needs."""
    return sum(
        (len(rev_ids) + API_BATCH_SIZE - 1) // API_BATCH_SIZE
        for rev_ids in rev_ids_by_domain.values()
    )


def _check_wikis(rev_ids_by_domain, budget):
    """
    Ask each wiki about its revisions, within the time budget.

    Returns (may_show, complete). `may_show` is {(domain, rev_id):
    may_show_row}, and anything we did not resolve is left out. `complete` is
    False if we did not get an answer for every batch, either because we ran
    out of time or because a call failed.
    """
    may_show = {}
    complete = True
    deadline = time.monotonic() + budget

    for domain, rev_ids in rev_ids_by_domain.items():
        rev_ids = sorted(rev_ids)
        for start in range(0, len(rev_ids), API_BATCH_SIZE):
            if time.monotonic() > deadline:
                logger.warning(
                    "Ran out of time checking revision visibility. "
                    "The rows we did not reach will not be shown."
                )
                return may_show, False

            batch = rev_ids[start : start + API_BATCH_SIZE]
            try:
                found = _read_response(_query_wiki(domain, batch))
            except CHECK_FAILURES as error:
                # Leave the batch unresolved. We drop those rows below, and
                # we report the check as incomplete.
                logger.warning("Could not check revisions on %s: %s", domain, error)
                complete = False
                continue

            for rev_id, verdict in found.items():
                may_show[(domain, rev_id)] = verdict

    return may_show, complete


def redact(rows, budget=None, max_batches=None):
    """
    Remove the rows that the wiki no longer shows publicly.

    `rows` are the named tuples that hashtag_queryset() returns, for one page
    of results or for one download. `budget` is the most time in seconds that
    we spend on API calls. `max_batches` refuses the whole check before we
    make the first call, if the check needs more calls than this.

    Returns (rows_to_show, number_removed, complete). `complete` is False if
    we could not check every row. A caller which must not send a part of a
    result, such as a download, refuses when it sees this.
    """
    # We read the constant here, and not in the signature, so that it stays
    # the one place that sets the value.
    if budget is None:
        budget = API_TOTAL_BUDGET_S

    rows = list(rows)

    rev_ids_by_domain = defaultdict(set)
    for row in rows:
        if row.rev_id is not None:
            rev_ids_by_domain[row.domain].add(row.rev_id)

    # We count the calls before we make the first one, so that we refuse at
    # once instead of after we spend the whole budget.
    if max_batches is not None and _count_batches(rev_ids_by_domain) > max_batches:
        logger.warning(
            "A result set needs more than %s API calls to check. "
            "We did not check it.",
            max_batches,
        )
        return [], len(rows), False

    may_show, complete = _check_wikis(rev_ids_by_domain, budget)

    rows_to_show = []
    number_removed = 0

    for row in rows:
        # A row with no revision ID is a log action, such as an upload or a
        # page move. We have no key to check it with, so we do not show it.
        if may_show.get((row.domain, row.rev_id)):
            rows_to_show.append(row)
        else:
            number_removed += 1

    return rows_to_show, number_removed, complete
