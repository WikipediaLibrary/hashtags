from urllib.parse import urlencode
from django import template

# Borrowed from https://stackoverflow.com/a/36288962 to retain
# GET parameters between pages

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context["request"].GET.dict()
    query.update(kwargs)
    return urlencode(query)
