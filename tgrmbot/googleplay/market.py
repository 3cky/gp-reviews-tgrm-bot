# -*- coding: utf-8 -*-

import treq

from twisted.internet import defer
from twisted.web import http

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
    def __init__(self, gp_api_server):
        self.gp_api_server = gp_api_server

    @defer.inlineCallbacks
    def execute(self, url, params):
        try:
            resp = yield treq.get(url, params=params)
            if resp.code == http.OK:
                response = yield resp.json()
                defer.returnValue(response)
            else:
                err_data = yield treq.content(resp)
                err_msg = str(err_data)
                raise RequestError(err_msg, resp.code)
        except RequestError as e:
            if isinstance(e, RequestError):
                raise e
            raise RequestError(e)

    @defer.inlineCallbacks
    def getReviews(self, appid, lang='en'):
        url = self.gp_api_server + "/api/apps/" + appid + "/reviews"
        response = yield self.execute(url, {"lang": lang})
        result = response['results']['data']
        defer.returnValue(result)
