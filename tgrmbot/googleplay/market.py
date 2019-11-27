# Based on:
# https://github.com/liato/android-market-api-py
# https://github.com/Akdeniz/google-play-crawler

import treq

import locale

from twisted.internet import defer
from twisted.web import http

from gpapi.googleplay import GooglePlayAPI, googleplay_pb2


class RequestError(Exception):
    def __init__(self, value, err_code=-1):
        self.value = value
        self.err_code = err_code

    def __str__(self):
        s = repr(self.value)
        if self.err_code > 0:
            s = "HTTP Error: " + str(self.err_code) + "\n" + s
        return s


class MarketSession(object):
    HOST_API_REQUEST = "https://android.clients.google.com/fdfe/"
    URL_REVIEWS = HOST_API_REQUEST + "rev"

    def __init__(self, gp_login, gp_password, android_id=None, auth_sub_token=None):
        self.logged_in = False
        self.gp_login = gp_login
        self.gp_password = gp_password
        self.android_id = android_id
        self.auth_sub_token = auth_sub_token
        self.server = GooglePlayAPI(locale.getdefaultlocale()[0], None)

    def login(self):
        if self.android_id and self.auth_sub_token:
            self.server.login(None, None, int(self.android_id), self.auth_sub_token)
        else:
            self.server.login(self.gp_login, self.gp_password)
        self.android_id = str(self.server.gsfId)
        self.auth_sub_token = self.server.authSubToken
        self.logged_in = True

    @defer.inlineCallbacks
    def execute(self, url, params, lang):
        try:
            headers = self.server.getHeaders()
            headers["Accept-Language"] = lang.encode("ascii")
            resp = yield treq.get(url, params=params, headers=headers)
            if resp.code == http.OK:
                data = yield treq.content(resp)
                response = googleplay_pb2.ResponseWrapper.FromString(data)  # @UndefinedVariable
                defer.returnValue(response)
            else:
                data = yield treq.content(resp)
                raise RequestError(str(data), resp.code)
        except Exception as e:
            if isinstance(e, RequestError):
                raise e
            raise RequestError(e)

    @defer.inlineCallbacks
    def getReviews(self, appid, startIndex=0, entriesCount=10, lang='en'):
        response = yield self.execute(self.URL_REVIEWS, {"doc": appid, "o": startIndex,
                                                         "n": entriesCount, "sort": 0}, lang)
        result = []
        rp = response.payload
        if rp.HasField("reviewResponse"):
            for review in rp.reviewResponse.getResponse.review:
                result.append(self._toDict(review))
        defer.returnValue(result)

    def _toDict(self, protoObj):
        msg = dict()
        for fielddesc, value in protoObj.ListFields():
            msg[fielddesc.name] = value
        return msg