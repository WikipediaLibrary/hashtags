#!/usr/bin/python
# -*- coding: utf-8 -*-
import re

EXCLUDED = ('redirect', # #REDIRECT in various languages
            'weiterleitung',
            'redirection',
            'redirección',
            'doorverwijzing',
            'redirecionamento',
            'omdirigering',
            'ifexist', # Other magic words and template syntax
            'switch',
            'ifexpr',
            'if',
            'rs',
            'mw',
            'default')


def hashtag_match(comment):
	# From https://gist.github.com/mahmoud/237eb20108b5805aed5f
	hashtag_re = re.compile("(?:^|\s)[＃#]{1}(\w+)")

	return hashtag_re.findall(comment)


def valid_hashtag(hashtag):

    not_excluded = hashtag.lower() not in EXCLUDED
    not_only_numbers = not hashtag.isdigit()
    not_only_one_character = len(hashtag) > 1

    return all([not_excluded, not_only_numbers, not_only_one_character])


def valid_edit(change):

    # Exclude Wikidata for now, just far too much data
    project_match = change['meta']['domain'] != "www.wikidata.org"

    # Excluding bots, mostly because of IABot. Lots of data, not very useful.
    not_bot = not change['bot']

    return all([project_match, not_bot])