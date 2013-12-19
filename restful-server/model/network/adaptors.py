#!/usr/bin/python2.7

import web
import os
import time
import subprocess
import re
import json
import ifcfg
from ifcfg.parser import *          # third part, for parse ifconfig command
from common.restfulclient import RestfulError
from common import invoke_shell

from common.global_helper import *  # public helper functions

urls = (
    '', 'Adaptors',
    '/(.*)', 'AdaptorsExt'
)

class IfconfigParse(LinuxParser):
    class Meta:
        override_patterns = [
                            '(?P<device>^[a-zA-Z0-9\:]+)(.*)Link encap:(.*).*',
                            '(.*)Link encap:(.*)(HWaddr )(?P<hwaddr>[^\s]*).*',
                            '.*(Link encap:)(?P<linkencap>[^\s]*).*',
                            '.*(inet addr:)(?P<inet>[^\s]*).*',
                            '.*(inet6 addr: )(?P<inet6>[^\s\/]*/(?P<prefixlen>[\d]*)).*',
                            '.*(Bcast:)(?P<broadcast>[^\s]*).*',
                            '.*(Mask:)(?P<netmask>[^\s]*).*',
                            '.*(Scope:)(?P<scope>[^\s]*).*',
                            '.*(RX packets:)(?P<rxpackets>[\d]*).*(errors:)(?P<rxpacketerror>[\d]*).*(dropped:)(?P<rxpacketdropped>[\d]*).*(overruns:)(?P<rxpacketoverruns>[\d]*).*(frame:)(?P<rxpacketframe>[\d]*).*',
                            '.*(RX bytes:)(?P<rxbytes>[\d]*).*',
                            '.*(TX packets:)(?P<txpackets>[\d]*).*(errors:)(?P<txpacketerror>[\d]*).*(dropped:)(?P<txpacketdropped>[\d]*).*(overruns:)(?P<txpacketoverruns>[\d]*).*(carrier:)(?P<txpacketcarrier>[\d]*).*',
                            '.*(TX bytes:)(?P<txbytes>[\d]*).*',
                            '.*(MTU:)(?P<mtu>[\d]*).*',
                            '.*(Metric:)(?P<metric>[\d]*).*',
                            ]
    def __init__(self, *args, **kw):
        super(IfconfigParse, self).__init__(*args, **kw)

def get_all_iface():
    ifcfg_parse = IfconfigParse(ifconfig=None)
    interface = ifcfg_parse.interfaces.keys()
    list = []
    rule = re.compile('^eth[0-9](:[0-9])?$')
    for str in interface:
        if rule.match(str):
            list.append(str)
    return list

def get_iface_list():
    ifcfg_parse = IfconfigParse(ifconfig=None)
    interface = ifcfg_parse.interfaces.keys()
    list = []
    rule = re.compile('^eth[0-9]$')
    for str in interface:
        if rule.match(str):
            list.append(str)
    return list

def get_gateway(file_name):
    gw = ''
    file = open(file_name, 'r')
    if file:
        lines = file.readlines()
        for line in lines:
            if re.compile('^GATEWAY').match(line):
                tmp_list = line.rstrip("\n").split('=')
                gw = tmp_list[1].replace("\"", "")
        file.close()
    return gw

def get_bootproto(file_name):
    bootproto = ''
    file = open(file_name, 'r')
    if file:
        lines = file.readlines()
        for line in lines:
            if re.compile('^BOOTPROTO').match(line):
                tmp_list = line.rstrip("\n").split('=')
                bootproto = tmp_list[1].replace("\"", "")
        file.close()
    return bootproto

def get_all():
    ifcfg_parse = IfconfigParse(ifconfig=None)
    interface = ifcfg_parse.interfaces.keys()
    # print interface
    dev_list = []
    rule = re.compile('^eth[0-9]$')

    for name in interface:
        if rule.match(name):
            # print name
            dev_list.append(name)

    device = {}
    device['status'] = 'true'
    data = []
    for eth in dev_list:
        eth_dict = ifcfg_parse.interfaces[eth]
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % eth
        eth_dict['gateway'] = get_gateway(conf_file)
        eth_dict['bootproto'] = get_bootproto(conf_file)
        data.append(eth_dict)
    device['data'] = data
    return device

