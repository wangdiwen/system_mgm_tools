#!/usr/bin/python2.7

import web
import json
import re, os, string, types
from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Ntp'
)

def get_ntp():
    data = {}
    data['status'] = ''
    data['ntp'] = []

    meta = get_meta_data()
    data['status'] = meta['system']['ntp-server']['status']
    data['ntp'] = meta['system']['ntp-server']['ntp']
    ret = set_meta_data(meta)
    return data

def set_ntp(info):
    ntp_status = info['status'] if 'status' in info.keys() else ''
    ntp_server = info['ntp'] if 'ntp' in info.keys() else ''

    if not ntp_status and not ntp_server:
        msg = '560 input data wrong, must given status or ntp server field'
        raise RestfulError(msg)

    if ntp_status:
        if not re.compile("^(on|off)$").match(ntp_status):
            msg = '560 ntp status wrong, use on or off'
            raise RestfulError(msg)

    ntp_info = get_ntp()
    # config ntp status
    if ntp_status:
        cur_status = ntp_info['status']
        if ntp_status != cur_status:
            meta = get_meta_data()
            meta['system']['ntp-server']['status'] = ntp_status
            ret = set_meta_data(meta)
            if ret:
                return True

    if ntp_server:
        if not ntp_server in ntp_info['ntp']:
            msg = '580 Error: '+ntp_server+ ' not in system ntp server list'
            raise RestfulError(msg)

        cmd = 'ntpdate ' + ntp_server
        status, stdout, stderr = invoke_shell(cmd)
        # print stdout
        if status == 0:
            return True
    return False

def add_ntp(info):
    addr_list = info
    if not addr_list:
        msg = '560 input data has no ntp server address'
        raise RestfulError(msg)

    ntp_info = get_ntp()
    ntp_list = ntp_info['ntp']
    invalid_ntp = []
    for addr in addr_list:
        if addr in ntp_list:
            invalid_ntp.append(addr)

    if invalid_ntp:
        msg = '560 ' + string.join(invalid_ntp, ',') + ' these ntp address has existed'
        raise RestfulError(msg)

    addr_list = list(set(addr_list))    # del the repeat item
    meta = get_meta_data()
    for addr in addr_list:
        meta['system']['ntp-server']['ntp'].append(addr)
    ret = set_meta_data(meta)
    return True

def del_ntp(info):
    addr_list = info
    if not type(addr_list) is types.ListType:
        msg = '580 input data type is wrong, use json list type'
        raise RestfulError(msg)

    ntp_info = get_ntp()
    ntp_list = ntp_info['ntp']
    invalid_ntp = []
    for addr in addr_list:
        if not addr in ntp_list:
            invalid_ntp.append(addr)

    if invalid_ntp:
        msg = '560 ' + string.join(invalid_ntp, ',') + ' has not existed'
        raise RestfulError(msg)

    # del the given ntp server addr
    meta = get_meta_data()
    ret = remove_list_by_list(meta['system']['ntp-server']['ntp'], addr_list)
    ret = set_meta_data(meta)
    return ret

class Ntp:
    def GET(self):
        data = get_ntp()
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        ret = set_ntp(input)
        if not ret:
            msg = '580 Error: Sync NTP Failed, Cannot connect to NTP Server, Pls check network'
            raise RestfulError(msg)
        return

    def POST(self):
        input = json.loads(web.data())
        ret = add_ntp(input)
        if not ret:
            msg = '580 Error: Add ntp server failed'
            raise RestfulError(msg)
        return

    def DELETE(self):
        input = json.loads(web.data())
        ret = del_ntp(input)
        if not ret:
            msg = '580 Error: Delete ntp server failed'
            raise RestfulError(msg)
        return

app = web.application(urls, locals())
