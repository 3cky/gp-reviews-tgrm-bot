# -*- coding: utf-8 -*-
'''
Created on 20-Jan-2017

@author: 3cky
'''

import os

from zope.interface import implementer

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import service

from TelegramBot.service.bot import BotService
from TelegramBot.client.twistedclient import TwistedClient as TelegramClient

from tgrmbot.bot import Bot
from tgrmbot.db import DataStorage
from tgrmbot.watcher import GpReviewsWatcher
from tgrmbot.template import TemplateRenderer
from tgrmbot.locale import LocalizationSupport

from configparser import ConfigParser

import codecs

import humanfriendly


import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

TAP_NAME = "gp-reviews-tgrm-bot"

DEFAULT_DB_FILENAME = 'db.sqlite'

DEFAULT_NICKNAME = TAP_NAME

DEFAULT_POLL_PERIOD = 600 # 10m
DEFAULT_POLL_DELAY = 5

DEFAULT_LANG = 'en'

class ConfigurationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class Options(usage.Options):
    optParameters = [["config", "c", None, 'Configuration file name']]


@implementer(IServiceMaker, IPlugin)
class ServiceManager(object):
    tapname = TAP_NAME
    description = "Telegram notifications about Google Play apps reviews."
    options = Options
    mucNotifiers = []
    apps = []
    gp_langs = []

    def makeService(self, options):
        # create Twisted application
        application = service.Application(TAP_NAME)
        serviceCollection = service.IServiceCollection(application)

        # check confguration file is specified and exists
        if not options["config"]:
            raise ValueError('Configuration file not specified (try to check --help option)')
        cfgFileName = options["config"];
        if not os.path.isfile(cfgFileName):
            raise ConfigurationError('Configuration file not found:', cfgFileName)

        # read configuration file
        cfg = ConfigParser()
        with codecs.open(cfgFileName, 'r', encoding='utf-8') as f:
            cfg.readfp(f)

        # get Google login and password from configuration
        if not cfg.has_option('google', 'login') or not cfg.has_option('google', 'password'):
            raise ConfigurationError('Google account login and password must be specified '
                                     'in configuration file [account] section')
        googleLogin = cfg.get('google', 'login')
        googlePassword = cfg.get('google', 'password')
        # get ANDROID_ID from configuration
        if not cfg.has_option('google', 'android_id'):
            raise ConfigurationError('ANDROID_ID must be specified in configuration file [account] section')
        androidId = cfg.get('google', 'android_id')

        # get Telegram token from configuration
        if not cfg.has_option('telegram', 'token'):
            raise ConfigurationError('Telegram API token must be specified in configuration file [telegram] section')
        token = cfg.get('telegram', 'token')

        # default language
        default_lang = DEFAULT_LANG
        if cfg.has_option('i18n', 'lang'):
            default_lang = cfg.get('i18n', 'lang')

        l10n_support = LocalizationSupport(default_lang)

        templateRenderer = TemplateRenderer(l10n_support)

        # initialize data storage
        dbFilename = cfg.get('db', 'filename') if cfg.has_option('db', 'filename') else DEFAULT_DB_FILENAME
        db = DataStorage(dbFilename)

        pollPeriod = humanfriendly.parse_timespan(cfg.get('poll', 'period')) \
                if cfg.has_option('poll', 'period') else DEFAULT_POLL_PERIOD
        pollDelay = humanfriendly.parse_timespan(cfg.get('poll', 'delay')) \
                if cfg.has_option('poll', 'delay') else DEFAULT_POLL_DELAY
        langs = [lang.strip() for lang in cfg.get('poll', 'lang').split(',')] \
                if cfg.has_option('poll', 'lang') else [ DEFAULT_LANG ]

        watcher = GpReviewsWatcher(db, templateRenderer, googleLogin, googlePassword,
                                   androidId, pollPeriod, pollDelay, langs)
        watcher.setServiceParent(application)

        bot = Bot(db, l10n_support)
        bot.setServiceParent(application)

        telegramBot = BotService(plugins=[bot])
        telegramBot.setServiceParent(application)

        client = TelegramClient(token, telegramBot.on_update, debug=True)
        client.setServiceParent(application)

        return serviceCollection


serviceManager = ServiceManager()