def get_device(device):
    ifcfg_parse = IfconfigParse(ifconfig=None)
    interface = ifcfg_parse.interfaces.keys()

    dev_list = []
    rule = re.compile('^eth')
    for name in interface:
        if rule.match(name):
            dev_list.append(name)

    if device in dev_list:
        eth_dict = ifcfg_parse.interfaces[device]
        conf_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % device
        eth_dict['gateway'] = get_gateway(conf_file)
        eth_dict['bootproto'] = get_bootproto(conf_file)
        return eth_dict
    else:
        return {}

def set_device(dev_info):
    data = {}

    device = dev_info['device']
    bootproto = dev_info['bootproto']
    ipaddr = ''
    if 'ipaddr' in dev_info.keys():
        ipaddr = dev_info['ipaddr']
    netmask = ''
    if 'netmask' in dev_info.keys():
        netmask = dev_info['netmask']
    gateway = ''
    if 'gateway' in dev_info.keys():
        gateway = dev_info['gateway']

    dev_list = get_iface_list()

    # check ip conflict
    has_ip_conflict = check_ip_conflict_advanced(ipaddr, dev_list)
    if has_ip_conflict:
        data['status'] = 'false'
        data['message'] = 'Ip conflict, already has ' + ipaddr
        return data

    if device in dev_list:
        if bootproto in ['dhcp', 'static']:
            meta = get_meta_data()
            meta['network']['adaptors'][device]['BOOTPROTO'] = bootproto
            if bootproto == 'static':
                meta['network']['adaptors'][device]['IPADDR'] = ipaddr
                meta['network']['adaptors'][device]['NETMASK'] = netmask
                meta['network']['adaptors'][device]['GATEWAY'] = gateway
                meta['network']['adaptors'][device]['ONBOOT'] = 'yes'
            ret = set_meta_data(meta)
            if ret:
                temp_conf = ''
                if re.compile('^eth[0-9]$').match(device):
                    temp_conf = template_name('ifcfg-ethx')
                else:
                    temp_conf = template_name('ifcfg-ethx:x')
                run_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % device
                map_dict = meta['network']['adaptors'][device]
                ret = engine_render_template(temp_conf, map_dict, run_file)
                ret = sync_run_config_file(run_file)

                # sync '/etc/sysconfig/network' config file
                temp_conf = template_name('network')
                run_file = '/etc/sysconfig/network'
                map_dict = {'HOSTNAME': meta['network']['hostname'],
                            'GATEWAY': meta['network']['adaptors'][device]['GATEWAY'],
                            }
                ret = engine_render_template(temp_conf, map_dict, run_file)
                ret = sync_run_config_file(run_file)
        else:
            data['status'] = 'false'
            data['message'] = "invalid bootproto %s" % bootproto
            return data

        # Restart the network
        cmd = '/etc/rc.d/init.d/network restart'
        status, stdout, stderr = invoke_shell(cmd, False)
        if status != None:
            data['status'] = 'false'
            data['message'] = "restart the network failed"
        else:
            data['status'] = 'true'
            data['message'] = "set %s %s success" % (device, bootproto)
        return data
    else:
        data['status'] = 'false'
        data['message'] = "invalid device %s" % device
        return data

def get_device_ipinfo(dev):
    data = []
    ifcfg_parse = IfconfigParse(ifconfig=None)
    interface = ifcfg_parse.interfaces.keys()
    if not dev in interface:
        error = '560 has no such device ['+dev+']'
        raise RestfulError(error)
        return

    for dev_name in interface:
        if re.compile("^"+dev).match(dev_name):
            dict = {}
            eth_dict = ifcfg_parse.interfaces[dev_name]
            dict['device'] = eth_dict['device']
            dict['ipaddr'] = eth_dict['inet']
            dict['netmask'] = eth_dict['netmask']
            conf_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % dev
            dict['gateway'] = get_gateway(conf_file)
            data.append(dict)

    return data

def check_ip_or_netmask(ipaddr = '', netmask = ''):
    value = True
    if ipaddr:
        if ipaddr == '0.0.0.0' or ipaddr == '127.0.0.1':
            value = False
        if not re.compile("^([1]?\d\d?|2[0-1]\d|22[0-3])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])$").match(ipaddr):
            value = False
    if netmask:
        if not re.compile("^(0|255)\.(0|255)\.(0|255)\.(0|255)").match(netmask):
            value = False
    return value

