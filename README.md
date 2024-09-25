# Basketball Reference Data Scraper

[Basketball Reference](https://www.basketball-reference.com/) is a resource to aggregate statistics on NBA teams, seasons, players, and games. This package provides methods to acquire data for all these categories in pre-parsed and simplified formats.

## Summary

The primary API used currently is for [stats.nba.com](https://stats.nba.com/), but the website blocks too many requests, hindering those who want to acquire a lot of data. Additionally, scrapers for [Basketball Reference](https://www.basketball-reference.com/) do exist, but none of them load dynamically rendered content. These scrapers can only acquire statically loaded content, preventing those who want statistics in certain formats (for example, Player Advanced Stats Per Game).

Most of the scrapers use outdated methodologies of scraping from `'https://widgets.sports-reference.com/'`. This is outdated and Basketball Reference no longer acquires their data from there. Additionally, [Sports Reference recently instituted a rate limiter](https://www.sports-reference.com/bot-traffic.html) preventing users from making an excess of 20 requests/minute. This package abstracts the waiting logic to ensure you never hit this threshold.

## Prerequisites
 To deploy this CDK Application you will need the following
 - [Python 3.12+](https://www.python.org/downloads/)
 - [Poetry](https://python-poetry.org/)
 

### Local Setup
Note: A `Makefile` is included in this project to wrap commands. 
You can review the available commands using `make help`  

To initialize the environment to run this sample:

```
$ make init
```

NOTE: To add additional dependencies, for example other libraries, you will need to run a `poetry` command.

```
$ poetry add <package_name>
```

At this point you can now build the Python package for this code.

```
$ make build
```

### Testing
There are basic unit tests included that can be run using the following command:

```
$ make test
```
Unit Tests for this project are located in the `tests` folder 

### Via GitHub
Alternatively, you can just clone this repo and import the libraries at your own discretion.

### Selenium

This package can also capture dynamically rendered content that is being added to the page via JavaScript, rather than baked into the HTML. To achieve this, it uses [Python Selenium](https://selenium-python.readthedocs.io/). Please refer to their [installation instructions](https://selenium-python.readthedocs.io/installation.html) and ensure you have [Chrome webdriver](https://selenium-python.readthedocs.io/installation.html#drivers) installed in and in your `PATH` variable.

### API
Currently, the package contains 5 modules: `teams`, `players`, `seasons`, `box_scores`, `pbp`, `shot_charts`, and `injury_report`. 
The package will be expanding to include other content as well, but this is a start.

For full details on the API please refer to the [documentation](https://github.com/aabragan/basketball_reference_scraper/blob/main/README.md).


## Credit
This repository is a **fork** of the work done in this [repository](https://github.com/vishaalagartha/basketball_reference_scraper). This repository can build a package but it is not currently published anywhere

### Key differences
- upgraded to use Python 3.12
- changed to use Poetry for project/package management
- fixed and updated unit tests
- adding new methods to enhance functionality
- bumped the package version to 3.x.x because of the number of changes