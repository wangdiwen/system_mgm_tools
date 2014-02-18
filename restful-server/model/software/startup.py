#!/usr/bin/python2.7

import web
import json
import re, os
from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Startup',
    '/(.*)', 'StartupExt'
)

###############################################################################
def startup_all():
    data = []
    meta = get_meta_data()
    item_list = meta['software']['startup']
    for item in item_list:
        tmp_list = item.split('|')
        if len(tmp_list) >= 2:
            tmp_dict = {}
            tmp_dict['name'] = tmp_list[0]
            tmp_dict['startup'] = tmp_list[1]
            data.append(tmp_dict)
    return data

def startup_app_list():
    data = []
    all_data = startup_all()
    for tmp_dict in all_data:
        data.append(tmp_dict['name'])
    return data

def startup_order(info):
    name = info['name'] if 'name' in info.keys() else ''
    position = info['position'] if 'position' in info.keys() else ''
    if not name or position == '':
        msg = '560 input data, less arguments'
        raise RestfulError(msg)

    name_list = startup_app_list()
    if not name in name_list:
        msg = '560 the software is invalid [' + name + ']'
        raise RestfulError(msg)
    if not re.compile("^[0-9]+$").match(position):
        msg = '560 the position is invalid'
        raise RestfulError(msg)

    # process the new position
    meta = get_meta_data()

    cur_startup_obj = meta['software']['startup']
    length = len(cur_startup_obj)
    index = 0
    for obj in cur_startup_obj:
        if re.compile("^"+name).match(obj):
            break
        else:
            index += 1
    cur_index = index

    new_position = int(position)
    if new_position < 0 or new_position >= length:
        msg = '580 can not remove, index is out'
        raise RestfulError(msg)

    if cur_index != new_position:
        cur_obj = cur_startup_obj.pop(cur_index)
        cur_startup_obj.insert(new_position, cur_obj)
        # save meta data
        ret = set_meta_data(meta)
        if ret:
            # create new 'startup' conf file
            conf_file = '/opt/system/conf/restful-server/startup'
            ret = create_conf_by_list(conf_file, meta['software']['startup'], '', '')
    return True


def apply_tmp_program(info):
    app_name = info['name'] if 'name' in info.keys() else ''
    app_list = startup_app_list()
    if not app_name or not app_name in app_list:
        msg = '580 has no such program [' + app_name + ']'
        raise RestfulError(msg)

    init_sh = '/opt/program/bin/'+app_name+'/.init'
    if os.path.isfile(init_sh):
        cmd = 'su - mmap -c \"' + init_sh + ' start\"'
        if app_name == 'hvec':
            cmd = 'bash ' + init_sh + ' > /dev/null 2>&1'
        status, stdout, stderr = invoke_shell(cmd, False)
        if status != None:
            return False
    else:
        msg = '580 Error: this application has no .init shell script'
        raise RestfulError(msg)
    return True

def set_autostart(info):
    app_name = info['name'] if 'name' in info.keys() else ''
    app_startup = info['startup'] if 'startup' in info.keys() else ''

    if not app_name or not app_startup:
        msg = '580 params is wrong, must give name and startup item'
        raise RestfulError(msg)
    if not re.compile("^(on|off)$").match(app_startup):
        msg = '580 startup item wrong, just use on or off'
        raise RestfulError(msg)

    app_list = startup_app_list()
    if not app_name in app_list:
        msg = '580 has no such program [' + app_name + ']'
        raise RestfulError(msg)

    meta = get_meta_data()
    index = 0
    for item in meta['software']['startup']:
        if re.compile("^"+app_name).match(item):
            break
        else:
            index += 1

    if index >= 0 and index < len(meta['software']['startup']):
        meta['software']['startup'][index] = app_name+'|'+app_startup
    ret = set_meta_data(meta)
    if ret:
        conf_file = '/opt/system/conf/restful-server/startup'
        ret = create_conf_by_list(conf_file, meta['software']['startup'], '', '')
    return True

def set_stop(info):
    app_name = info['name'] if 'name' in info.keys() else ''

    if not app_name:
        msg = '580 params is wrong, must give name item'
        raise RestfulError(msg)

    app_list = startup_app_list()
    if not app_name in app_list:
        msg = '580 has no such program [' + app_name + ']'
        raise RestfulError(msg)

    init_sh = '/opt/program/bin/' + app_name + '/.init'
    if os.path.isfile(init_sh):
        cmd = 'su - mmap -c \"' + init_sh + ' stop\"'
        status, stdout, stderr = invoke_shell(cmd, False)
        if status != None:
            return False
    else:
        msg = '580 error: this application has no .init shell script'
        raise RestfulError(msg)
    return True

def set_restart(info):
    app_name = info['name'] if 'name' in info.keys() else ''

    if not app_name:
        msg = '580 params is wrong, must give name item'
        raise RestfulError(msg)

    app_list = startup_app_list()
    if not app_name in app_list:
        msg = '580 has no such program [' + app_name + ']'
        raise RestfulError(msg)

    init_sh = '/opt/program/bin/' + app_name + '/.init'
    if os.path.isfile(init_sh):
        cmd = 'su - mmap -c \"' + init_sh + ' restart\"'
        status, stdout, stderr = invoke_shell(cmd, False)
        if status != None:
            return False
    else:
        msg = '580 error: this application has no .init shell script'
        raise RestfulError(msg)
    return True

###############################################################################

class Startup:
    def GET(self):
        name_list = startup_all()
        if name_list:
            i = 0
            for name in name_list:
                name['position'] = "%d" % i
                i += 1
        return json.dumps(name_list)

    def PUT(self):
        input = json.loads(web.data())
        ret = startup_order(input)
        return json.dumps(ret)

    def POST(self):
        pass
    def DELETE(self):
        pass

class StartupExt:
    def GET(self, arg):
        pass

    def PUT(self, arg):
        if not arg in ['apply', 'autostart', 'stop', 'restart']:
            msg = '560 require path wrong'
            raise RestfulError(msg)
        data = web.data() if web.data() else '{}'

        if arg == 'apply':
            input = json.loads(data)
            ret = apply_tmp_program(input)
            return json.dumps(ret)
        elif arg == 'autostart':
            input = json.loads(data)
            ret = set_autostart(input)
            return json.dumps(ret)
        elif arg == 'stop':
            input = json.loads(data)
            ret = set_stop(input)
            return json.dumps(ret)
        elif arg == 'restart':
            input = json.loads(data)
            ret = set_restart(input)
            return json.dumps(ret)
        return

    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