def check_ip_invalid(ipaddr = ''):
    value = True
    if ipaddr == '0.0.0.0' or ipaddr == '127.0.0.1':
        value = False
    if not re.compile("^([1]?\d\d?|2[0-1]\d|22[0-3])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])\.([01]?\d\d?|2[0-4]\d|25[0-4])$").match(ipaddr):
        value = False
    return value

def bind_multi_ipaddr(info):
    field = info.keys()
    if not 'device' in field or not 'ipaddr' in field or not 'netmask' in field:
        msg = '560 input data, less arguments'
        raise RestfulError(msg)

    device = info['device']
    ipaddr = info['ipaddr']
    netmask = info['netmask']
    gateway = info['gateway'] if 'gateway' in field else ''
    check_ip = check_ip_or_netmask(ipaddr, netmask)
    if not check_ip:
        msg = '560 ipaddr or netmask is wrong'
        raise RestfulError(msg)

    # get the ethx info
    interface = get_iface_list()
    if not device in interface:
        msg = '560 has no such device ' + device
        raise RestfulError(msg)

    # check ip conflict
    has_ip_conflict = check_ip_conflict_advanced(ipaddr, interface)
    if has_ip_conflict:
        msg = 'Ip conflict, already has ' + ipaddr
        raise RestfulError(msg)

    # check the device proto: is static or dhcp
    device_info = get_device(device)
    bootproto = device_info['bootproto']
    if bootproto != 'static':
        msg = '560 device bootproto is dhcp, can not set multi ip address'
        raise RestfulError(msg)

    ifcfg_parse = IfconfigParse(ifconfig=None)  # ifconfig parse obj, from third party python lib

    dev_bind = []
    dev_bind_ip = []
    for inter in get_all_iface():
        if re.compile("^"+device).match(inter):
            dev_bind.append(inter)
            dev_bind_ip.append(ifcfg_parse.interfaces[inter]['inet'])

    new_dev = ''
    for num in range(0, 254):
        dev_name = "%s:%d" % (device, num)
        if not dev_name in dev_bind:
            new_dev = dev_name
            break

    new_dev_conf = "/etc/sysconfig/network-scripts/ifcfg-" + new_dev
    old_dev_conf = "/etc/sysconfig/network-scripts/ifcfg-" + device
    # check the new child device
    if not new_dev:
        msg = '560 create new child device of failed ' + device
        raise RestfulError(msg)
        return
    # check the input ipaddr
    if ipaddr in dev_bind_ip:
        msg = ' 560 the new ipaddr has existed'
        raise RestfulError(msg)
        return

    # add meta data
    meta = get_meta_data()
    new_ethx = dict(meta['network']['adaptors'][device])

    ret = remove_dict_by_key(new_ethx, 'ETHTOOL_OPTS')
    new_ethx['DEVICE'] = new_dev
    new_ethx['BOOTPROTO'] = 'static'
    new_ethx['IPADDR'] = ipaddr
    new_ethx['NETMASK'] = netmask
    new_ethx['GATEWAY'] = gateway

    meta['network']['adaptors'][new_dev] = new_ethx
    ret = set_meta_data(meta)
    if ret:
        # render template conf file
        temp_conf = template_name('ifcfg-ethx:x')
        run_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % new_dev
        map_dict = meta['network']['adaptors'][new_dev]
        ret = engine_render_template(temp_conf, map_dict, run_file)
        ret = sync_run_config_file(run_file)

    cmd = '/etc/rc.d/init.d/network restart'
    status, stdout, stderr = invoke_shell(cmd, False)
    if status != None:
        return False
    return True

