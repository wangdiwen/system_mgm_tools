import web

urls = (
  "", "SystemInfo",
)

class SystemInfo:
    def GET(self):
        render = web.template.frender("./view/templates/menu.html")
        return render()
    
app = web.application(urls, locals())
