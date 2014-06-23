#!/usr/bin/python2.7

import web
import json
import os
from common import invoke_shell, rpm_query, rpm_install, rpm_update, rpm_uninstall
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Uninstall'
)

def get_installed():
    # meta = get_meta_data()
    # rpm_installed = meta['software']['installed']

    # here, we get all the vmediax software, via VMediaX repo
    rpm_installed = []
    sta, out, err = invoke_shell('yum list installed | grep -E \"vmediax|installed|zeroc-ice-x86_64|zeroc-ice-i386\" | awk \'{print $1}\' | grep -v installed')
    # result like: tvwall-webcontent.x86_64
    # print out
    if sta == 0 and out:
        for item in out.split("\n"):
            rpm_installed.append(item.strip())

    return rpm_installed

class Uninstall:
    def GET(self):
        data = get_installed()
        return json.dumps(data)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        input = json.loads(web.data())
        has_installed = rpm_query(input['name'])
        if has_installed:
            if not input['name'] in get_installed():
                err = '580 ' + input['name'] + ' donnot installed'
                raise RestfulError(err)
            ret_info = rpm_uninstall(input['name'])
            ret_status = ret_info['status']
            if ret_status:
                delete_rpm_log(input['name'])
                return 'Uninstall '+ input['name'] + ' success'
            else:
                msg = '580 Uninstall failed '+ input['name'] + "\n" \
                        + 'Error Msg: ' + ret_info['error']
                raise RestfulError(msg)
        else:
            msg = '580 no such program ' + input['name']
            raise RestfulError(msg)
        return

app = web.application(urls, locals())
