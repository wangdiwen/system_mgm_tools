#!/usr/bin/python

import web
import json
import subprocess
import re
import string
import types
from common.restfulclient import RestfulError
from common import invoke_shell

from common.global_helper import *  # public helper functions

urls = (
    '', 'Iptables'
)

def exec_iptables(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    status = process.returncode
    stdout, stderr = process.communicate()
    return (status, stdout)

def get_table(content):
    part_dict = {}

    parts = content.split("\n\n")
    for part in parts:
        part_name = ''
        part_list = []

        lines = part.split("\n")
        for line in lines:
            tmp_dict = {}

            if re.compile('^Chain ').match(line):
                part_name = line.split()[1]
            elif re.compile('^[0-9]').match(line):
                tmp_list = line.split()
                tmp_dict['number'] = tmp_list[0]
                tmp_dict['target'] = tmp_list[3]
                tmp_dict['prot'] = tmp_list[4]
                tmp_dict['opt'] = tmp_list[5]
                tmp_dict['in-interface'] = tmp_list[6]
                tmp_dict['out-interface'] = tmp_list[7]
                tmp_dict['source'] = tmp_list[8]
                tmp_dict['destination'] = tmp_list[9]
                tmp_dict['method'] = '*'
                tmp_dict['match'] = '*'
                tmp_dict['state'] = '*'
                tmp_dict['dport'] = '*'
                tmp_dict['to-port'] = '*'
                tmp_dict['attach'] = '*'
                # tmp_dict['to-port'] = ''

                if len(tmp_list) >= 11:
                    length = len(tmp_list)
                    attach = string.join(tmp_list[10:length])
                    attach_list = attach.split()
                    attach_len = len(attach_list)

                    list0 = attach_list[0]
                    if list0 in ('udp', 'tcp'):
                        tmp_dict['match'] = list0
                    elif list0 in ('state', 'icmp'):
                        tmp_dict['method'] = list0
                        if attach_len > 2:
                            tmp_dict['state'] = attach_list[1]
                            tmp_dict['match'] = attach_list[2]
                    else:
                        tmp_dict['attach'] = attach
                    ret_dport = re.compile("(?P<key>.*)dpt:(?P<value>[0-9]+$)").match(attach)
                    if ret_dport:
                        tmp_dict['dport'] = ret_dport.groupdict()['value']
                    ret_to = re.compile(".*dpt:(?P<key>[0-9]+) to:(?P<value>.*)").match(attach)
                    if ret_to:
                        tmp_dict['dport'] = ret_to.groupdict()['key']
                        tmp_dict['to-port'] = ret_to.groupdict()['value']

            if tmp_dict:
                part_list.append(tmp_dict)

        part_dict[part_name] = part_list

    return part_dict

def get_all():
    data = {}
    # table filter
    cmd = '/sbin/iptables -t filter -L -n --line-numbers -v'
    status, stdout = exec_iptables(cmd)
    if status == 0:
        filter_dict = get_table(stdout)
        data['filter'] = filter_dict
    # table nat
    cmd = '/sbin/iptables -t nat -L -n --line-numbers -v'
    status, stdout = exec_iptables(cmd)
    if status == 0:
        nat_dict = get_table(stdout)
        data['nat'] = nat_dict
    # table mangle
    cmd = '/sbin/iptables -t mangle -L -n --line-numbers -v'
    status, stdout = exec_iptables(cmd)
    if status == 0:
        mangle_dict = get_table(stdout)
        data['mangle'] = mangle_dict

    return data

def out_error(error):
    data = {}
    data['status'] = 'false'
    data['message'] = error
    return data

def open_port_forward():
    status, stdout, stderr = invoke_shell("cat /proc/sys/net/ipv4/ip_forward")
    if status == 0:
        if stdout == '0':
            cmd = "sysctl -w net.ipv4.ip_forward=1"
            status, stdout, stderr = invoke_shell(cmd)
            # modify the '/etc/sysctl.conf'
            temp_conf = template_name('sysctl.conf')
            run_file = '/etc/sysctl.conf'
            map_dict = {'IPFORWARD': '1'}
            ret = engine_render_template(temp_conf, map_dict, run_file)
            ret = sync_run_config_file(run_file)
    return True

def add_iptables(rules):
    error = ''                     # check the params
    table = ''
    if 'table' in rules.keys():
        table = rules['table']
        if not re.compile('[filter|nat|mangle]').match(table):
            error = 'invalid table name, use [filter|nat|mangle]'
            return out_error(error)
    chain = ''
    if 'chain' in rules.keys():
        chain = rules['chain']
        if not re.compile("[PREROUTING|POSTROUTING|INPUT|OUTPUT|FORWARD|RH\-Firewall\-1\-INPUT]").match(chain):
            error = 'invalid chain, use [PREROUTING|POSTROUTING|INPUT|OUTPUT|FORWARD|RH-Firewall-1-INPUT]'
            return out_error(error)
    source = ''
    if 'source' in rules.keys():
        source = rules['source']
        # print source
        if not re.compile("^((\d)+.(\d)+.(\d)+.(\d)+(\/\d+)?)?$").match(source):
            error = 'invalid source ip address'
            # print error
            return out_error(error)
    destination = ''
    if 'destination' in rules.keys():
        destination = rules['destination']
        if not re.compile("^((\d)+.(\d)+.(\d)+.(\d)+(\/\d+)?)?$").match(destination):
            error = 'invalid destination ip address'
            return out_error(error)
    position = 0
    if 'position' in rules.keys():
        position = rules['position']
        if position:
            if not type(position) is types.IntType:
                error = 'invalid position, not a number'
                return out_error(error)
            if not position > 0:
                error = 'invalid position, must > 0'
                return out_error(error)
    in_interface = ''
    if 'in-interface' in rules.keys():
        in_interface = rules['in-interface']
        if not re.compile('(^(eth[0-9]+|lo)$)?').match(in_interface):
            error = 'invalid in-interface device'
            return out_error(error)
    out_interface = ''
    if 'out-interface' in rules.keys():
        out_interface = rules['out-interface']
        if not re.compile('(^(eth[0-9]+|lo)$)?').match(out_interface):
            error = 'invalid out-interface device'
            return out_error(error)
    protocol = ''
    if 'protocol' in rules.keys():
        protocol = rules['protocol']
        if not re.compile('([tcp|udp|icmp|esp|ah|all])?').match(protocol):
            error = 'invalid protocol, use [tcp|udp|icmp|esp|ah|all]'
            return out_error(error)
    method = ''
    if 'method' in rules.keys():
        method = rules['method']
        if not re.compile('([state|icmp])?').match(method):
            error = 'invalid method, use [state|icmp] method'
            return out_error(error)
    state = ''
    if 'state' in rules.keys():
        state = rules['state']
    match = ''
    if 'match' in rules.keys():
        match = rules['match']
    dport = ''
    if 'dport' in rules.keys():
        dport = rules['dport']
        if not re.compile('^[0-9]*$').match(dport):
            error = 'invalid dport, must be a number string'
            return out_error(error)
    action = ''
    if 'action' in rules.keys():
        action = rules['action']
        if not re.compile("[DROP|SNAT|DNAT|LOG|ACCEPT|REJECT|RH\-Firewall\-1\-INPUT]").match(action):
            error = 'invalid action, use [DROP|SNAT|LOG|ACCEPT|REJECT|RH\-Firewall\-1\-INPUT]'
            return out_error(error)
    to_port = ''
    if 'to-port' in rules.keys():
        to_port = rules['to-port']
        if not re.compile("^([\d]+.[\d]+.[\d]+.[\d]+)*(:[0-9]+)?$").match(to_port):
            error = 'invalid port forward address'
            return out_error(error)

    data = {}
    cmd = "iptables "
    if table in ['filter', 'nat', 'mangle']:
        cmd += "-t " + table + " "
        if position and position > -1:   # insert define pos
            cmd = "%s -I %s %d " % (cmd, chain, position)
        else:
            cmd += "-A " + chain + " "
        if source:
            cmd += "-s " + source + " "
        if destination:
            cmd += "-d " + destination + " "
        if in_interface:
            cmd += "-i " + in_interface + " "
        if out_interface:
            cmd += "-o " + out_interface + " "
        if protocol:
            if not protocol == 'all':
                cmd += "-p " + protocol + " "
        if method:
            cmd += "-m " + method + " "
        if state:
            if method == 'state':
                cmd += "--state " + state + " "
            elif method == 'icmp':
                cmd += "--icmp-type " + state + " "
        if match:
            cmd += "-m " + match + " "
        if dport:
            if not protocol == 'all':
                cmd += "--dport " + dport + " "
        if action:
            cmd += "-j " + action + " "
        if to_port:
                cmd += "--to " + to_port
        # print cmd

        # Set port forward
        if re.compile(".*nat.*--to.*").match(cmd):
            open_port_forward()

        status, stdout = exec_iptables(cmd)
        if status == 0:
            cmd = "/etc/init.d/iptables save"
            status, stdout = exec_iptables(cmd)
            if status == 0:
                run_file = '/etc/sysconfig/iptables'
                ret = sync_run_config_file(run_file)

                data['status'] = 'true'
                data['message'] = "add iptables rules success"
                return data
            else:
                data['status'] = 'false'
                data['message'] = "save iptables rules failed"
                return data
        else:
            data['status'] = 'false'
            data['message'] = "add iptables rules failed"
            return data
    else:
        data['status'] = 'false'
        data['message'] = "invalid table %s" % table
        return data

def order_iptables(info):
    field = info.keys()
    position = info['position'] if 'position' in field else -1
    to_position = info['to-position'] if 'to-position' in field else -1
    table = info['table'] if 'table' in field else ''
    chain = info['chain'] if 'chain' in field else ''
    source = info['source'] if 'source' in field else ''
    destination = info['destination'] if 'destination' in field else ''
    in_interface = info['in-interface'] if 'in-interface' in field else ''
    out_interface = info['out-interface'] if 'out-interface' in field else ''
    protocol = info['protocol'] if 'protocol' in field else ''
    method = info['method'] if 'method' in field else ''
    state = info['state'] if 'state' in field else ''
    match = info['match'] if 'match' in field else ''
    dport = info['dport'] if 'dport' in field else ''
    action = info['action'] if 'action' in field else ''
    to_port = info['to-port'] if 'to-port' in field else ''

    if position != -1 and to_position != -1:
        # del the old pos rule
        cmd = "iptables -t %s -D %s %d" % (table, chain, position)
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            cmd = "/etc/init.d/iptables save"
            sta, out, err = invoke_shell(cmd)
            if sta != 0:
                return False
        else:
            return False

        # add the rule to new pos
        cmd = "iptables "
        if table in ['filter', 'nat', 'mangle']:
            cmd += "-t " + table + " "
            if to_position and to_position > -1:   # insert define pos
                cmd = "%s -I %s %d " % (cmd, chain, to_position)
            else:
                cmd += "-A " + chain + " "
            if source:
                cmd += "-s " + source + " "
            if destination:
                cmd += "-d " + destination + " "
            if in_interface:
                cmd += "-i " + in_interface + " "
            if out_interface:
                cmd += "-o " + out_interface + " "
            if protocol:
                if not protocol == 'all':
                    cmd += "-p " + protocol + " "
            if method:
                cmd += "-m " + method + " "
            if state:
                if method == 'state':
                    cmd += "--state " + state + " "
                elif method == 'icmp':
                    cmd += "--icmp-type " + state + " "
            if match:
                cmd += "-m " + match + " "
            if dport:
                if not protocol == 'all':
                    cmd += "--dport " + dport + " "
            if action:
                cmd += "-j " + action + " "
            if to_port:
                    cmd += "--to " + to_port
            # print cmd

            # Set port forward
            if re.compile(".*nat.*--to.*").match(cmd):
                open_port_forward()

            status, stdout, stderr = invoke_shell(cmd)
            if status == 0:
                cmd = "/etc/init.d/iptables save"
                sta, out, err = invoke_shell(cmd)
                if sta == 0:
                    # sync etc conf file
                    run_file = '/etc/sysconfig/iptables'
                    ret = sync_run_config_file(run_file)
                    return True
    return False

def del_iptables(rules):
    error = ''                     # check the params
    table = ''
    if 'table' in rules.keys():
        table = rules['table']
        if not re.compile('[filter|nat|mangle]').match(table):
            error = 'invalid table name, use [filter|nat|mangle]'
            return out_error(error)
    chain = ''
    if 'chain' in rules.keys():
        chain = rules['chain']
        if not re.compile("[PREROUTING|POSTROUTING|INPUT|OUTPUT|FORWARD|RH\-Firewall\-1\-INPUT]").match(chain):
            error = 'invalid chain, use [PREROUTING|POSTROUTING|INPUT|OUTPUT|FORWARD|RH-Firewall-1-INPUT]'
            return out_error(error)
    source = ''
    if 'source' in rules.keys():
        source = rules['source']
        if not re.compile("^((\d)+.(\d)+.(\d)+.(\d)+(\/\d)?)?$").match(source):
            error = 'invalid source ip address'
            return out_error(error)
    destination = ''
    if 'destination' in rules.keys():
        destination = rules['destination']
        if not re.compile("^((\d)+.(\d)+.(\d)+.(\d)+(\/\d)?)?$").match(destination):
            error = 'invalid destination ip address'
            return out_error(error)
    position = 0
    if 'position' in rules.keys():
        position = rules['position']
        if position:
            if not type(position) is types.IntType:
                error = 'invalid position, not a number'
                return out_error(error)
            if not position > 0:
                error = 'invalid position, must > 0'
                return out_error(error)
    in_interface = ''
    if 'in-interface' in rules.keys():
        in_interface = rules['in-interface']
        if not re.compile('(^(eth[0-9]+|lo)$)?').match(in_interface):
            error = 'invalid in-interface device'
            return out_error(error)
    out_interface = ''
    if 'out-interface' in rules.keys():
        out_interface = rules['out-interface']
        if not re.compile('(^(eth[0-9]+|lo)$)?').match(out_interface):
            error = 'invalid out-interface device'
            return out_error(error)
    protocol = ''
    if 'protocol' in rules.keys():
        protocol = rules['protocol']
        if not re.compile('([tcp|udp|icmp|esp|ah|all])?').match(protocol):
            error = 'invalid protocol, use [tcp|udp|icmp|esp|ah|all]'
            return out_error(error)
    method = ''
    if 'method' in rules.keys():
        method = rules['method']
        if not re.compile('([state|icmp])?').match(method):
            error = 'invalid method, use [state|icmp] method'
            return out_error(error)
    state = ''
    if 'state' in rules.keys():
        state = rules['state']
    match = ''
    if 'match' in rules.keys():
        match = rules['match']
    dport = ''
    if 'dport' in rules.keys():
        dport = rules['dport']
        if not re.compile('^[0-9]*$').match(dport):
            error = 'invalid dport, must be a number string'
            return out_error(error)
    action = ''
    if 'action' in rules.keys():
        action = rules['action']
        if not re.compile("([DROP|SNAT|DNAT|LOG|ACCEPT|REJECT|RH\-Firewall\-1\-INPUT])?").match(action):
            error = 'invalid action, use [DROP|SNAT|LOG|ACCEPT|REJECT|RH\-Firewall\-1\-INPUT]'
            return out_error(error)
    to_port = ''
    if 'to-port' in rules.keys():
        to_port = rules['to-port']
        if not re.compile("^(\d)+.(\d)+.(\d)+.(\d)+(:[0-9]+)?$").match(to_port):
            error = 'invalid port forward address'
            return out_error(error)

    data = {}
    cmd = "iptables "
    if table in ['filter', 'nat', 'mangle']:
        if chain and position > -1:
            cmd = "%s -t %s -D %s %d" % (cmd, table, chain, position)
        else:
            cmd += "-t " + table + " "
            if chain:
                cmd += "-D " + chain + " "
            if source:
                cmd += "-s " + source + " "
            if destination:
                cmd += "-d " + destination + " "
            if in_interface:
                cmd += "-i " + in_interface + " "
            if out_interface:
                cmd += "-o " + out_interface + " "
            if protocol:
                if not protocol == 'all':
                    cmd += "-p " + protocol + " "
            if method:
                cmd += "-m " + method + " "
            if state:
                if method == 'state':
                    cmd += "--state " + state + " "
                elif method == 'icmp':
                    cmd += "--icmp-type " + state + " "
            if match:
                cmd += "-m " + match + " "
            if dport:
                if not protocol == 'all':
                    cmd += "--dport " + dport + " "
            if action:
                cmd += "-j " + action + " "
            if to_port:
                cmd += "--to " + to_port
        # print cmd

        status, stdout = exec_iptables(cmd)
        if status == 0:
            cmd = "/etc/init.d/iptables save"
            status, stdout = exec_iptables(cmd)
            if status == 0:
                run_file = '/etc/sysconfig/iptables'
                ret = sync_run_config_file(run_file)

                data['status'] = 'true'
                data['message'] = "delete iptables rules success"
                return data
            else:
                data['status'] = 'false'
                data['message'] = "save iptables rules failed"
                return data
        else:
            data['status'] = 'false'
            data['message'] = "delete iptables rules failed"
            return data
    else:
        data['status'] = 'false'
        data['message'] = "invalid table %s" % table
        return data

class Iptables:
    def GET(self):
        data = get_all()
        return json.dumps(data)

    def PUT(self):
        input = json.loads(web.data())
        ret = order_iptables(input)
        if not ret:
            msg = '580 order the iptables position failed'
            raise RestfulError(msg)
        return json.dumps(ret)

    def POST(self):
        input = json.loads(web.data())
        data = add_iptables(input)

        status = data['status']
        if status == 'true':
            return
        else:
            msg = "560 %s" % data['message']
            raise RestfulError(msg)

    def DELETE(self):
        input = json.loads(web.data())
        data = del_iptables(input)
        status = data['status']
        if status == 'true':
            return
        else:
            msg = "560 %s" % data['message']
            raise RestfulError(msg)

app = web.application(urls, locals())
