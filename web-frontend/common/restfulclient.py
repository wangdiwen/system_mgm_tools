#!/usr/bin/python

import httplib,web

class RestfulClient:
    restful_addr = "127.0.0.1:88"
    def __init__(self):
        pass
    @staticmethod
    def getresponse(method, url, data = None, headers = None):
        conn = httplib.HTTPConnection(RestfulClient.restful_addr)
        cookies = web.cookies()
        if headers == None:
            headers = {}

        headers["Cookie"] = ""

        for key in cookies.keys():
            headers["Cookie"] += key + "=" + cookies[key] + ";"

        headers["Cookie"] += "ip=" + web.ctx.ip + ";"
        #print web.utils.utf8(data)
        if data != None:
            conn.request(method, url, data, headers)
        else:
            conn.request(method, url, None, headers)

        res = conn.getresponse()
        res_data = res.read()
        conn.close()
        if res.status != 200 :
            if res.status == 570:
                _url = url.split("?")[0]
                if _url == "/auth" and web.ctx.path != "/":
                    raise Exception("%d %s" % (res.status, res.reason))
                else:
                    raise web.seeother("/view/login", True)
            else:
                raise Exception("%d %s" % (res.status, res.reason))
        return res_data

class RestfulError(web.HTTPError):
    def __init__(self, status):
        #headers = {'Content-Type': 'text/json'}
        web.HTTPError.__init__(self, status)

