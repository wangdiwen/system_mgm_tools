#!/usr/bin/python2.7


import web,os,json
from common.restfulclient import RestfulClient,RestfulError

urls = (
  "", "Index",
)

class Index:
    def GET(self):
        try:
            res = RestfulClient.getresponse("GET", "/system/info")
        except Exception as e:
            raise RestfulError(e.message)
        else:
            render = web.template.frender("./view/templates/system_info_index.html")
            return render()

app = web.application(urls, locals())
