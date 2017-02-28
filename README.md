# gp-reviews-tgrm-bot

*gp-reviews-tgrm-bot* is Google Play application reviews monitoring Telegram bot.
It's written in Python using [Twisted](https://twistedmatrix.com/trac/) framework.

## Installation

*gp-reviews-tgrm-bot* runs on Python 2.7 or Python 3.4 and above.

Clone the repo in the directory of your choice using git:
```
git clone https://github.com/3cky/gp-reviews-tgrm-bot-git
cd gp-reviews-tgrm-bot-git
```

Next, install all needed Python requirements using [pip](https://pip.pypa.io/en/latest/) package manager:

`pip install --upgrade -r ./requirements.txt`

Then install *gp-reviews-tgrm-bot* itself:

`python setup.py install`

## Configuration

Before run this bot, you will have to create a configuration file. You could use
provided `doc/gp-reviews-tgrm-bot.cfg` as example. Minimal configuration includes specifying
Google account information needed for accessing Google API and Telegram token.

## Run

Run *gp-reviews-tgrm-bot* by command `twistd -n gp-reviews-tgrm-bot -c /path/to/config/file.cfg`.

## Commands

Use `/help` to get list of available commands.