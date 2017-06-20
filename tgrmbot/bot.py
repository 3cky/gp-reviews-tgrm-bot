# -*- coding: utf-8 -*-
'''
Created on 20-Jan-2017

@author: 3cky
'''

from twisted.web import http
from twisted.internet import defer
from twisted.application import service

from TelegramBot.plugin.bot import BotPlugin

from tgrmbot.util import sleep, gp_app_name, gp_app_desc, gp_app_url

import treq


class Bot(service.Service, BotPlugin):
    '''
    Telegram chat bot.

    '''
    name = 'tgrmbot_bot'

    def __init__(self, db, l10n_support):
        BotPlugin.__init__(self)
        self.db = db
        self.l10n_support = l10n_support

    def startService(self):
        self._gp_watcher = self.parent.getServiceNamed('tgrmbot_gp_watcher')
        self._last_message_send = 0.

    def on_unknown_command(self, cmd):
        return _(u'Unknown command: /%(cmd)s\n' +
                 u'Please use /help for list of available commands.') % {'cmd': cmd}

    def on_command_start(self, _cmd_args, _cmd_msg):
        return _(u'Hello, I\'m *Google Play app reviews watching bot*.\n' +
                 'For help, please use /help command.')

    def on_command_help(self, _cmd_args, _msg):
        return _(u'*Available commands:*\n\n' +
                 u'/watch `[app_id_or_url [app_description]]`\n' +
                 'Start watching for reviews for an application. ' +
                 u'Command without arguments shows the list of watched applications. ' +
                 u'Example:\n/watch `https://play.google.com/store/apps/details' +
                 '?id=com.android.chrome Chrome`\n\n' +
                 u'/unwatch `<app_id_or_url>`\nStop watching for reviews for an application.')

    def on_command_echo(self, cmd_args, _cmd_msg):
        return cmd_args

    @defer.inlineCallbacks
    def on_command_watch(self, cmd_args, cmd_msg):
        '''
        Format: /watch [app_id_or_url [app_desc]]

        '''
        chat_id = cmd_msg.chat.id

        if cmd_args is None or not cmd_args:
            msg = yield self._cmd_watch_list(chat_id)
            defer.returnValue(msg)

        watch_args = cmd_args.split(' ', 1)
        watch_args = [w.strip() for w in watch_args]

        if len(watch_args) == 1:
            app_str = watch_args[0]
            # will fetch app description from its gp page
            app_desc = None
        else:
            app_str, app_desc = watch_args

        app_name = self._to_app_name(app_str)

        if app_name is None or not app_name:
            defer.returnValue(_(u'Invalid app: `%(app_str)s`') % {'app_str': app_str})

        # reconstruct app gp page url from its symbolic name
        app_url = gp_app_url(app_name, 'en')

        app_data = yield self._fetch_app_data(app_url)
        if app_data is None:
            defer.returnValue(_(u'App not found: %(app_url)s') % {'app_url': app_url})

        # get app page url without explicit language identifier
        app_url = gp_app_url(app_name)

        if app_desc is None:
            # try to extract app description from app page
            app_desc = gp_app_desc(app_data)

        if app_desc is None:
            app_desc = app_name

        res = yield self._gp_watcher.watch(chat_id, app_name, app_desc)
        if not res:
            defer.returnValue(_(u'Already watching: [%(app_desc)s](%(app_url)s)') %
                              {'app_desc': app_desc, 'app_url': app_url})

        defer.returnValue(_(u'Added for watching: [%(app_desc)s](%(app_url)s)') %
                          {'app_desc': app_desc, 'app_url': app_url})

    def _to_app_name(self, app_str):
        if app_str.startswith('http'):
            # extract app symbolic name from its gp page url
            return gp_app_name(app_str)
        return app_str

    @defer.inlineCallbacks
    def _cmd_watch_list(self, chat_id):
        apps = yield self._gp_watcher.watched_apps(chat_id)
        if apps:
            msg = _(u'Watched apps:')
            for app in apps:
                _app_id, app_name, app_desc = app
                app_url = gp_app_url(app_name)
                msg += u'\n[%s](%s)' % (app_desc, app_url,)
        else:
            msg = _(u'No watched apps.')
        defer.returnValue(msg)

    @defer.inlineCallbacks
    def on_command_unwatch(self, app_str, cmd_msg):
        '''
        Format: /unwatch <app_id_or_url>

        '''
        if app_str is None or not app_str:
            defer.returnValue(_(u'Please specify app to remove from watched.'))

        app_name = self._to_app_name(app_str)
        if app_name is None or not app_name:
            defer.returnValue(_(u'Invalid app to unwatch: `%(app_str)s`') % {'app_str': app_str})

        app = yield self._gp_watcher.unwatch(cmd_msg.chat.id, app_name)
        if not app:
            defer.returnValue(_(u'App not watched: `%(app_name)s`') % {'app_name': app_name})

        _app_name, app_desc = app
        app_url = gp_app_url(app_name)
        defer.returnValue(_(u'Removed from watched: [%(app_desc)s](%(app_url)s)') %
                          {'app_desc': app_desc, 'app_url': app_url})

    @defer.inlineCallbacks
    def _fetch_app_data(self, app_url):
        resp = yield treq.get(app_url)
        yield sleep(0)  # switch to main thread
        if resp.code == http.OK:
            app_data = yield treq.content(resp)
            yield sleep(0)  # switch to main thread
            defer.returnValue(app_data)
        defer.returnValue(None)

    @defer.inlineCallbacks
    def send_messages(self, chat_id, messages):
        for message in messages:
            yield self.send_message(chat_id, message)
