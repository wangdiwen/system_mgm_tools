#!/usr/bin/python2.7

import web,json,string,types


from common.restfulclient import RestfulError

urls = (
  "/(.+)", "MonitorSetting"
)

class MonitorSetting:
    def GET(self, args):
        import monitorsetting
        method_list = [
            "getMonitorResolutionList",
            "getMonitorXrandrResolutionList",
            "getCurrentResolution",
            "getBrightness",
            "getContrast",
            "getSaturation",
            "getCurrentMonitorsMode",
            "getMonitorCount",
            "getDisplayList",
        ]
        try:
            arg_list = args.split("/");
            if arg_list[0] in method_list:
                func = getattr(monitorsetting, arg_list[0])
                if len(arg_list) == 1:
                    ret = func();
                elif len(arg_list) == 2:
                    ret = func(string.atoi(arg_list[1], 10));
        except Exception as e:
            raise RestfulError("580 " + e.message)
        else:
            return json.dumps(ret)

    def POST(self, args):
        import monitorsetting
        method_list = [
            "setMonitorResolution",
            "addResolution",
            "setFrequency",
            "setBrightness",
            "setContrast",
            "setSaturation",
            "setMonitorMode",
        ]
        try:
            client_json_data = web.data()
            json_loaded_data = json.loads(client_json_data)

            if client_json_data != "" and type(json_loaded_data) is not types.ListType:
                raise RestfulError("580 arguments is not valid!")

            arg_list = args.split("/");
            if arg_list[0] in method_list:
                func = getattr(monitorsetting, arg_list[0])
                if len(json_loaded_data) == 0:
                    ret = func();
                elif len(json_loaded_data) == 1:
                    ret = func(json_loaded_data[0]);
                elif len(json_loaded_data) == 2:
                    ret = func(json_loaded_data[0], json_loaded_data[1]);
                elif len(json_loaded_data) == 3:
                    ret = func(json_loaded_data[0], json_loaded_data[1], json_loaded_data[2]);
                elif len(json_loaded_data) == 4:
                    ret = func(json_loaded_data[0], json_loaded_data[1], json_loaded_data[2], json_loaded_data[3]);
        except Exception as e:
            raise RestfulError("580 " + e.message)
        else:
            return json.dumps(ret)

app = web.application(urls, locals())
