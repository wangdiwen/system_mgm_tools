#!/usr/bin/python2.7

import web
import datetime,time,json

from common import invoke_shell
from common.restfulclient import RestfulError

urls = (
  "", "SystemTime",
)

def get_time_info():
    time_struct = time.localtime(time.time())
    time_list = ["tm_year", "tm_mon", "tm_mday", "tm_wday", "tm_yday", "tm_hour", "tm_min", "tm_sec"]
    time_map = {}

    for item in time_list:
        if hasattr(time_struct, item):
            time_map[item[3:]] = getattr(time_struct, item)
    time_map["zone"] = time.strftime("%Z", time_struct)
    return time_map

class SystemTime:
    def GET(self):
        time_map = get_time_info()
        return json.dumps(time_map)

    def PUT(self):
        input_data = json.loads(web.data())
        field = input_data.keys()
        if 'ntp' in field:
            shell = 'ntpdate ' + input_data['ntp']
            status, stdout, stderr = invoke_shell(shell)
        else:
            time_map = get_time_info()
            for item in input_data:
                time_map[item] = int(input_data[item])
            time_stamp = "%d-%d-%d %d:%d:%d" % (time_map['year'], time_map['mon'], \
                                time_map['mday'], time_map['hour'], time_map['min'], time_map['sec'])
            shell = 'date -s \"' + time_stamp + '\" && hwclock --systohc --utc'
            stat, out, err = invoke_shell(shell, False)
            if stat != None:
                raise RestfulError('580 Error: modify system time something wrong')
            return ''

app = web.application(urls, locals())
