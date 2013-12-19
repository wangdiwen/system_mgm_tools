#!/usr/bin/python2.7


import web,os,json,Cookie,random 
from common.restfulclient import RestfulClient,RestfulError

urls = (
  "(.*)", "Login",
)

class Login:
    def GET(self, args):
        if args == "":
            render = web.template.frender("./view/templates/login.html")
            return render()
        if args == "/login_random":
            if "LOGIN_RANDOM" in os.environ.keys():
                return json.dumps(os.environ["LOGIN_RANDOM"]);
        #if args == "/login_src_url":
        #    if "HTTP_REFERER" in web.ctx.environ.keys():
        #        return json.dumps(web.ctx.environ["HTTP_REFERER"]);
        return json.dumps("")
    def POST(self, args):
        data = web.data()
        if data == "":
            web.setcookie("user_name", "", -1, None, False, False, "/")
            web.setcookie("user_passwd", "", -1, None, False, False, "/")
            web.setcookie("login_random", "", -1, None, False, False, "/")
            raise web.seeother("/view/login", True)
            return ""
        try:
            res = RestfulClient.getresponse("POST", "/auth", data)
        except Exception as e:
            raise RestfulError(e.message)
        else:
            user_data = json.loads(data)
            web.setcookie("user_name", user_data["name"], "", None, False, False, "/")
            web.setcookie("user_passwd", user_data["passwd"], "", None, False, False, "/")
            os.environ["LOGIN_RANDOM"] = '%d' %random.randint(100000, 999999)
            web.setcookie("login_random", os.environ["LOGIN_RANDOM"], "", None, False, False, "/")
        return ""
        

app = web.application(urls, locals())
