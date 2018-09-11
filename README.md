#Hashtags

This tool is a rewrite of the Hatnote Hashtags tool.

##Differences

The tool should do most if not all of what the previous tool did but with some changes and improvements:

Most notably, this version monitors the recentchanges EventStream (https://wikitech.wikimedia.org/wiki/EventStreams) rather than periodically reading from the recentchanges database. This means all Wikimedia projects and languages are monitored (except Wikidata, see below), and new hashtag uses are ingested into the tool's database almost as soon as they happen.

This version of the tool runs on Django, rather than Flask. No important reason for this, it's just the framework Sam knows best.

Bot edits are excluded. One of the reasons the old Hashtags tool slowed to a crawl and had to be taken down was the huge number of bot edits that made their way into the database. While in an ideal world we would collect these too, it's simply too easy to overload the database with millions of entries that very few people are interested in. If individual bot edits need to be tracked, the better solution would be to do so directly via the bot or by looking at the bot account's contributions.

Wikidata is currently excluded too, for similar reasons. A huge number of automated or semi-automated edits happen there utilising hashtag edit summaries, and from initial testing it looked like similar problems were going to present themselves. This will be revisited once the tool is up and running and stable.

This tool is also running on a Horizon VPS instance, rather than Toolforge, to ensure it has the database resources it needs and doesn't disrupt other tools.

##Setup

TODO.