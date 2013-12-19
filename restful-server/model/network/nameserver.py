#!/usr/bin/python2.7

import web
import json
import re

from common.restfulclient import RestfulError
from common.global_helper import *  # public helper functions

urls = (
    '', 'Nameserver'
)

def get_nameserver():
    meta = get_meta_data()
    dns_list = meta['network']['nameserver']
    return dns_list

def post_nameserver(ip_addr):
    # Check the ip_addr has existed or not
    data = {}
    ip_has = False

    if not re.compile("^([1]?\d\d?|2[0-1]\d|22[0-3])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])$").match(ip_addr):
        data['status'] = 'false'
        data['message'] = 'invalid ip addr [' + ip_addr + ']'
        return data

    ip_list = get_nameserver()
    for ip in ip_list:
        if ip == ip_addr:
            ip_has = True

    if not ip_has:
        # Add a new ip_addr to meta
        meta = get_meta_data()
        meta['network']['nameserver'].append(ip_addr)
        ret = set_meta_data(meta)
        if ret:
            run_file = '/etc/resolv.conf'
            ret = create_conf_by_list(run_file, meta['network']['nameserver'], 'nameserver', ' ')
            ret = sync_run_config_file(run_file)

        data['status'] = 'true'
        data['message'] = 'set nameserver %s success' % ip_addr
    else:
        data['status'] = 'false'
        data['message'] = 'nameserver %s has existed' % ip_addr
    return data

def delete_nameserver(ip_addr):
    # Check the ip_addr has existed or not
    data = {}
    ip_has = False

    if not re.compile("^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$").match(ip_addr):
        data['status'] = 'false'
        data['message'] = 'invalid ip addr [' + ip_addr + ']'
        return data

    ip_list = get_nameserver()
    for ip in ip_list:
        if ip == ip_addr:
            ip_has = True

    if ip_has:
        # Delete this ip_addr of nameserver from meta data
        meta = get_meta_data()
        ret = remove_list_by_value(meta['network']['nameserver'], ip_addr)
        ret = set_meta_data(meta)
        if ret:
            run_file = '/etc/resolv.conf'
            ret = create_conf_by_list(run_file, meta['network']['nameserver'], 'nameserver', ' ')
            ret = sync_run_config_file(run_file)

        data['status'] = 'true'
        data['message'] = 'delete nameserver %s success' % ip_addr
    else:
        data['status'] = 'false'
        data['message'] = 'has no nameserver %s' % ip_addr
    return data

def order_nameserver(info):
    nameserver = info['nameserver']
    direct = info['direct']
    # check the nameserver ip
    if not re.compile("^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$").match(nameserver):
        msg = '560 nameserver address is invalid'
        raise RestfulError(msg)
    if not direct in ('up', 'down'):
        msg = '560 direct is wrong, use up and down'
        raise RestfulError(msg)

    # handle input
    server_list = get_nameserver()
    if not nameserver in server_list:
        msg = '560 nameserver is not existed'
        raise RestfulError(msg)

    length = len(server_list)
    cur_index = server_list.index(nameserver)
    if direct == 'up':
        insert_index = cur_index - 1;
    elif direct == 'down':
        insert_index = cur_index + 1;
    if insert_index < length and insert_index >= 0:
        old_server = server_list.pop(cur_index)
        server_list.insert(insert_index, old_server)
        # modify meta data
        meta = get_meta_data()
        meta['network']['nameserver'] = server_list
        ret = set_meta_data(meta)
        if ret:
            run_file = '/etc/resolv.conf'
            ret = create_conf_by_list(run_file, meta['network']['nameserver'], 'nameserver', ' ')
            ret = sync_run_config_file(run_file)
    else:
        msg = '560 can not move ' + direct
        raise RestfulError(msg)
    return

class Nameserver:
    def GET(self):
        data = []
        name_list = get_nameserver()
        if name_list:
            i = 0
            for name in name_list:
                tmp_dict = {}
                tmp_dict['addr'] = name
                tmp_dict['position'] = "%d" % i
                data.append(tmp_dict)
                i += 1
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        if not 'nameserver' in input.keys() or not 'direct' in input.keys():
            msg = '560 input date error, less arguments'
            raise RestfulError(msg)
        else:
            ret = order_nameserver(input)
            return json.dumps(ret)

    def POST(self):
        input = json.loads(web.data())
        if not 'nameserver' in input.keys():
            msg = '560 input date error, less arguments'
            raise RestfulError(msg)
        else:
            ip_addr = input['nameserver']
            data = post_nameserver(ip_addr)
            status = data['status']
            if status == 'true':
                del data['status']
                return
            else:
                msg = "560 %s" % data['message']
                raise RestfulError(msg)

    def DELETE(self):
        input = json.loads(web.data())
        ip_addr = input['nameserver']
        data = delete_nameserver(ip_addr)
        status = data['status']
        if status == 'true':
            del data['status']
            return
        else:
            msg = "560 %s" % data['message']
            raise RestfulError(msg)

app = web.application(urls, locals())
