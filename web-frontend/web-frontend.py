#!/usr/bin/python2.7

import web,os,json

#####
#view import
import view.index as view_index
import view.menu as view_menu
import view.system as view_system
import view.network as view_network
import view.software as view_software
import view.storage as view_storage
import view.login as view_login
import view.other as view_other
#####
#utils
from common.restfulclient import RestfulClient
from common.restfulclient import RestfulError

from common import deal_array_data_for_client_ui

urls = (
    "/view/templates/(.*)", "template",
    "/favicon.ico", "favicon",
    "/", "index",
    "/view/index", view_index.app,
    "/view/menu", view_menu.app,
    "/view/system", view_system.app,
    "/view/network", view_network.app,
    "/view/software", view_software.app,
    "/view/storage", view_storage.app,
    "/view/login", view_login.app,
    "/view/other", view_other.app,
    "/model/(.+)", "model_proxy",
)

def auth_processor(handler):
    method = True
    if method == True:
        return handler()
    return "{not pass}"

def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")

class model_proxy:
    def GET(self, args):
        try:
            res = RestfulClient.getresponse("GET", "/" + args + web.ctx.query)
            page_list = [
                #"system/process",
                #"network/route",
                #"system/shared-memory/detail",
                #"software/startup"
            ]
            if args in page_list:
                record_set = json.loads(res);
                record_set = deal_array_data_for_client_ui(web.ctx.query[1:], record_set);
                res = json.dumps(record_set)
            
        except Exception as e:
            raise RestfulError(e.message)
        else:
            return res
    def POST(self, args):
        try:
            res = RestfulClient.getresponse("POST", "/" + args, web.data())
        except Exception as e:
            raise RestfulError(e.message)
        else:
            return res
    def PUT(self, args):
        try:
            res = RestfulClient.getresponse("PUT", "/" + args, web.data())
        except Exception as e:
            raise RestfulError(e.message)
        else:
            return res
    def DELETE(self, args):
        try:
            res = RestfulClient.getresponse("DELETE", "/" + args, web.data())
        except Exception as e:
            raise RestfulError(e.message)
        else:
            return res

class index:
    def GET(self):
        try:
            data = web.data()
            res = RestfulClient.getresponse("GET", "/auth", data)
        except Exception as e:
            raise RestfulError(e.message)
        else:
            #if "HTTP_REFERER" in web.ctx.environ.keys() and web.ctx.environ["HTTP_REFERER"].endswith("view/login"):
            render = web.template.frender("./view/templates/index.html")
            return render()
            #else:
            #    raise web.seeother('/view/login')

class template:
    def GET(self, args):
        file_path = "./view/templates/" + args
        file_type = {
            ".html" : "text/html",
            ".htm" : "text/html",
            ".jpeg" : "image/jpeg",
            ".png" : "image/png",
            ".gif" : "image/gif",
            ".jpg" : "image/jpeg",
            ".js" : "application/x-javascript",
            ".css" : "text/css"
        }
        args_lower = args.lower();
        data = ""
        
        type = os.path.splitext(args_lower)[1];
        if type in file_type.keys():
            web.header('Content-type', file_type[type])
        else:
            return data;
        #for type in file_type.keys():
        #    if args_lower.endswith(type):
        #        web.header('Content-type', file_type[type])
        #        break
        web.header('Cache-Control', 'max-age=300')
        if os.path.exists(file_path):
            f = open(file_path)
            data = f.read()
            f.close()
        web.header('Content-Length', len(data))
        return data
        
class favicon():
    def GET(self):
        file_path = "./view/templates/images/favicon.ico"
        data = ""
        if os.path.exists(file_path):
            f = open(file_path)
            data = f.read()
            f.close()
        return data

app = web.application(urls, globals())
app.notfound = notfound
RestfulClient.restful_addr = "127.0.0.1:88"
if __name__ == "__main__":
    os.environ["PORT"] = "8089"
    app.add_processor(auth_processor)
    app.run()


