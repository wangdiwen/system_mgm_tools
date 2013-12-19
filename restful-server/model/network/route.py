#!/usr/bin/python2.7

import web
import json
import subprocess
import re

from common.restfulclient import RestfulError
from common.global_helper import *  # public helper functions

urls = (
    '', 'Route'
)

def get_route_list(content, exp_rule):
    list = []
    rule = re.compile(exp_rule)
    lines = content.split("\n")
    for line in lines:
        if rule.match(line):
            data = {}
            line_list = line.rstrip("\n").split()
            data['destination'] = line_list[0]
            data['gateway'] = line_list[1]
            data['genmask'] = line_list[2]
            data['flags'] = line_list[3]
            data['metric'] = line_list[4]
            data['ref'] = line_list[5]
            data['use'] = line_list[6]
            data['iface'] = line_list[7]
            list.append(data)
    return list

def get_all_route():
    cmd = 'route -N'
    status, stdout, stderr = shell_cmd(cmd)
    list = []
    if status == 0:
        list = get_route_list(stdout, '^[0-9]')
    return list

def exec_route(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    status = process.returncode
    stdout, stderr = process.communicate()
    return status

def add_route(route_info):
    type = route_info['type']
    target = ''
    if 'target' in route_info.keys():
        target = route_info['target']
    netmask = ''
    if 'netmask' in route_info.keys():
        netmask = route_info['netmask']
    gw = ''
    if 'gateway' in route_info.keys():
        gw = route_info['gateway']
    dev = ''
    if 'dev' in route_info.keys():
        dev = route_info['dev']

    data = {}

    if type == 'host':
        # Here, modify the 'gateway' and 'dev' item,
        cmd = ""
        str = ""
        if gw:
            if dev:
                cmd = "route add -host %s gw %s dev %s" % (target, gw, dev)
                str = "any -host %s gw %s dev %s" % (target, gw, dev)
            else:
                cmd = "route add -host %s gw %s" % (target, gw)
                str = "any -host %s gw %s" % (target, gw)
        elif dev:
            cmd = "route add -host %s dev %s" % (target, dev)
            str = "any -host %s dev %s" % (target, dev)
        else:
            data['status'] = 'false'
            data['message'] = 'gateway or device item error'
            return data

        status = exec_route(cmd)
        if status == 0:
            meta = get_meta_data()
            meta['network']['route'].append(str)
            ret = set_meta_data(meta)
            if ret:
                run_file = '/etc/sysconfig/static-routes'
                route_list = meta['network']['route']
                ret = create_conf_by_list(run_file, route_list, '', '')
                ret = sync_run_config_file(run_file)

            data['status'] = 'true'
            data['message'] = 'add host route success'
            return data
        else:
            data['status'] = 'false'
            data['message'] = 'add host route failed'
            return data
    elif type == 'net':
        # Here, modify the 'gateway' and 'dev' item,
        cmd = ""
        str = ""
        if gw:
            if dev:
                cmd = "route add -net %s netmask %s gw %s dev %s" % (target, netmask, gw, dev)
                str = "any -net %s netmask %s gw %s dev %s" % (target, netmask, gw, dev)
            else:
                cmd = "route add -net %s netmask %s gw %s" % (target, netmask, gw)
                str = "any -net %s netmask %s gw %s" % (target, netmask, gw)
        elif dev:
            cmd = "route add -net %s netmask %s dev %s" % (target, netmask, dev)
            str = "any -net %s netmask %s dev %s" % (target, netmask, dev)
        else:
            data['status'] = 'false'
            data['message'] = 'gateway or device item error'
            return data

        status = exec_route(cmd)
        if status == 0:
            meta = get_meta_data()
            meta['network']['route'].append(str)
            ret = set_meta_data(meta)
            if ret:
                run_file = '/etc/sysconfig/static-routes'
                route_list = meta['network']['route']
                ret = create_conf_by_list(run_file, route_list, '', '')
                ret = sync_run_config_file(run_file)

            data['status'] = 'true'
            data['message'] = 'add net route success'
            return data
        else:
            data['status'] = 'false'
            data['message'] = 'add net route failed'
            return data
    elif type == 'default':
        # Here, modify the 'gateway' and 'dev' item,
        cmd = ""
        str = ""
        if gw:
            if dev:
                cmd = "route add default netmask %s gw %s dev %s" % (netmask, gw, dev)
                str = "any default netmask %s gw %s dev %s" % (netmask, gw, dev)
            else:
                cmd = "route add default netmask %s gw %s" % (netmask, gw)
                str = "any default netmask %s gw %s" % (netmask, gw)
        elif dev:
            cmd = "route add default netmask %s dev %s" % (netmask, dev)
            str = "any default netmask %s dev %s" % (netmask, dev)
        else:
            data['status'] = 'false'
            data['message'] = 'gateway or device item error'
            return data

        status = exec_route(cmd)
        if status == 0:
            meta = get_meta_data()
            meta['network']['route'].append(str)
            ret = set_meta_data(meta)
            if ret:
                run_file = '/etc/sysconfig/static-routes'
                route_list = meta['network']['route']
                ret = create_conf_by_list(run_file, route_list, '', '')
                ret = sync_run_config_file(run_file)

            data['status'] = 'true'
            data['message'] = 'add default route success'
            return data
        else:
            data['status'] = 'false'
            data['message'] = 'add default route failed'
            return data
    else:
        data['status'] = 'false'
        data['message'] = 'Invalid type %s' % type
        return data

def del_route(route_info):
    type = route_info['type']
    target = ''
    if 'target' in route_info.keys():
        target = route_info['target']
    netmask = route_info['netmask']
    gw = ''
    if 'gateway' in route_info.keys():
        gw = route_info['gateway']
    dev = ''
    if 'dev' in route_info.keys():
        dev = route_info['dev']

    # Note: here, we handle 'default' route a bug
    if target == '0.0.0.0' and netmask == target:
        type = 'default'

    data = {}

    if type == 'host':
        # Here, modify the 'gateway' and 'dev' item,
        cmd = ""
        exp_list = []
        if gw:
            if dev:
                cmd = "route del -host %s gw %s dev %s" % (target, gw, dev)
                str = "any -host %s gw %s dev %s" % (target, gw, dev)
                str_extra = "any -host %s gw %s" % (target, gw)
                exp_list.append(str)
                exp_list.append(str_extra)  # revise special
            else:
                cmd = "route del -host %s gw %s" % (target, gw)
                str = "any -host %s gw %s" % (target, gw)
                exp_list.append(str)
            if gw == '0.0.0.0':
                str = "any -host %s" % target
                exp_list.append(str)
                if dev:
                    str = "any -host %s dev %s" % (target, dev)
                    exp_list.append(str)
                else:
                    str = "any -host %s dev eth0" % target
                    exp_list.append(str)
        elif dev:
            cmd = "route del -host %s dev %s" % (target, dev)
            str = "any -host %s dev %s" % (target, dev)
            exp_list.append(str)
        else:
            data['status'] = 'false'
            data['message'] = 'gateway or device item error'
            return data

        status = exec_route(cmd)
        if status == 0:
            meta = get_meta_data()
            ret = remove_list_by_list(meta['network']['route'], exp_list)
            ret = set_meta_data(meta)
            if ret:
                run_file = '/etc/sysconfig/static-routes'
                route_list = meta['network']['route']
                ret = create_conf_by_list(run_file, route_list, '', '')
                if ret:
                    ret = sync_run_config_file(run_file)

            data['status'] = 'true'
            data['message'] = 'delete host route success'
            return data
        else:
            data['status'] = 'false'
            data['message'] = 'delete host route failed'
            return data
    elif type == 'net':
        # Here, modify the 'gateway' and 'dev' item,
        cmd = ""
        exp_list = []
        if gw:
            if dev:
                cmd = "route del -net %s netmask %s gw %s dev %s" % (target, netmask, gw, dev)
                str = "any -net %s netmask %s gw %s dev %s" % (target, netmask, gw, dev)
                exp_list.append(str)
            else:
                cmd = "route del -net %s netmask %s gw %s" % (target, netmask, gw)
                str = "any -net %s netmask %s gw %s" % (target, netmask, gw)
                exp_list.append(str)
            if gw == '0.0.0.0':
                str = "any -net %s" % target
                exp_list.append(str)
                if netmask:
                    str = "any -net %s netmask %s" % (target, netmask)
                    exp_list.append(str)
                if dev:
                    str = "any -net %s netmask %s dev %s" % (target, netmask, dev)
                    exp_list.append(str)
                else:
                    str = "any -net %s netmask %s dev eth0" % (target, netmask)
                    exp_list.append(str)
        elif dev:
            cmd = "route del -net %s netmask %s dev %s" % (target, netmask, dev)
            str = "any -net %s netmask %s dev %s" % (target, netmask, dev)
            exp_list.append(str)
        else:
            data['status'] = 'false'
            data['message'] = 'gateway or device item error'
            return data

        status = exec_route(cmd)
        if status == 0:
            meta = get_meta_data()
            ret = remove_list_by_list(meta['network']['route'], exp_list)
            ret = set_meta_data(meta)
            if ret:
                run_file = '/etc/sysconfig/static-routes'
                route_list = meta['network']['route']
                ret = create_conf_by_list(run_file, route_list, '', '')
                if ret:
                    ret = sync_run_config_file(run_file)

            data['status'] = 'true'
            data['message'] = 'delete net route success'
            return data
        else:
            data['status'] = 'false'
            data['message'] = 'delete net route failed'
            return data
    elif type == 'default':
         # Here, modify the 'gateway' and 'dev' item,
        cmd = ""
        exp_list = []
        if gw:
            if dev:
                cmd = "route del default netmask %s gw %s dev %s" % (netmask, gw, dev)
                str = "any default netmask %s gw %s dev %s" % (netmask, gw, dev)
                exp_list.append(str)
            else:
                cmd = "route del default netmask %s gw %s" % (netmask, gw)
                str = "any default netmask %s gw %s" % (netmask, gw)
                exp_list.append(str)
            if gw == '0.0.0.0':
                str = "any default netmask %s" % netmask
                exp_list.append(str)
                if dev:
                    str = "any default netmask %s dev %s" % (netmask, dev)
                    exp_list.append(str)
            else:
                str = "any default netmask %s gw %s" % (netmask, gw)
                exp_list.append(str)
        elif dev:
            cmd = "route del default netmask %s dev %s" % (netmask, dev)
            str = "any default netmask %s dev %s" % (netmask, dev)
            exp_list.append(str)
        else:
            data['status'] = 'false'
            data['message'] = 'gateway or device item error'
            return data
        # print cmd
        # print str
        # print exp_list
        status = exec_route(cmd)
        if status == 0:
            meta = get_meta_data()
            ret = remove_list_by_list(meta['network']['route'], exp_list)
            ret = set_meta_data(meta)
            if ret:
                run_file = '/etc/sysconfig/static-routes'
                route_list = meta['network']['route']
                ret = create_conf_by_list(run_file, route_list, '', '')
                if ret:
                    ret = sync_run_config_file(run_file)

            data['status'] = 'true'
            data['message'] = 'delete default route success'
            return data
        else:
            data['status'] = 'false'
            data['message'] = 'delete default route failed'
            return data
    else:
        data['status'] = 'false'
        data['message'] = 'Invalid type %s' % type
        return data

class Route:
    def GET(self):
        list = get_all_route()
        return json.dumps(list)
    def PUT(self):
        pass
    def POST(self):
        input = json.loads(web.data())
        data = add_route(input)
        status = data['status']
        if status == 'true':
            return
        else:
            msg = "560 %s" % data['message']
            raise RestfulError(msg)
    def DELETE(self):
        input = json.loads(web.data())
        data = del_route(input)
        status = data['status']
        if status == 'true':
            return
        else:
            msg = "560 %s" % data['message']
            raise RestfulError(msg)

app = web.application(urls, locals())
