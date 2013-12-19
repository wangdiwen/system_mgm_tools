#!/usr/bin/python2.7

import web
import os
import json
import re

from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Env'
)
###############################################################################
def get_all_env():
    data = []
    meta = get_meta_data()
    if 'env' in meta.keys():
        for key in meta['env'].keys():
            tmp_dict = {}
            tmp_dict['key'] = key
            tmp_dict['value'] = meta['env'][key]
            data.append(tmp_dict)
    return data

def set_env(info):
    key = info['key'] if 'key' in info.keys() else ''
    value = info['value'] if 'value' in info.keys() else ''

    if not key or not value:
        raise RestfulError('580 Error: Less env key or value')
        return False

    key = key.strip()
    value = value.strip()

    meta = get_meta_data()
    if not 'env' in meta.keys():
        raise RestfulError('580 Error: meta data has no <env> dict')
        return False
    # print meta.keys()
    meta['env'][key] = value
    ret = set_meta_data(meta)
    if not ret:
        raise RestfulError('580 Error: Save meta data failed !')
        return False

    # create new '/etc/profile' conf file
    temp_conf = template_name('profile')
    if not os.path.isfile(temp_conf):
        raise RestfulError('580 Error: No template conf file <profile>')
        return False

    file = open(temp_conf, 'r')
    lines = file.readlines()
    file.close()

    context = ''
    if lines:
        for line in lines:
            context += line

    context += "\n# Here, define env variables\n"
    run_file = '/etc/profile'
    # print context
    ret = create_conf_by_dict_append_context(run_file, meta['env'], '=', context, 'export ')
    ret = sync_run_config_file(run_file)

    # enable this env
    shell = 'source /etc/profile'
    status, stdout, stderr = invoke_shell(shell, False)

    return True

def del_env(info):
    key = info['key'] if 'key' in info.keys() else ''

    if not key:
        raise RestfulError('580 Error: Less env key')
        return False

    meta = get_meta_data()
    if not key in meta['env'].keys():
        raise RestfulError('580 Error: No such key <'+key+'>')
        return False

    if key in meta['env'].keys():
        del meta['env'][key]
        ret = set_meta_data(meta)
        if not ret:
            raise RestfulError('580 Error: Save meta data failed !')
            return False

    # create new '/etc/profile' conf file
    temp_conf = template_name('profile')
    if not os.path.isfile(temp_conf):
        raise RestfulError('580 Error: No template conf file <profile>')
        return False

    file = open(temp_conf, 'r')
    lines = file.readlines()
    file.close()

    context = ''
    if lines:
        for line in lines:
            context += line

    context += "\n# Here, define env variables"
    run_file = '/etc/profile'
    ret = create_conf_by_dict_append_context(run_file, meta['env'], '=', context)
    ret = sync_run_config_file(run_file)

    # enable this env
    shell = 'source /etc/profile'
    status, stdout, stderr = invoke_shell(shell, False)

    return True

###############################################################################
class Env:
    def GET(self):
        data = get_all_env()
        return json.dumps(data, indent=4)

    def PUT(self):
        pass
    def POST(self):
        input = json.loads(web.data())
        ret = set_env(input)
        if not ret:
            raise RestfulError('580 Error: Set env failed')
        return

    def DELETE(self):
        input = json.loads(web.data())
        ret = del_env(input)
        if not ret:
            raise RestfulError('580 Error: Delete env failed')
        return

app = web.application(urls, locals())
