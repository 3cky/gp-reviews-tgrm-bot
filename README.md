# gp-reviews-tgrm-bot

*gp-reviews-tgrm-bot* is Google Play applications reviews monitoring Telegram bot.
It's written in Python using [Twisted](https://twistedmatrix.com/trac/) framework.

## Installation

*gp-reviews-tgrm-bot* runs on Python 3.4 and above.

`virtualenv -p python3 gp-reviews-tgrm-bot`
`cd gp-reviews-tgrm-bot`
`source bin/activate`

Clone the repo in the directory of your choice using git:
`git clone https://github.com/3cky/gp-reviews-tgrm-bot-git`
`cd gp-reviews-tgrm-bot-git`

Next, install all needed Python requirements using [pip](https://pip.pypa.io/en/latest/) package manager:
`pip install -r ./requirements.txt`

Then install *gp-reviews-tgrm-bot* itself:

`python setup.py install`

## Configuration

Before run this bot, you will have to create a configuration file. You could use
provided `doc/gp-reviews-tgrm-bot.cfg` as example. Minimal configuration includes specifying
Google account information needed for accessing Google API, Telegram token and
list of application package names to monitor for reviews.

## Run

Run *gp-reviews-tgrm-bot* by command `twistd -n gp-reviews-tgrm-bot -c /path/to/config/file.cfg`

