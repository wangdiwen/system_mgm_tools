import os
import sys
import re, json, types
from subprocess import Popen, PIPE

from common.restfulclient import RestfulError

# Note: These are global helper functions.

def check_ip_conflict_advanced(ip_addr = '', eth_list = ['eth0']):
    has_ip = False
    if not eth_list:
        eth_list.append('eth0')
    for eth in eth_list:
        shell = 'ping -c 1 ' + ip_addr + ' -w 1 -I ' + eth
        status, stdout, stderr = shell_cmd(shell)
        if status == 0:
            has_ip = True
    return has_ip

def check_ip_conflict(ip_addr = '127.0.0.1', eth = 'eth0'):
    shell = 'ping -c 1 ' + ip_addr + ' -w 1 -I ' + eth
    status, stdout, stderr = shell_cmd(shell)
    if status == 0:
        return True
    return False

def delete_mount_log(mount_point = ''):
    if not mount_point:
        return False
    meta = get_meta_data()
    mount_list = meta['storage']['device']
    for info in mount_list:
        if re.compile(".*"+mount_point+".*").match(info):
            mount_list.remove(info)
            break
    ret = set_meta_data(meta)
    if ret:
        # create new 'vmx_fstab' conf file
        conf_file = '/opt/system/etc/vmx-fstab'
        ret = create_conf_by_list(conf_file, meta['storage']['device'], '', '')
    return True

def record_mount_log(record = ''):
    if not record:
        return False
    meta = get_meta_data()
    meta['storage']['device'].append(record)
    ret = set_meta_data(meta)
    if ret:
        # create new 'vmx_fstab' conf file
        conf_file = '/opt/system/etc/vmx-fstab'
        ret = create_conf_by_list(conf_file, meta['storage']['device'], '', '')
    return True

def has_mount_record(mount_point):
    meta = get_meta_data()
    has_mount = False
    mount_list = meta['storage']['device']
    for dev_info in mount_list:
        if re.compile(".*"+mount_point+".*").match(dev_info):
            has_mount = True
            break
    return has_mount

def delete_rpm_log(rpm_name):
    meta = get_meta_data()
    ret = remove_list_by_value(meta['software']['installed'], rpm_name)
    has_startup = False
    for item in meta['software']['startup']:
        if re.compile("^"+rpm_name).match(item):
            has_startup = True
            ret = remove_list_by_value(meta['software']['startup'], item)
    # create 'startup' conf
    if has_startup:
        conf_file = '/opt/system/conf/restful-server/startup'
        ret = create_conf_by_list(conf_file, meta['software']['startup'], '', '')
    # save meta
    ret = set_meta_data(meta)
    return ret

def record_rpm_log(rpm_name):
    meta = get_meta_data()
    meta['software']['installed'].append(rpm_name)
    # record the auto startup software
    init_file = '/opt/program/bin/' + rpm_name + '/.init'
    if os.path.isfile(init_file):
        rpm_startup = rpm_name+'|on'
        meta['software']['startup'].append(rpm_startup)
        # create 'startup' conf file
        conf_file = '/opt/system/conf/restful-server/startup'
        ret = create_conf_by_list(conf_file, meta['software']['startup'], '', '')
    ret = set_meta_data(meta)
    return ret

def template_name(conf_file):
    temp_path = GlobalData.g_template_path
    temp_file = temp_path+'/'+conf_file
    if not os.path.isfile(temp_file):
        raise RestfulError('580 Error: '+ temp_file + ' not exist')
    return temp_file

def get_template_path():
    temp_path = GlobalData.g_template_path
    return temp_path

def engine_text_parse(conf_file, filter_exp = [], separator = '=', return_type = 'dict'):
    if not os.path.isfile(conf_file):
        raise Exception('Error: engine_text_parse : '+conf_file+' is not exist')
        return False
    if type(filter_exp) != types.ListType:
        raise Exception('Error: engine_text_parse : filter_exp type not list')
        return False
    if not return_type in ['list', 'dict']:
        raise Exception('Error: engine_text_parse : return_type not in list or dict')
        return False

    file = open(conf_file, 'r')
    lines = file.readlines()
    file.close()

    data_list = []
    data_dict = {}

    for exp in filter_exp:
        if return_type == 'list':
            for line in lines:
                line = line.strip("\n")
                if re.compile(exp).match(line):
                    if separator:
                        tmp_list = line.split(separator)
                        length = len(tmp_list)
                        if length >= 2:
                            data_list.append(tmp_list[1])
                    else:
                        data_list.append(line)
        elif return_type == 'dict':
            for line in lines:
                line = line.strip("\n")
                if re.compile(exp).match(line):
                    if separator:
                        tmp_list = line.split(separator)
                        length = len(tmp_list)
                        if length >= 2:
                            data_dict[tmp_list[0]] = tmp_list[1]

    if not filter_exp and return_type == 'dict':
        rule = re.compile("(?P<key>[\w]+)"+separator+"(?P<value>[\S]+)")
        for line in lines:
            rule_obj = rule.match(line.strip("\n"))
            if rule_obj:
                tmp_dict = rule_obj.groupdict()
                data_dict[tmp_dict["key"]] = tmp_dict["value"]

    if return_type == 'list':
        return data_list
    elif return_type == 'dict':
        return data_dict
    return None

