#!/usr/bin/python2.7


import web,os,json,re
from common.restfulclient import RestfulClient
from common.restfulclient import RestfulError

urls = (
  "/mount", "Mount",
  "/raid", "Raid",
  "/disk", "Disk",
)

class Mount:
    def GET(self):
        render = web.template.frender("./view/templates/storage_mount.html")
        return render()
    def POST(self):
        pass
        
class Raid:
    def GET(self):
        render = web.template.frender("./view/templates/storage_raid.html")
        return render()
        
class Disk:
    def GET(self):
        render = web.template.frender("./view/templates/storage_disk.html")
        return render()
        

app = web.application(urls, locals())
