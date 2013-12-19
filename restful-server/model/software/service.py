#!/usr/bin/python2.7

import web
import json
import re
from common import invoke_shell
from common.restfulclient import RestfulError

urls = (
    '', 'Service',
    '/(.*)', 'ServiceExt',
)

def get_service_list():
    data = []
    cmd = 'ls /etc/init.d'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        for line in stdout.split("\n"):
            # filter these sys service
            if line in ['cpuspeed', 'dund', 'firstboot', 'functions', 'halt', 'irda', 'killall', 'krb524', 'mdmpd', 'multipathd', 'rawdevices', 'readahead_early', 'readahead_later', 'restorecond', 'rpcgssd', 'single', 'status', 'blk-availability',]:
                continue
            data.append(line)
    return data

def get_service_status(service_name):
    data = {'status': ''}

    status_cmd = ''
    ser_status = 'stopped'
    if service_name in ['restful-server', 'web-frontend']:
        status_cmd = 'ps -ef | grep ' + service_name + ' | grep -v grep'
    else:
        status_cmd = '/etc/init.d/' + service_name.strip() + ' status'
    sta, out, err = invoke_shell(status_cmd)
    if sta == 0:
        ser_status = 'running'
        if out and re.compile(".*stopped.*").match(out.replace("\n", "")):
            ser_status = 'stopped'
        elif out and service_name == 'iptables':  # special handle
            ser_status = 'stopped'
            rule = re.compile('^[0-9]+')
            for line in out.split("\n"):
                if rule.match(line):
                    ser_status = 'running'
                    break

    data['status'] = ser_status
    return data

def mod_service(info):
    name = ''
    status = ''
    if 'name' in info.keys():
        name = info['name']
    if 'status' in info.keys():
        status = info['status']
    if not name or not status:
        err = '580 input data: name and status is empty'
        raise RestfulError(err)
    if not name in get_service_list():
        err = '580 service not support ' + name
        raise RestfulError(err)
    if not re.compile("^(start|stop|restart){1}$").match(status):
        err = '580 status is wrong, use start|stop|restart'
        raise RestfulError(err)

    cmd = 'service ' + name + ' ' + status
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        return True
    else:
        return False

class Service:
    def GET(self):
        data = get_service_list()
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        ret = mod_service(input)
        if not ret:
            err = '560 system service script wrong'
            raise RestfulError(err)
        return

    def POST(self):
        pass
    def DELETE(self):
        pass

class ServiceExt:
    def GET(self, arg):
        if not arg in get_service_list():
            msg = '580 Error: not exist such service ' + arg
            raise RestfulError(msg)
        data = get_service_status(arg)
        return json.dumps(data)

    def PUT(self, arg):
        pass
    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
