# -*- coding: utf-8 -*-
'''
Created on 20-Jan-2017

@author: 3cky
'''

from twisted.python import log
from twisted.web import http
from twisted.internet import defer
from twisted.application import service

from TelegramBotAPI.types import sendMessage

from TelegramBot.plugin.message import MessagePlugin

from tgrmbot.util import sleep, gp_app_name, gp_app_desc, gp_app_url

import treq
import time

MESSAGE_SEND_DELAY = 1.0 # message send delay in seconds

class Bot(service.Service, MessagePlugin):
    '''
    Telegram chat bot.

    '''
    name = 'tgrmbot_bot'

    def __init__(self, db, l10n_support):
        self.db = db
        self.l10n_support = l10n_support


    def startService(self):
        self._gp_watcher = self.parent.getServiceNamed('tgrmbot_gp_watcher')
        self._last_message_send = 0.


    @defer.inlineCallbacks
    def on_update(self, update):
        msg = getattr(update, 'message', None)
        if msg is None:
            msg = getattr(update, 'channel_post', None)

        log.msg("on_update: msg: %s" % msg)
        if msg is not None and hasattr(msg, 'text'):
            cmd_args = msg.text.split(maxsplit=1)
            if len(cmd_args) == 2:
                cmd, args = cmd_args
                args = args.strip()
            else:
                cmd = cmd_args[0]
                args = None

            resp = yield self._handle_cmd(msg.chat.id, cmd, args)

            if resp is not None:
                yield self.send_message(msg.chat.id, resp)

        defer.returnValue(True)


    @defer.inlineCallbacks
    def _handle_cmd(self, chat_id, cmd, args):
        try:
            if cmd == '/watch':
                resp = yield self._cmd_watch(chat_id, args)
            if cmd == '/unwatch':
                resp = yield self._cmd_unwatch(chat_id, args)
            elif cmd == '/echo':
                resp = self._cmd_echo(chat_id, args)
        except Exception as e:
            log.err(e, 'Error while handling command \'%s %s\':' % (cmd, args,))
            resp = 'ERROR: [%s] (see log file for details)' % str(e)
        defer.returnValue(resp)


    def _cmd_echo(self, chat_id, cmd_args):
        return cmd_args


    @defer.inlineCallbacks
    def _cmd_watch(self, chat_id, cmd_args):
        '''
        Format: /watch [app_id_or_url [app_desc]]

        '''
        if cmd_args is None or not cmd_args:
            msg = yield self._cmd_watch_list(chat_id)
            defer.returnValue(msg)

        watch_args = cmd_args.split(maxsplit=1)
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
                msg += '\n[%(app_desc)s](%(app_url)s)' % {'app_desc': app_desc, 'app_url': app_url}
        else:
            msg = _(u'No watched apps.')
        defer.returnValue(msg)


    @defer.inlineCallbacks
    def _cmd_unwatch(self, chat_id, app_str):
        '''
        Format: /unwatch <app_id_or_url>

        '''
        if app_str is None or not app_str:
            defer.returnValue(_(u'Please specify app to remove from watched.'))

        app_name = self._to_app_name(app_str)
        if app_name is None or not app_name:
            defer.returnValue(_(u'Invalid app to unwatch: `%(app_str)s`') % {'app_str': app_str})

        app = yield self._gp_watcher.unwatch(chat_id, app_name)
        if not app:
            defer.returnValue(_(u'App not watched: `%(app_name)s`') % {'app_name': app_name})

        _app_name, app_desc = app
        app_url = gp_app_url(app_name)
        defer.returnValue(_(u'Removed from watched: [%(app_desc)s](%(app_url)s)') %
                                {'app_desc': app_desc, 'app_url': app_url})


    @defer.inlineCallbacks
    def _fetch_app_data(self, app_url):
        resp = yield treq.get(app_url)
        yield sleep(0) # switch to main thread
        if resp.code == http.OK:
            app_data = yield treq.content(resp)
            yield sleep(0) # switch to main thread
            defer.returnValue(app_data)
        defer.returnValue(None)


    @defer.inlineCallbacks
    def send_message(self, chat_id, message):
        # throttle message send, if needed
        last_message_send_elapsed = time.time() - self._last_message_send
        if last_message_send_elapsed < MESSAGE_SEND_DELAY:
            yield sleep(MESSAGE_SEND_DELAY-last_message_send_elapsed)
        self._last_message_send = time.time()

        # do message send with markdown enabled
        m = sendMessage()
        m.chat_id = chat_id
        m.text = message
        m.parse_mode = 'Markdown'
        m.disable_web_page_preview = True
        yield self.send_method(m)

    @defer.inlineCallbacks
    def send_messages(self, chat_id, messages):
        for message in messages:
            yield self.send_message(chat_id, message)
