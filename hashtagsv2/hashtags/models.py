from django.db import models


class Hashtag(models.Model):
    """
    Hashtags model, based on the db schema for the original hashtags tool.
    We should always be gathering every piece of the model - edit summary
    is optional, but we shouldn't be logging anything with no summary.
    """
    hashtag = models.CharField(max_length=128, db_index=True)

    # Hashtags v1 only recorded language Wikipedia project. Recording
    # the entire domain allows us to track edits to other projects too.
    domain = models.CharField(max_length=32)

    # We sometimes do date-based queries, like when finding the top tags for the
    # last month. An index on the timestamp speeds up those queries.
    timestamp = models.DateTimeField(db_index=True)
    username = models.CharField(max_length=255)
    page_title = models.CharField(max_length=500)

    # Per https://meta.wikimedia.org/wiki/Help:Edit_summary, summaries
    # have a maximum possible length of 800 characters.
    edit_summary = models.CharField(max_length=800)

    # Recentchanges ID
    # (https://www.mediawiki.org/wiki/Manual:Recentchanges_table)
    rc_id = models.PositiveIntegerField()

    # Revision ID (https://www.mediawiki.org/wiki/Manual:Revision_table)
    rev_id = models.PositiveIntegerField(null=True)

    # Whether this change introduces different media in the page.
    has_image = models.BooleanField(default=False)
    has_video = models.BooleanField(default=False)
    has_audio = models.BooleanField(default=False)

    def get_values_list(self):
        # When returning hashtag results we're using a values_list rather than
        # a full queryset so that multiple hashtag searches can be properly
        # supported without returning duplicates. As such, it can be useful
        # to access the 'values_list' for an individual object, such as
        # when testing
        return Hashtag.objects.filter(pk=self.pk).values_list(
            'domain', 'timestamp', 'username', 'page_title', 'edit_summary',
            'rc_id', 'rev_id', 'has_image', 'has_video', 'has_audio',
            named=True
        )[0]

    class Meta:
        # Indexes we need for computing statistics.
        index_together = [
            ('hashtag', 'timestamp'),
            ('hashtag', 'rev_id'),
            ('hashtag', 'domain', 'page_title'),
            ('hashtag', 'username'),
        ]
