from haystack import indexes
from .models import Hashtag


class HashtagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    domain = indexes.CharField(model_attr='domain')
    timestamp = indexes.DateTimeField(model_attr='timestamp')
    username = indexes.CharField(model_attr='username')
    page_title = indexes.CharField(model_attr='page_title')
    edit_summary = indexes.CharField(model_attr='edit_summary')
    rev_id = indexes.IntegerField(null=True, model_attr='rev_id')

    def get_model(self):
        return Hashtag
