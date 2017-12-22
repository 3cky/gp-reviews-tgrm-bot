# -*- coding: utf-8 -*-
'''
Created on 20-Feb-2017

@author: avm
'''

import time
import random

from twisted.python import log
from twisted.application import service
from twisted.internet import reactor, defer

from tgrmbot.util import sleep

from tgrmbot.googleplay.market import MarketSession, RequestError, LoginError

REVIEW_TEMPLATE_NAME = 'review.md'

NUM_REQUEST_RETRIES = 3
REQUEST_RETRY_TIMEOUT = 5  # in seconds


class GpReviewsWatcher(service.Service):
    '''
    Google Play app reviews watcher service.

    '''
    name = 'tgrmbot_gp_watcher'

    def __init__(self, db, templateRenderer, gp_login, gp_password, android_id,
                 poll_period, poll_delay, gp_langs):
        self.db = db
        self.templateRenderer = templateRenderer
        self.gp_login = gp_login
        self.gp_password = gp_password
        self.android_id = android_id
        self.poll_period = poll_period
        self.poll_delay = poll_delay
        self.gp_langs = gp_langs
        self._d_poll = None

    def startService(self):
        self._bot = self.parent.getServiceNamed('tgrmbot_bot')
        reactor.callLater(3, self._run)  # @UndefinedVariable

    @defer.inlineCallbacks
    def _run(self):
        # poll cycle loop
        session = MarketSession(self.android_id)
        while reactor.running:  # @UndefinedVariable
            yield self._check_app_reviews(session)
            # delay before next application reviews poll cycle
            yield sleep(self.poll_period)

    @defer.inlineCallbacks
    def _check_app_reviews(self, session):
        log.msg('Checking for new application reviews...')
        apps = yield self.db.get_apps()
        random.shuffle(apps)
        for app in apps:
            app_id, app_name, app_desc = app
            try:
                # get new reviews for an application
                app_reviews = []
                for gp_lang in self.gp_langs:
                    retry_num = 1
                    while True:  # request retries loop
                        try:
                            if not session.loggedIn:
                                log.msg('Authorizing Google Play session...')
                                yield session.login(self.gp_login, self.gp_password)
                                yield sleep(0)  # switch to the main thread

                            lang_reviews = yield self._get_app_reviews(session, app_id, app_name,
                                                                       gp_lang)
                            yield sleep(0)  # switch to the main thread

                            app_reviews.extend(lang_reviews)

                            break  # request retries loop
                        except LoginError as le:
                            yield sleep(0)  # switch to the main thread
                            log.msg('Google Play authorization failed, error: %s' % le)
                            defer.returnValue(None)
                        except RequestError as re:
                            yield sleep(0)  # switch to the main thread
                            if re.err_code == 401:
                                session.loggedIn = False
                            retry_num += 1
                            if retry_num > NUM_REQUEST_RETRIES:
                                log.msg('Request retries limit exceeded, error: %s' % re)
                                defer.returnValue(None)
                        yield sleep(REQUEST_RETRY_TIMEOUT)

                    if gp_lang != self.gp_langs[-1]:
                        # delay before check next gp_lang
                        yield sleep(self.poll_delay)

                if app_reviews:
                    # sort app_reviews by creation time before notification
                    app_reviews.sort(key=lambda k: k.get('timestamp'))
                    # notify all related chats about new application reviews
                    yield self._notify_watchers(app_id, app_name, app_desc, app_reviews)
            except Exception as e:
                yield sleep(0)  # switch to main thread
                log.err(e, 'Error while checking for new reviews for an application %s' % app_name)
            if app != apps[-1]:
                # delay before check next application
                yield sleep(self.poll_delay)

        # purge old message track data from db
        try:
            yield self.db.purge_message_data()
        except Exception as e:
            log.err(e, "Can't purge old message track data from db")

    @defer.inlineCallbacks
    def _get_app_reviews(self, session, app_id, app_name, gp_lang):
        app_reviews = []
        gp_reviews = yield session.getReviews(appid=app_name, lang=gp_lang)
        yield sleep(0)  # switch to main thread
        for gp_review in gp_reviews:
            review_author_id = gp_review.get('commentId')
            review_author_name = gp_review.get('authorName')
            review_timestamp = gp_review.get('timestampMsec')
            review_rating = gp_review.get('starRating')
            review_comment = gp_review.get('comment')
            # check author is ignored
            author_ignored = yield self.check_author_ignored(review_author_id)
            if author_ignored:
                log.msg('Skipping review from ignored author: %s' % (review_author_id,))
                continue
            # check for review with same author id
            db_reviews = yield self.db.get_reviews(app_id, review_author_id)
            if not db_reviews:
                # new review found, will add to database and notify
                log.msg('Found new review for %s from author: %s' % (app_name, review_author_id,))
                yield self.db.add_review(app_id, review_author_id, review_author_name,
                                         review_timestamp, review_rating, review_comment, gp_lang)
                app_reviews.append({'author': review_author_id,
                                    'timestamp': review_timestamp,
                                    'version': gp_review.get('documentVersion'),
                                    'device': gp_review.get('deviceName'),
                                    'rating': review_rating,
                                    'title': gp_review.get('title'),
                                    'comment': review_comment,
                                    'lang': gp_lang})
            else:
                # review with given author ID already seen, check for changes
                review_id, _app_id, _author_id, _author_name, old_review_timestamp, \
                    old_review_rating, old_review_comment, _lang = db_reviews[0]
                if (review_rating != old_review_rating) or (review_comment != old_review_comment):
                    # review updated, will update database and notify
                    log.msg('Found updated review for %s from author: %s' %
                            (app_name, review_author_id,))
                    yield self.db.update_review(review_id, review_timestamp,
                                                review_rating, review_comment)
                    app_reviews.append({'author': review_author_id,
                                        'timestamp': review_timestamp,
                                        'version': gp_review.get('documentVersion'),
                                        'device': gp_review.get('deviceName'),
                                        'rating': review_rating,
                                        'title': gp_review.get('title'),
                                        'comment': review_comment,
                                        'old_timestamp': old_review_timestamp,
                                        'old_timedelta': review_timestamp-old_review_timestamp,
                                        'old_rating': old_review_rating,
                                        'old_comment': old_review_comment,
                                        'lang': gp_lang})

        defer.returnValue(app_reviews)

    @defer.inlineCallbacks
    def _notify_watchers(self, app_id, app_name, app_desc, app_reviews):
        # notify all related chats about new application reviews
        watchers = yield self.db.get_watchers(app_id)
        if watchers:
            chat_ids = [chat_id for _watcher_id, _app_id, chat_id in watchers]
            messages = [self.templateRenderer.render(REVIEW_TEMPLATE_NAME,
                                                     app={'name': app_name, 'desc': app_desc},
                                                     review=review)
                        for review in app_reviews]
            for chat_id in chat_ids:
                for i, message in enumerate(messages):
                    # send notification message to chat
                    try:
                        sent_message = yield self._bot.send_message(chat_id, message)
                    except Exception as e:
                        log.err(e, "Can't send message: %s to chat: %s" % (message, chat_id))
                        continue
                    # store notification message tracking information
                    try:
                        yield self.db.add_message_data(chat_id, app_reviews[i]['author'],
                                                       sent_message.message_id, sent_message.date)
                    except Exception as e:
                        log.err(e, "Can't store tracking info for notification message: %s" %
                                (sent_message,))

    @defer.inlineCallbacks
    def review_author(self, chat_id, message_id):
        d = yield self.db.get_message_data(chat_id, message_id)
        if not d:
            defer.returnValue(None)
        defer.returnValue(d[0][2])

    @defer.inlineCallbacks
    def check_author_ignored(self, author_id):
        d = yield self.db.get_ignored_author(author_id)
        defer.returnValue(len(d) > 0)

    @defer.inlineCallbacks
    def ignore_author(self, author_id):
        yield self.db.add_ignored_author(author_id, int(time.time()))

    @defer.inlineCallbacks
    def watch(self, chat_id, app_name, app_desc):
        app = yield self.db.get_app(app_name)
        if not app:
            # add new app
            app_id = yield self.db.add_app(app_name, app_desc)
        else:
            app_id, _app_name, _app_desc = app[0]
            # check chat is already watching for an app
            watcher = yield self.db.get_watcher(app_id, chat_id)
            if watcher:
                defer.returnValue(False)
        # add new watcher
        yield self.db.add_watcher(app_id, chat_id)
        # force next poll cycle
        self.poll()
        defer.returnValue(True)

    @defer.inlineCallbacks
    def unwatch(self, chat_id, app_name):
        app = yield self.db.get_app(app_name)
        if not app:
            defer.returnValue(None)

        app_id, app_name, app_desc = app[0]
        watcher = yield self.db.get_watcher(app_id, chat_id)
        if not watcher:
            defer.returnValue(None)

        # delete watcher first
        watcher_id, _app_id, _chat_id = watcher[0]
        yield self.db.delete_watcher(watcher_id)

        # if no more watchers are watching given app, delete it and its reviews
        app_watchers = yield self.db.get_watchers(app_id)
        if not app_watchers:
            yield self.db.delete_reviews(app_id)
            yield self.db.delete_app(app_id)

        defer.returnValue((app_name, app_desc))

    @defer.inlineCallbacks
    def watched_apps(self, chat_id):
        apps = yield self.db.get_watched_apps(chat_id)
        defer.returnValue(apps)

    def poll(self):
        if self._d_poll is not None:
            self._d_poll.cancel()
