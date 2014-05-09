#!/usr/bin/python2.7

import httplib,web

class RestfulClient:
    restful_addr = "127.0.0.1:88"
    def __init__(self):
        pass
    @staticmethod
    def getresponse(method, url, data = None):
        conn = httplib.HTTPConnection(RestfulClient.restful_addr)

        if data != None:
            conn.request(method, url, data)
        else:
            conn.request(method, url)

        res = conn.getresponse()
        res_data = res.read()
        conn.close()
        if res.status != 200:
            raise Exception("%d %s" % (res.status, res.reason))
        return res_data

class RestfulError(web.HTTPError):
    def __init__(self, status):
        headers = {'Content-Type': 'text/html'}
        web.HTTPError.__init__(self, status)
