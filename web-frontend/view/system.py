#!/usr/bin/python2.7


import web,os,json,re
from common.restfulclient import RestfulClient
from common.restfulclient import RestfulError
from common import exec_sub

urls = (
  "/process", "Process",
  "/shared-memory", "SharedMemory",
  "/datetime", "DateTime",
  "/run-mode", "RunMode",
  "/env", "Env",
)

class Process:
    def GET(self):
        render = web.template.frender("./view/templates/system_process.html")
        return render()
        
class SharedMemory:
    def GET(self):
        try:
            res = RestfulClient.getresponse("GET", "/system/shared-memory")
        except Exception as e:
            raise RestfulError(e.message)
        else:
            render = web.template.frender("./view/templates/system_shared_memory.html")
            return render(res)
            
class DateTime:
    def GET(self):
        try:
            res = RestfulClient.getresponse("GET", "/system/time")
        except Exception as e:
            raise RestfulError(e.message)
        else:
            render = web.template.frender("./view/templates/system_datetime.html")
            return render()
            
class RunMode:
    def GET(self):
        ret = False
        try:
            out, status = exec_sub("cat /etc/issue|head -n 1 |awk '{printf $3}'|awk -F '.' '{printf $1}'")
            if out == "5":
                out, status = exec_sub("cat /proc/mounts|grep -q '/dev/root /'")
            elif out == "6":
                out, status = exec_sub("cat /proc/mounts |grep -Eq '/dev/[a-z0-9]+ / '")
        except Exception as e:
            ret = True
        
        return json.dumps(ret)
        
class Env:
    def GET(self):
        render = web.template.frender("./view/templates/system_env.html")
        return render()
        

app = web.application(urls, locals())