def del_bind_ipaddr(info):
    field = info.keys()
    if not 'ipaddr' in field or not 'device' in field:
        msg = '560 input data, less arguments'
        raise RestfulError(msg)

    device = info['device']
    ipaddr = info['ipaddr']
    # check the value
    check_ip = check_ip_invalid(ipaddr)
    if not check_ip:
        msg = '560 ipaddr is wrong'
        raise RestfulError(msg)

    # check the device exist or not
    device_list = get_iface_list()
    if not device in device_list:
        msg = '560 this device is not existed [' + device + ']'
        raise RestfulError(msg)
    # check the device proto: is static or dhcp
    device_info = get_device(device)
    bootproto = device_info['bootproto']
    if bootproto != 'static':
        msg = '560 device bootproto is dhcp, can not set multi ip address'
        raise RestfulError(msg)
    # check ip address
    dev_ipinfo = get_device_ipinfo(device)
    slave_dev_list = []
    dev_name = ''
    for ipinfo in dev_ipinfo:
        if ipinfo['ipaddr'] == ipaddr:
            dev_name = ipinfo['device']
        if re.compile("^eth[0-9]:").match(ipinfo['device']):
            slave_dev_list.append(ipinfo['device'])

    if not dev_name:
        msg = '560 this device has no such address [' + ipaddr + ']'
        raise RestfulError(msg)

    # check the device name is 'eth0' or 'eth0:0'?
    if re.compile("^eth[0-9]$").match(dev_name):  # master dev
        # print 'master device'
        # first, del the 'ethx', x is most big num
        if slave_dev_list:
            slave_dev_list.sort()
        big_dev_name = slave_dev_list[-1] if slave_dev_list else ''
        if not big_dev_name:                # just master dev
            # print 'auto set to dhcp mode'
            meta = get_meta_data()
            meta['network']['adaptors'][dev_name]['BOOTPROTO'] = 'dhcp'
            ret = set_meta_data(meta)
            if ret:
                temp_conf = template_name('ifcfg-ethx')
                run_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % dev_name
                map_dict = meta['network']['adaptors'][dev_name]
                ret = engine_render_template(temp_conf, map_dict, run_file)
                ret = sync_run_config_file(run_file)
        else:                           # has slave dev
            # print 'delete slave bind device, and update the master device'
            meta = get_meta_data()
            big_dev_ip = meta['network']['adaptors'][big_dev_name]['IPADDR']
            ret = remove_dict_by_key(meta['network']['adaptors'], big_dev_name)
            meta['network']['adaptors'][device]['BOOTPROTO'] = 'static'
            meta['network']['adaptors'][device]['IPADDR'] = big_dev_ip
            ret = set_meta_data(meta)
            if ret:
                # del slave etc conf
                run_big_conf = '/etc/sysconfig/network-scripts/ifcfg-' + big_dev_name
                ret = sync_del_run_config_file(run_big_conf)
                # sync etc conf
                temp_conf = template_name('ifcfg-ethx')
                run_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % device
                map_dict = meta['network']['adaptors'][device]
                ret = engine_render_template(temp_conf, map_dict, run_file)
                ret = sync_run_config_file(run_file)

        # restart the net
        cmd = '/etc/rc.d/init.d/network restart'
        status, stdout, stderr = invoke_shell(cmd, False)
        if status != None:
            return False
    else:                                         # slave dev
        # print 'slave device'
        meta = get_meta_data()
        ret = remove_dict_by_key(meta['network']['adaptors'], dev_name)
        ret = set_meta_data(meta)
        if ret:
            run_file = "/etc/sysconfig/network-scripts/ifcfg-" + dev_name
            ret = sync_del_run_config_file(run_file)

        # restart the net
        cmd = '/etc/rc.d/init.d/network restart'
        status, stdout, stderr = invoke_shell(cmd, False)
        if status != None:
            return False
    return True

def get_device_mode(device):
    dev_list = get_iface_list()
    if not device in dev_list:
        error = '560 has no such device ['+device+']'
        raise RestfulError(error)
        return

    # get the info of adaptor
    data = {}
    data['speed'] = ''
    data['duplex'] = ''
    data['auto-negotiation'] = ''
    cmd = 'ethtool ' + device
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        for line in stdout.split("\n"):
            field = line.strip()
            field_list = field.split(":")
            if re.compile("^Speed").match(field):
                data['speed'] = field_list[1].strip()
            if re.compile("^Duplex").match(field):
                data['duplex'] = field_list[1].strip()
            if re.compile("^Auto-negotiation").match(field):
                data['auto-negotiation'] = field_list[1].strip()
    return data

