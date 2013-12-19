from subprocess import Popen, PIPE
import os, re, commands, string
import shutil
import json
from restfulclient import RestfulError

###############################################################################
def get_sys_startup_mode():
    cur_mode = ''
    config = '/boot/grub/grub.conf'
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

def get_rpminfo(rpm_name):
    data = {}
    re_list = [
            "Name[ ]*:[ ]*(?P<name>[\w\-\_\.]+)",
            "[\w\:\t ]*Relocations[ ]*:[ ]*(?P<relocations>[\w\(\) ]+)",
            "Version[ ]*:[ ]*(?P<version>[\w\.]+)",
            "[\w\:\t\. ]*Vendor[ ]*:[ ]*(?P<vendor>[\w]+)",
            "Release[ ]*:[ ]*(?P<release>[\w\.\_]+)",
            "[\w\:\t\.\_ ]*Build Date[ ]*:[ ]*(?P<builddate>[\w\: ]+)",
            "Install Date[ ]*:[ ]*(?P<installdate>[\w\: ]+)[\t ]+Build Host:",
            "[\w\:\t ]*Build Host[ ]*:[ ]*(?P<buildhost>[\w\.]+)",
            "Group[ ]*:[ ]*(?P<group>[\w\/]+)",
            "[\w\:\t\/ ]*Source RPM[ ]*:[ ]*(?P<sourcerpm>[\w\-\.\_ ]+)",
            "Size[ ]*:[ ]*(?P<size>[\w]+)",
            "[\w\:\t ]*License[ ]*:[ ]*(?P<license>[\w]+)",
            "Signature[ ]*:[ ]*(?P<signature>[\w\/\,\: ]+)",
            "URL[ ]*:[ ]*(?P<url>[\w\:\/\. ]+)",
            "Summary[ ]*:[ ]*(?P<summary>[\w\(\)\,\+\-\. ]+)",
            "Description[ ]*:[ ]*(?P<description>[\w\(\)\, ]*)"
    ]

    if os.path.isfile(rpm_name):
        cmd = 'rpm -qpi ' + rpm_name
    else:
        cmd = 'rpm -qi ' + rpm_name

    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        lines = stdout.split("\n")
        data = {}
        description = ""
        for rule in re_list:
            for line in lines:
                ret = re.compile(rule).match(line)
                if ret:
                    _ret = ret.groupdict()
                    for key in _ret.keys():
                        data[key] = _ret[key].strip()

        length = len(lines)
        i = 0
        for line in lines:
            i += 1
            if re.compile("^Description").match(line):
                break
        description += string.join(lines[i:length])
        data['description'] = description
    return data

def check_ip(ipaddr = ''):
    value = True
    # if ipaddr == '0.0.0.0' or ipaddr == '127.0.0.1':
    #     value = False
    if not re.compile("^([1]?\d\d?|2[0-1]\d|22[0-3])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])$").match(ipaddr):
        value = False
    return value

def update_conf_file(conf_file, key, value, separator= '='):
    content = ''
    has_key = False
    if os.path.isfile(conf_file):
        file = open(conf_file, 'r')
        lines = file.readlines()
        file.close()

        for line in lines:
            if re.compile("^"+key).match(line):
                content += key+separator+value+"\n"
                has_key = True
            else:
                content += line
        if not has_key:
            content += key+separator+value+"\n"
        # print content
        file = open(conf_file, 'w')
        file.write(content)
        file.close()
    return

def auth_list():
    auth_user_file = '/opt/system/conf/restful-server/auth_user'
    data = {}
    rule = re.compile("(?P<key>[\w]+):(?P<value>[\w]+)")
    file = open(auth_user_file, 'r')
    lines = file.readlines()
    for line in lines:
        ret = rule.match(line)
        if ret:
            tmp_dict = ret.groupdict()
            data[tmp_dict['key']] = tmp_dict['value']
    file.close()
    return data

def rpm_query(name):
    if name:
        cmd = 'rpm -q ' + name
        status, stdout, stderr = invoke_shell(cmd)
        if stdout and re.compile(".*not installed").match(stdout):
            return False
        return True

def rpm_install(rpm_file):
    if os.path.isfile(rpm_file):
        # cmd = 'rpm -ivh ' + rpm_file + ' --nodeps --nomd5'
        cmd = 'rpm -ivh ' + rpm_file + ' --nomd5'
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            return True
    return False

def rpm_uninstall(name):
    data = {
        'status': False,
        'error': '',
    }
    cmd = 'rpm -e ' + name + ' --nodeps'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        data['status'] = True
    else:
        data['error'] = stdout.rstrip()
    return data

def rpm_update(rpm_file, nodeps, old_package = False):
    if os.path.isfile(rpm_file):
        if nodeps:
            cmd = 'rpm -Uvh ' + rpm_file + ' --nodeps --nomd5'
        else:
            cmd = 'rpm -Uvh ' + rpm_file + ' --nomd5'
        if old_package:
            cmd += ' --oldpackage'
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            return True
    return False

def invoke_shell(cmd, wait = True):     # wait-> status=0; no wait-> status=None
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout = ''
    status = 0
    stderr = ''
    if wait:
        process.wait()
    status = process.returncode
    stdout, stderr = process.communicate()
    return (status, stdout.rstrip("\n"), stderr.rstrip("\n"))

def get_key_value(file_name, exp_rule, separator):
    rule = re.compile(exp_rule)
    data = {}
    data['key'] = ''
    data['value'] = ''

    if os.path.isfile(file_name):
        file = open(file_name, 'r')
        lines = file.readlines()
        for line in lines:
            if rule.match(line.rstrip("\n")):
                tmp_list = line.split(separator)
                length = len(tmp_list)
                if length >= 2:
                    data['key'] = tmp_list[0].strip()
                    data['value'] = string.join(tmp_list[1:length], separator).strip()
        file.close()
    return data