def remove_list_by_value(var_list, var_value):
    if type(var_list) != types.ListType:
        return False
    tmp_list = list(var_list)
    for var in tmp_list:
        if var == var_value:
            var_list.remove(var)
    return True

def remove_list_by_list(var_list, in_list):
    if type(var_list) != types.ListType or type(in_list) != types.ListType:
        return False
    tmp_list = list(var_list)
    for var in tmp_list:
        if var in in_list:
            var_list.remove(var)
    return True

def remove_dict_by_value(var_dict, var_value):
    if type(var_dict) != types.DictType:
        return False
    keys = var_dict.keys()
    for key in keys:
        if var_dict[key] == var_value:
            del var_dict[key]
    return True

def remove_dict_by_key(var_dict, var_key):
    if type(var_dict) != types.DictType:
        return False
    keys = var_dict.keys()
    for key in keys:
        if key == var_key:
            del var_dict[key]
    return True

def create_conf_by_dict_append_context(save_file, var_dict, separator = '=', context = '', pre_title = ''):
    if type(var_dict) != types.DictType:
        return False

    context += "\n"
    keys = var_dict.keys()
    for key in keys:
        context += pre_title + key + separator + var_dict[key] + "\n"
    file = open(save_file, 'w')
    file.write(context)
    file.close()
    return True


def create_conf_by_dict(save_file, var_dict, separator = '='):
    if type(var_dict) != types.DictType:
        return False
    if not var_dict:
        return False

    context = ''
    keys = var_dict.keys()
    for key in keys:
        context += key + separator + var_dict[key] + "\n"
    file = open(save_file, 'w')
    file.write(context)
    file.close()
    return True

def create_conf_by_list(save_file, var_list, key = '', separator = '='):
    if type(var_list) != types.ListType:
        return False

    context = ''
    for var in var_list:
        context += key + separator + var + "\n"
    file = open(save_file, 'w')
    file.write(context)
    file.close()
    return True

def sync_run_config_file(run_file):
    if not os.path.isfile(run_file):
        raise Exception('Error: sync_run_config_file : '+run_file+' not exists')
        return False
    if not os.path.exists('/opt/system/etc/sysconfig/network-scripts/'):
        os.makedirs('/opt/system/etc/sysconfig/network-scripts/')
    shell = 'cp -a ' + run_file + ' /opt/system' + run_file
    status, stdout, stderr = shell_cmd(shell)
    if status != 0:
        return False
    return True

def sync_del_run_config_file(run_file):
    if not os.path.isfile(run_file):
        return False
    opt_run = '/opt/system' + run_file
    shell = '/usr/bin/shred -z -u ' + run_file + ' ' + opt_run
    status, stdout, stderr = shell_cmd(shell)
    if status != 0:
        return False
    return True

def json_echo(json_any):
    return json.dumps(json_any, indent=4)

def engine_render_template(conf_file, map_dict, save_file):
    if not os.path.isfile(conf_file):
        return False

    if type(map_dict) != types.DictType:
        return False

    file = open(conf_file, 'r')
    context = file.read()
    file.close()

    keys = map_dict.keys()
    for key in keys:
        tag = '{{' + key + '}}'
        context = context.replace(tag, map_dict[key])

    if os.path.isdir(save_file):
        msg = '580 Error: '+save_file+' is a directory'
        RestfulError(msg)
        return False

    file = open(save_file, 'w')
    file.write(context)
    file.close()
    return True

def set_meta_data(json_dict):
    conf = '/opt/system/conf/restful-server/global_meta_data.json'
    if not json_dict:
        return False
    file = open(conf, 'w')
    context = json.dumps(json_dict)
    file.write(context)
    file.close()
    return True

def get_meta_data():
    conf = '/opt/system/conf/restful-server/global_meta_data.json'
    if os.path.isfile(conf):
        file = open(conf, 'r')
        context = file.read()
        file.close()
        if context:
            return json.loads(context)
    return {}

def get_ntp_server():
    meta = get_meta_data()
    if meta and 'system' in meta.keys():
        if 'ntp-server' in meta['system'].keys():
            return meta['system']['ntp-server']
    return {}

def get_system_version():
    shell = 'head -1 /etc/issue | awk \'{print $3}\''
    status, stdout, stderr = shell_cmd(shell)
    if status == 0:
        return stdout.strip()
    return ''

def shell_cmd(cmd, wait = True):
    # Note: # wait-> status=0; no wait-> status=None
    stdout = ''
    status = 0
    stderr = ''

    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    if wait:
        process.wait()
    status = process.returncode
    stdout, stderr = process.communicate()
    return (status, stdout, stderr)

###############################################################################
#### Note: Below is global data, for get some vars
###############################################################################

class GlobalData(object):
    # global static data
    g_system_version = ''
    g_restful_root = ''
    g_template_path = ''

    def __init__(self):
        super(GlobalData, self).__init__()
        GlobalData.g_system_version = get_system_version()

    def set_restful_root(self, root_path):
        GlobalData.g_restful_root = root_path
        return

    def set_template_path(self):
        GlobalData.g_template_path = GlobalData.g_restful_root+'/template/'+GlobalData.g_system_version
        return
