#!/usr/bin/python2.7

import web
import json
import os, re
import subprocess

from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import engine_text_parse

urls = (
    '/(.*)', 'Manager'
)

def sys_shutdown():
    cmd = 'shutdown -h now'
    status, stdout, stderr = invoke_shell(cmd, False)
    if status != None:
        return False
    return True

def sys_reboot():
    cmd = 'reboot'
    status, stdout, stderr = invoke_shell(cmd, False)
    if status != None:
        return False
    return True

def get_product():
    conf = '/etc/version'
    filter_exp = ['^product']
    seprator = '='
    return_type = 'dict'

    info = engine_text_parse(conf, filter_exp, seprator, return_type)
    if info and 'product' in info.keys():
        return info['product']
    return ''

class Manager:
    def GET(self, arg):
        if arg == 'product':
            return get_product()

    def PUT(self, arg):
        if not arg in ['shutdown', 'reboot']:
            msg = '560 argument wrong, just [shutdown and reboot] can be use'
            raise RestfulError(msg)

        if arg == 'shutdown':
            ret = sys_shutdown()
        elif arg == 'reboot':
            ret = sys_reboot()
        return

    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
