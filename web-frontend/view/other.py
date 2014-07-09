#!/usr/bin/python2.7


import web,os,json,re,datetime,shutil
from common.restfulclient import RestfulClient
from common.restfulclient import RestfulError
from common import get_method_query_to_map
from common import exec_sub
from common import auth

urls = (
  "/log", "Log",
  "/backup", "Backup",
  "/license", "License",
  "/display", "Display",
  "/licensefile(.*)", "LicenseFile",
)

class Log:
    def GET(self):
        render = web.template.frender("./view/templates/other_log.html")
        return render()
class Backup:
    def GET(self):
        auth()

        if web.ctx.query == "":
            render = web.template.frender("./view/templates/other_backup.html")
            return render()
        '''
        datatype=list|file|tar
        file=""
        path=log|etc|conf
        type=sys|usr|web
        '''
        arg_map = get_method_query_to_map(web.ctx.query[1:]);
        command = ""
        res = ""

        try:
            if "path" in arg_map.keys():
                if arg_map["type"] == "usr":
                    path = "/opt/program/" + arg_map["path"]
                else:
                    path = "/opt/system/" + arg_map["path"]

            if arg_map["datatype"] == "list":
                res, status = exec_sub("find " + path + " -type f -name '*'")
                res = res.strip('\n');
                if len(res) != 0:
                    res = res.split("\n");
                else:
                    res = [];
                res = json.dumps(res)
            elif arg_map["datatype"] == "file":
                web.header('Content-type', 'text/plain')
                if arg_map["file"].startswith("/opt/system") or arg_map["file"].startswith("/opt/program/etc") or arg_map["file"].startswith("/opt/program/log"):
                    if os.path.exists(arg_map["file"]):
                        f = open(arg_map["file"])
                        res = f.read()
                        f.close()
            elif arg_map["datatype"] == "tar":
                file = arg_map["path"] + "-" + datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S') + ".tar.gz"
                if arg_map["type"] == "usr":
                    file = "usr-" + file
                file_path = "/var/" + file

                exec_sub("cd " + path + "&& tar -zcf " + file_path + " ./*")
                web.header('Content-type', 'application/x-tar')
                web.header('Content-disposition', 'attachment;filename=' + file)
                if os.path.exists(file_path):
                    f = open(file_path)
                    res = f.read()
                    f.close()
                os.remove(file_path)

        except Exception as e:
            raise RestfulError("580 " + e.message)
        else:
            return res

    def PUT(self):
        auth()
        '''
        file=""
        data=log|etc
        action=clear|clearall|tar|save|del
        type=sys|usr|web
        '''
        client_json_data = web.data()
        json_data = json.loads(client_json_data)

        try:
            if json_data["type"] == "web":
                if json_data["data"] == "log" and json_data["action"] == "clear":
                    #exec_sub("echo ''>/opt/system/log/restful-server/restful.log")
                    f = open('/opt/system/log/restful-server/restful.log', 'w')
                    f.truncate(0);
                    f.close()

            if json_data["type"] == "usr":
                if json_data["data"] == "log":
                    if json_data["action"] == "clearall":
                        res, status = exec_sub("find /opt/program/log -type f -name '*'")
                        res = res.strip('\n').split("\n");
                        for file in res:
                            f = open(file, 'w')
                            f.truncate(0);
                            f.close()
                    if json_data["action"] == "del":
                        file_path = json_data["file"]
                        if os.path.exists(file_path):
                            os.remove(file_path)
                if json_data["data"] == "etc":
                    if json_data["action"] == "save":
                        file_path = json_data["file"]
                        if os.path.exists(file_path):
                            f = open(file, 'w')
                            f.truncate(0);
                            f.write(json_data["file_text"]);
                            f.close()


        except Exception as e:
            raise RestfulError("580 " + e.message)
        else:
            return ""

class License:
    def GET(self):
        render = web.template.frender("./view/templates/other_license.html")
        return render()

    def POST(self):
        data = web.input(upload_file = {})
        try:
            if 'upload_file' in data:
                file_name = os.path.split(data.upload_file.filename)[1]
                tmp_name_list = file_name.split("\\")
                file_name = tmp_name_list[-1]
                if os.path.splitext(file_name)[1] != '.img':
                    raise Exception("the filename extension is not .img!!!");

                dir_path = "/opt/system/license"
                if not os.path.exists(dir_path):
                    os.mkdir(dir_path);

                tmp_dir_path = "/opt/system/license/.tmp"
                if os.path.exists(tmp_dir_path):
                    shutil.rmtree(tmp_dir_path)
                os.mkdir(tmp_dir_path);

                file_path = tmp_dir_path + "/" + file_name
                if os.path.exists(file_path):
                    os.remove(file_path)

                file = open(file_path, 'w')
                file.write(data.upload_file.file.read())
                file.close()

                exec_sub("cd " + tmp_dir_path + "&&bzcat " + file_name + " | openssl bf-cbc -d -k 'mmap@vmediax' | cpio -iduv");
                exec_sub("cd " + tmp_dir_path + "&&md5sum -c md5sum")

                os.remove(file_path)
                os.remove(tmp_dir_path + "/md5sum")

                list = os.listdir(tmp_dir_path)
                for line in list:
                    if os.path.splitext(line)[1] == ".lic":
                        exec_sub("cd " + tmp_dir_path + "&&bzcat " + line + " | cpio -iduv");
                        os.remove(tmp_dir_path + "/" + line)

                exec_sub("cd " + tmp_dir_path + "&&cp -ar ./* ../");
                #shutil.copytree(tmp_dir_path, dir_path)
                shutil.rmtree(tmp_dir_path)

        except Exception as e:
            shutil.rmtree(tmp_dir_path)
            return "{\"error\":\"" + e.message + "\"}"
        else:
            return "{}"
class LicenseFile:
    def GET(self, args):
        dir_path = "/opt/system/license"
        if args == "":
            list = []
            if os.path.exists(dir_path):
                list = os.listdir(dir_path)
            return json.dumps(list);
        else:
            web.header('Content-type', 'application/x-tar')
            web.header('Content-disposition', 'attachment;filename=' + args[1:])
            f = open(dir_path + args)
            res = f.read()
            f.close()
            return res;
class Display:
    def GET(self):
        render = web.template.frender("./view/templates/other_display.html")
        return render()

app = web.application(urls, locals())
