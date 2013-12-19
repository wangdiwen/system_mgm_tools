#!/usr/bin/python2.7

import web
import json
import os, re
import subprocess

from common import get_key_value, update_conf_file
from common.restfulclient import RestfulError

urls = (
    '', 'StartupMode'
)

def get_cur_mode():
    cur_mode = ''
    config = StartupMode.grub_conf
    if os.path.isfile(config):
        dict_data = get_key_value(config, "^default", '=')
        if dict_data:
            key = dict_data['key']
            value = dict_data['value']
            if value == '0':
                cur_mode = 'release'
            elif value == '1':
                cur_mode = 'develop'

    return cur_mode

def modify_cur_mode(info):
    mode = info['startup-mode'] if 'startup-mode' in info.keys() else ''
    if not mode:
        msg = '580 input data wrong, no startup-mode item'
        raise RestfulError(msg)
        return False
    if not re.compile("^(release|develop)$").match(mode):
        msg = '580 startup-mode item is wrong, just use [develop | release]'
        raise RestfulError(msg)

    mode_val = '0'
    if mode == 'release':
        mode_val = '0'
    elif mode == 'develop':
        mode_val = '1'

    cur_mode = get_cur_mode()
    if mode == cur_mode:
        return True
    config = StartupMode.grub_conf
    if os.path.isfile(config):
        update_conf_file(config, 'default', mode_val, '=')
    return True

class StartupMode():
    grub_conf = '/boot/grub/grub.conf'

    def GET(self):
        data = {}
        cur_mode = get_cur_mode()
        data['startup-mode'] = cur_mode
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        ret = modify_cur_mode(input)
        if not ret:
            msg = "560 set startup mode failed"
            raise RestfulError(msg)
        return

    def POST(self):
        pass
    def DELETE(self):
        pass

app = web.application(urls, locals())
