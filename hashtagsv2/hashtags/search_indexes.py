from haystack import indexes
from .models import Hashtag


class HashtagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    domain = indexes.CharField(model_attr='domain')
    timestamp = indexes.DateTimeField(model_attr='timestamp')

    def get_model(self):
        return Hashtag
