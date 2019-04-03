from datetime import datetime
from datetime import timedelta

from .models import Hashtag

def split_hashtags(hashtag_list):
    split_hashtags_list = hashtag_list.split(",")
    stripped_hashtags = [x.strip() for x in split_hashtags_list]

    # Strip # from hashtags if entered
    final_hashtags = [x[1:] if x.startswith("#") else x for x in stripped_hashtags]

    return final_hashtags