def set_device_mode(info):
    device = info['device']
    speed = info['speed'] if 'speed' in info.keys() else ''
    duplex = info['duplex'] if 'duplex' in info.keys() else ''
    negotiation = info['auto-negotiation'] if 'auto-negotiation' in info.keys() else ''

    if not speed or not duplex or not negotiation:
        msg = '560 input data, less arguments'
        raise RestfulError(msg)
        return
    if not re.compile("^(10Mb\/s|100Mb\/s|1000Mb\/s)$").match(speed):
        msg = '560 speed is wrong, use 10, 100, 1000'
        raise RestfulError(msg)
    if not re.compile("^(full|half|Full|Half)$").match(duplex):
        msg = '560 duplex is wrong, use Full or Half'
        raise RestfulError(msg)
    if not re.compile("^(on|off)$").match(negotiation):
        msg = '560 auto-negotiation is wrong, use on or off'
        raise RestfulError(msg)

    dev_list = get_iface_list()
    if not device in dev_list:
        error = '560 has no such device ['+device+']'
        raise RestfulError(error)
        return

    # get speed number
    duplex = duplex.lower()
    speed = speed.replace('Mb/s', '')
    # set the work mode of adaptor
    cmd = 'ethtool -s ' + device + ' speed ' + speed + ' duplex ' + duplex + ' autoneg ' + negotiation
    # print cmd
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        meta = get_meta_data()
        meta['network']['adaptors'][device]['ETHTOOL_OPTS'] = 'speed '+speed+' duplex '+duplex+' autoneg '+negotiation
        ret = set_meta_data(meta)
        if ret:
            temp_conf = template_name('ifcfg-ethx')
            run_file = '/etc/sysconfig/network-scripts/ifcfg-%s' % device
            map_dict = meta['network']['adaptors'][device]
            ret = engine_render_template(temp_conf, map_dict, run_file)
            ret = sync_run_config_file(run_file)
    else:
        msg = '580 config the adaptor mode, failed'
        raise RestfulError(msg)
    return

def get_adaptors_list():
    dev_list = []
    meta = get_meta_data()
    if 'network' in meta.keys() and 'adaptors' in meta['network'].keys():
        adaptor_list = meta['network']['adaptors'].keys()
        rule = re.compile('^eth[0-9]+$')
        for adaptor in adaptor_list:
            if rule.match(adaptor):
                dev_list.append(adaptor)
    return dev_list

###############################################################################
class Adaptors:
    def GET(self):
        data = get_all()
        status = data['status']
        if status == 'true':
            del data['status']
            return json.dumps(data['data'])
        else:
            msg = "560 get adaptors info error"
            raise RestfulError(msg)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

class AdaptorsExt:
    def GET(self, arg):
        if re.compile('^eth[0-9](:[0-9])?$').match(arg):
            device = get_device(arg)
            if device:
                return json.dumps(device)
            else:
                msg = "560 has no such device %s" % arg
                raise RestfulError(msg)
        elif re.compile("^eth[0-9]\/ipinfo").match(arg):
            device = arg.split('/')[0]
            ipinfo = get_device_ipinfo(device)
            return json.dumps(ipinfo)
        elif re.compile("^eth[0-9]\/workmode").match(arg):
            device = arg.split('/')[0]
            mode_info = get_device_mode(device)
            return json.dumps(mode_info)
        elif arg == 'devices':
            device_list = get_adaptors_list()
            return json.dumps(device_list)
        else:
            msg = "560 invalid arguments %s" % arg
            raise RestfulError(msg)

    def PUT(self, arg):
        if re.compile('^eth[0-9]$').match(arg):
            data = {}
            input = json.loads(web.data())
            data = set_device(input)
            status = data['status']
            if status == 'true':
                return
            else:
                msg = "560 %s" % data['message']
                raise RestfulError(msg)
        elif re.compile("^eth[0-9]\/workmode").match(arg):
            device = arg.split('/')[0]
            input = json.loads(web.data())
            input['device'] = device
            info = set_device_mode(input)
            return json.dumps(info)
        else:
            msg = "560 invalid device %s" % arg
            raise RestfulError(msg)

    def POST(self, arg):
        if re.compile("^eth[0-9]$").match(arg):
            input = json.loads(web.data())
            input['device'] = arg
            ret = bind_multi_ipaddr(input)
            return json.dumps(ret)
        else:
            msg = "560 invalid device %s" % arg
            raise RestfulError(msg)
    def DELETE(self, arg):
        if re.compile("^eth[0-9]$").match(arg):
            input = json.loads(web.data())
            input['device'] = arg
            ret = del_bind_ipaddr(input)
            return json.dumps(ret)
        else:
            msg = "560 invalid device %s" % arg
            raise RestfulError(msg)

app = web.application(urls, locals())
