#!/usr/bin/python2.7


import web,os,json,re
from common.restfulclient import RestfulClient
from common.restfulclient import RestfulError

urls = (
  "/upload", "Upload",
  "/service", "Service",
  "/startup", "Startup",
)

class Upload:
    def GET(self):
        render = web.template.frender("./view/templates/software_upload.html")
        return render()
    def POST(self):
        try:
            headers = {}
            data = web.data()
            data_array = data[0:128].split('\n');
            headers["Content-Type"] = "multipart/form-data; boundary=" + data_array[0][2:]
            res = RestfulClient.getresponse("POST", "/software/upload", data, headers)
        except Exception as e:
            return "{\"error\":\"" + e.message + "\"}"
            #raise RestfulError(e.message)
        else:
            if res == "":
                res = "{}"
            return res
        
class Service:
    def GET(self):
        render = web.template.frender("./view/templates/software_services.html")
        return render()
            
class Startup:
    def GET(self):
        render = web.template.frender("./view/templates/software_startup.html")
        return render()

app = web.application(urls, locals())
