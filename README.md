[![Build Status](https://travis-ci.org/WikipediaLibrary/hashtags.svg?branch=master)](https://travis-ci.org/WikipediaLibrary/hashtags)
[![codecov](https://codecov.io/gh/Samwalton9/hashtags/branch/master/graph/badge.svg)](https://codecov.io/gh/Samwalton9/hashtags)

# Hashtags

This tool is a rewrite of the Hatnote Hashtags tool.

## Version 2?

The tool should do most if not all of what the [previous tool](https://github.com/hatnote/hashtag-search) did but with some changes and improvements:

Most notably, this version monitors the [recentchanges EventStream](https://wikitech.wikimedia.org/wiki/EventStreams) rather than periodically reading from the recentchanges database. This means all Wikimedia projects and languages are monitored (except Wikidata, see below), and new hashtag uses are ingested into the tool's database almost as soon as they happen.

This version of the tool runs on Django, rather than Flask. No important reason for this, it's just the framework Sam knows best. This does mean that the backend has almost separate code to the old tool.

Bot edits are excluded. One of the reasons the old Hashtags tool slowed to a crawl and had to be taken down was the huge number of bot edits that made their way into the database. While in an ideal world we would collect these too, it's simply too easy to overload the database with millions of entries that very few people are interested in. If individual bot edits need to be tracked, the better solution would be to do so directly via the bot or by looking at the bot account's contributions.

Wikidata is currently excluded too, for similar reasons. A huge number of automated or semi-automated edits happen there utilising hashtag edit summaries, and from initial testing it looked like similar problems were going to present themselves. This will be revisited once the tool is up and running and stable.

This tool is also running on a Horizon VPS instance, rather than Toolforge, to ensure it has the database resources it needs and doesn't disrupt other tools.

# Local development


Contributions to the tool are welcomed! A list of open tasks can be found on the tool's [Phabricator workboard](https://phabricator.wikimedia.org/project/view/3229/)


The tool uses the [Django framework](https://www.djangoproject.com/) and is deployed via [Docker](https://www.docker.com/). Docker and docker compose are required for local setup.

After cloning the repository to your directory of choice:
1. Copy `template.env` to `.env`. No further changes are required for local development.
2. Run `docker compose up -d --build` to build and run containers in detached mode. If you want to enable the [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/index.html), you should run `docker compose build --build-arg REQUIREMENTS_FILE=local.txt && docker compose up`

You should now be able to access the tool in your browser on `http://localhost`.

## Running tests

The tests can be run within the container using docker exec. The following command will run the test suite:

```bash
docker compose exec app python manage.py test
```

If you would like to generate a coverage report as well, you can invoke the test runner using `coverage run` instead:

```bash
docker compose exec app coverage run manage.py test
```

You can view this report in your browser (located at `htmlcov/index.html`) by running the following command:

```bash
docker compose exec app coverage html
```

## Debugging

This section has instructions for attaching [gdb](https://www.gnu.org/software/gdb/) to the `collect_hashtags.py` script and use its [Python tooling](https://devguide.python.org/gdb/) to inspect the state of the process.

This is helpful in case the script appears to be stuck so we can determine what it is trying to do.

Open a privileged shell in the scripts container:

```
docker compose exec --privileged scripts bash
```

The next steps should all be run in that terminal, inside the container.

Install gdb and a text editor of your choosing with:

```
apt update && apt install -y gdb vim
```

Download the source code for the Python version used in the scripts:

```
wget https://www.python.org/ftp/python/3.11.13/Python-3.11.13.tgz -O - | tar -xzvf -
```

The version (3.11.13, in this case) should match the one in the `Dockerfile-scripts` file in this repository.

Now, copy the Python gdb library to a suitable place where gdb can find it:

```
cp Python-3.11.13/Tools/gdb/libpython.py /usr/local/bin/python3.11-gdb.py
```

Edit `/root/.gdbinit` so it looks like this:

```
add-auto-load-safe-path /usr/local/bin/python3.11-gdb.py
set auto-load python-scripts on
```

Find the process ID of the script through any of the usual means (e.g. `pgrep -lf python`, or `top`).

Finally, you can attach gdb to the process with:

```
gdb python <pid>
```

Try running `py-bt` to view the stack, `py-up`/`py-down` to navigate it, and `py-locals` to view local variables!
