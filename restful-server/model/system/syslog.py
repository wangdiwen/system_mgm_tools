#!/usr/bin/python2.7

import web
import datetime,time,json, os
from common import invoke_shell
from common.restfulclient import RestfulError
from common.deamon_task import LogRatio

from common.global_helper import *  # public helper functions

urls = (
    '', 'Syslog'
)

def get_log():
    data = []
    log_file = '/opt/system/log/restful-server/restful.log'

    if os.path.isfile(log_file):
        cmd = 'tail -n 500 ' + log_file
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            for line in stdout.split("\n"):
                if line:
                    data.append(line)
            data.reverse()
    return data

def set_clear_ratio(info):  # Ratio: 1-99
    ratio = info['ratio'] if 'ratio' in info.keys() else 0
    if type(ratio) != int:
        msg = '580 Error: ratio is not digit'
        raise RestfulError(msg)
    if ratio < 1 or ratio > 99:
        msg = '580 Error: ratio must be in [1-99]'
        raise RestfulError(msg)

    LogRatio.log_ratio = ratio
    # record to meta data
    meta = get_meta_data()
    meta['restful']['log-disk-ratio'] = ratio
    ret = set_meta_data(meta)
    return True

class Syslog:
    def GET(self):
        data = get_log()
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        ret = set_clear_ratio(input)
        return

    def POST(self):
        pass
    def DELETE(self):
        pass

app = web.application(urls, locals())
