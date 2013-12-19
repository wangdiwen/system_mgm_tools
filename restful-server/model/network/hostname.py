#!/usr/bin/python2.7

import web
import json
import subprocess

from common.restfulclient import RestfulError
from common.global_helper import *  # public helper functions

urls = (
    '', 'Hostname'
)

def get_hostname():
    cmd = 'hostname'
    status, stdout, stderr = shell_cmd(cmd)
    if status == 0:
        return stdout.rstrip("\n")
    return ''

def put_hostname(name):
    # Modify the /etc/hosts
    data = {}

    # modify the meta data
    meta = get_meta_data()
    meta['network']['hostname'] = name
    eth0_gateway = ''
    if 'adaptors' in meta['network'] and 'eth0' in meta['network']['adaptors']:
        eth0_gateway = meta['network']['adaptors']['eth0']['GATEWAY']
        if not eth0_gateway:
            eth0_gateway = '10.1.0.1'

    ret = set_meta_data(meta)
    if ret:
        # /etc/hosts
        temp_conf = template_name('hosts')
        run_file = '/etc/hosts'
        map_dict = {'HOSTNAME': meta['network']['hostname']}
        ret = engine_render_template(temp_conf, map_dict, run_file)
        ret = sync_run_config_file(run_file)
        # /etc/sysconfig/network
        temp_conf = template_name('network')
        run_file = '/etc/sysconfig/network'
        map_dict = {'HOSTNAME': meta['network']['hostname'],
                    'GATEWAY': eth0_gateway,
                    }
        ret = engine_render_template(temp_conf, map_dict, run_file)
        ret = sync_run_config_file(run_file)

    # Call the hostname
    shell = 'hostname ' + name
    status, stdout, stderr = shell_cmd(shell)
    if status == 0:
        data['status'] = 'true'
        data['message'] = "update the hostname success"
    else:
        data['status'] = 'false'
        data['message'] = "update the hostname failed"
    return data

class Hostname():
    def GET(self):
        data = {}
        hostname = get_hostname()
        data['hostname'] = hostname
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        name = input['hostname']
        if name:
            name = name.strip().replace(" ", '')
        if not re.compile('^(\w|-)*$').match(name):
            print 'here'
            msg = '560 Error: hostname has invalid character, just use [a-z,A-z,-,_]'
            raise RestfulError(msg)

        data = put_hostname(name)
        status = data['status']
        if status == 'true':
            return
        else:
            msg = "560 %s" % data['message']
            raise RestfulError(msg)

    def POST(self):
        pass
    def DELETE(self):
        pass

app = web.application(urls, locals())
