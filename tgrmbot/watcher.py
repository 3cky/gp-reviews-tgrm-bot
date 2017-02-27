'''
Created on 20-Feb-2017

@author: avm
'''

from twisted.python import log
from twisted.application import service
from twisted.internet import reactor, defer

from tgrmbot.util import sleep

from tgrmbot.googleplay.market import MarketSession, RequestError

RELOGIN_TIMEOUT = 60 # 1m

REVIEW_TEMPLATE_NAME = 'review.md'

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
        reactor.callLater(3, self._run)


    @defer.inlineCallbacks
    def _run(self):
        # poll cycle loop
        session = MarketSession(self.android_id)
        while reactor.running:
            if not session.loggedIn:
                log.msg('Authorizing Google Play session...')
                try:
                    yield session.login(self.gp_login, self.gp_password)
                except Exception as e:
                    log.err(e, 'Can\'t authorize Google Play session')
                    # delay before next login try
                    yield sleep(RELOGIN_TIMEOUT)
                    continue
            yield sleep(0) # switch to main thread
            log.msg('Checking for new reviews...')
            apps = yield self.db.get_apps()
            for app in apps:
                app_id, app_name, app_desc = app
                try:
                    # get last gp_reviews for an application
                    reviews = []
                    for gp_lang in self.gp_langs:
                        gp_reviews = yield session.getReviews(appid=app_name, lang=gp_lang)
                        yield sleep(0) # switch to main thread
                        for gp_review in gp_reviews:
                            review_author_id = gp_review.get('commentId')
                            review_author_name = gp_review.get('authorName')
                            review_timestamp = gp_review.get('timestampMsec')
                            review_rating = gp_review.get('starRating')
                            review_comment = gp_review.get('comment')
                            # check for review with same author id
                            db_reviews = yield self.db.get_reviews(app_id, review_author_id)
                            if not db_reviews:
                                # new review found, will add to database and notify
                                log.msg('Found new review for %s from author: %s' % (app_name, review_author_id,))
                                yield self.db.add_review(app_id, review_author_id, review_author_name,
                                                         review_timestamp, review_rating, review_comment,
                                                         gp_lang)
                                reviews.append({'timestamp': review_timestamp,
                                                'version': gp_review.get('documentVersion'),
                                                'device': gp_review.get('deviceName'),
                                                'rating': review_rating,
                                                'title': gp_review.get('title'),
                                                'comment': review_comment,
                                                'lang': gp_lang})
                            else:
                                # review with given author ID already seen, check for changes
                                review_id, _app_id, _author_id, _author_name, _timestamp, \
                                    old_review_rating, old_review_comment, _lang = db_reviews[0]
                                if (review_rating != old_review_rating) or (review_comment != old_review_comment):
                                    # review changed, will update database and notify
                                    log.msg('Found changed review for %s from author: %s' % \
                                            (app_name, review_author_id,))
                                    yield self.db.update_review(review_id, review_rating, review_comment)
                                    reviews.append({'timestamp': review_timestamp,
                                                    'version': gp_review.get('documentVersion'),
                                                    'device': gp_review.get('deviceName'),
                                                    'rating': review_rating,
                                                    'title': gp_review.get('title'),
                                                    'comment': review_comment,
                                                    'old_rating': old_review_rating,
                                                    'old_comment': old_review_comment,
                                                    'lang': gp_lang})
                        if gp_lang != self.gp_langs[-1]:
                            # delay before check next gp_lang
                            yield sleep(self.poll_delay)
                    # notify about new gp_reviews all related chats
                    if reviews:
                        # sort gp_reviews by creation time before notification
                        reviews.sort(key = lambda k: k.get('timestamp'))
                        # notify all related chats
                        watchers = yield self.db.get_watchers(app_id)
                        if watchers:
                            chat_ids = [chat_id for _watcher_id, _app_id, chat_id in watchers]
                            messages = [self.templateRenderer.render(REVIEW_TEMPLATE_NAME,
                                                                     app={'name': app_name, 'desc': app_desc},
                                                                     review=review)
                                        for review in reviews]
                            for chat_id in chat_ids:
                                yield self._bot.send_messages(chat_id, messages)

                except RequestError as re:
                    if re.err_code == 401:
                        log.err(re, 'Access denied while checking for new gp_reviews for an application %s' % app_name)
                        session.loggedIn = False
                        yield sleep(RELOGIN_TIMEOUT)
                        break
                    log.err(re, 'Can\'t request new gp_reviews for an application %s' % app_name)
                except Exception as e:
                    log.err(e, 'Error while checking for new gp_reviews for an application %s' % app_name)
                if app != apps[-1]:
                    # delay before check next application
                    yield sleep(self.poll_delay)

            # delay before next applications poll cycle
            self._d_poll = sleep(self.poll_period)
            try:
                yield self._d_poll
            except defer.CancelledError:
                # pause canceled
                pass


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
