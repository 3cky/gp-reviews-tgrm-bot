'''
Created on 21-Feb-2017

@author: 3cky
'''

from twisted.internet import reactor, defer

from datetime import datetime

import re

import babel.dates

GP_APP_URL = u'https://play.google.com/store/apps/details?id={app_name}&hl={lang}'

GP_REVIEW_URL = u'https://play.google.com/apps/publish/?dev_acc={dev_id}#ReviewDetailsPlace:p={app_id}&reviewid={review_id}'

GP_APP_ID_REGEX = r'id=([a-zA_Z_][.\w]*)'
GP_APP_DESC_REGEX = r'<title id="main-title">(.+) - Android Apps on Google Play</title>'

def sleep(secs):
    '''
    Create deferred for pause to given timespan (in seconds)
    '''
    d = defer.Deferred()
    reactor.callLater(secs, d.callback, None)
    return d


def format_datetime(timestamp_msec):
    '''
    Convert given Unix timestamp (in milliseconds) to localized date string
    '''
    date = datetime.fromtimestamp(timestamp_msec / 1000.0)
    return babel.dates.format_datetime(date)


def gp_app_name(app_url):
    '''
    Extract Google Play application symbolic name from its page URL
    '''
    m = re.search(GP_APP_ID_REGEX, str(app_url))
    return m.group(1) if m else None


def gp_app_desc(app_data):
    '''
    Extract Google Play application description from its page data
    '''
    m = re.search(GP_APP_DESC_REGEX, str(app_data))
    return m.group(1) if m else None


def gp_app_url(app_name, lang=''):
    '''
    Get Google Play application page URL
    '''
    return GP_APP_URL.format(app_name=app_name, lang=lang)


def gp_review_url(review_id, dev_id, app_name):
    '''
    Get Google Play developer console URL of application review
    '''
    return GP_REVIEW_URL.format(dev_id=dev_id, app_name=app_name, review_id=review_id)