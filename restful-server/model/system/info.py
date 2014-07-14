#!/usr/bin/python2.7

import os, json, datetime
import web
import re

from common import invoke_shell, get_rpminfo

urls = (
  "", "SystemInfo",
  "/(.*)", "SystemInfoExt",
)

def memory_stat():
    mem = {}
    f = open("/proc/meminfo")
    data = f.read()
    f.close()

    p = re.compile("(?P<key>[a-zA-Z_]{1,}):[ \s]{0,}(?P<value>[0-9]{1,})[ \s\w]{0,}\n")
    for m in p.finditer(data):
        _m = m.groupdict()
        mem[_m["key"].lower()] = long(_m["value"]) * 1024.0
    mem['memused'] = mem['memtotal'] - mem['memfree'] - mem['buffers'] - mem['cached']
    return mem

def processor_stat():
    processor = []
    processorinfo = {}
    f = open("/proc/cpuinfo")
    data = f.read()
    f.close()
    #p = re.compile("([ \sa-zA-Z_]{1,}):([ \s\w.\(\)\@\[\]]{1,})\n")
    p = re.compile("(?P<key>[ \sa-zA-Z_]{1,}):(?P<value>.*)\n")
    for m in p.finditer(data):
        _m = m.groupdict()
        if _m["key"].strip() == "processor" and _m["value"].strip() != '0':
            processor.append(processorinfo)
            processorinfo = {}
        processorinfo[_m["key"].strip()] = _m["value"].strip()
    processor.append(processorinfo)
    return processor

def load_stat():
    loadavg = {}
    f = open("/proc/loadavg")
    con = f.read().split()
    f.close()
    loadavg['lavg_1']=con[0]
    loadavg['lavg_5']=con[1]
    loadavg['lavg_15']=con[2]
    loadavg['nr']=con[3]
    loadavg['last_pid']=con[4]
    return loadavg

def uptime_stat():
    uptime = {}
    f = open("/proc/uptime")
    con = f.read().split()
    f.close()
    all_sec = float(con[0])
    MINUTE,HOUR,DAY = 60,3600,86400
    uptime['day'] = int(all_sec / DAY )
    uptime['hour'] = int((all_sec % DAY) / HOUR)
    uptime['minute'] = int((all_sec % HOUR) / MINUTE)
    uptime['second'] = int(all_sec % MINUTE)
    uptime['free_rate'] = float(con[1]) / float(con[0])
    return uptime

def net_stat():
    net = []
    f = open("/proc/net/dev")
    lines = f.readlines()
    f.close()
    p = re.compile("[ ]*(?P<interface>[\w]+):[ ]*(?P<receivebytes>[\d]+)[ ]*" +
                   "(?P<receivepackets>[\d]+)[ ]*(?P<receiveerrs>[\d]+)[ ]*" +
                   "(?P<receivedrop>[\d]+)[ ]*(?P<receivefifo>[\d]+)[ ]*" +
                   "(?P<receiveframes>[\d]+)[ ]*(?P<receivecompressed>[\d]+)[ ]*" +
                   "(?P<receivemulticast>[\d]+)[ ]*(?P<transmitbytes>[\d]+)[ ]*" +
                   "(?P<transmitpackets>[\d]+)[ ]*(?P<transmiterrs>[\d]+)[ ]*" +
                   "(?P<transmitdrop>[\d]+)[ ]*(?P<transmitfifo>[\d]+)[ ]*" +
                   "(?P<transmitframes>[\d]+)[ ]*(?P<transmitcompressed>[\d]+)[ ]*" +
                   "(?P<transmitmulticast>[\d]+)[ ]*\n")

    for data in lines:
        for m in p.finditer(data):
            _m = m.groupdict()
            net.append(_m)

    return net

def disk_stat():
    hd = {}
    disk = os.statvfs("/")
    hd['available'] = disk.f_bsize * disk.f_bavail
    hd['capacity'] = disk.f_bsize * disk.f_blocks
    hd['used'] = disk.f_bsize * disk.f_bfree
    return hd

def date_stat():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S' )

def get_old_version():
    data = {}
    cmd = 'cat /etc/version'
    if os.path.isfile('/etc/version'):
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            for line in stdout.split("\n"):
                tmp_list = line.split("=")
                if len(tmp_list) >= 2:
                    data[tmp_list[0]] = tmp_list[1].strip()
    return data

def get_new_version():
    data = {}
    update_tool_version = '0.1'
    issue = ''
    kernel = ''
    cpu = ''
    base_board = ''
    video_adaptor = ''

    cmd = 'cat /etc/issue | head -1'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        issue += stdout.strip()
    cmd = 'uname -spir'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        kernel += stdout.strip()
    cmd = "cat /proc/cpuinfo |grep name| head -1 |awk -F \":\" \'{ print $2 }\'"
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        cpu += stdout.strip()
    cmd = "dmidecode -t 2|grep Product|awk -F \":\" \'{ print $2 }\'"
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        base_board += stdout.strip()
    cmd = "lspci |grep -i VGA|awk -F \":\" \'{ print $3 }\' | head -n 1"
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        video_adaptor += stdout.strip()

    data['update_tool_version'] = update_tool_version
    data['issue'] = issue
    data['kernel'] = kernel
    data['cpu'] = cpu
    data['base_board'] = base_board
    data['video_adaptor'] = video_adaptor

    return data

def get_mamttools_version():
    data = {}
    data['restful-server'] = ''
    data['web-frontend'] = ''

    restful_info = get_rpminfo('restful-server')
    webfrontend_info = get_rpminfo('web-frontend')

    if restful_info:
        version = restful_info['version']
        build_version = restful_info['release']
        data['restful-server'] = version+'-'+build_version
    if webfrontend_info:
        version = webfrontend_info['version']
        build_version = webfrontend_info['release']
        data['web-frontend'] = version+'-'+build_version

    return data

class SystemInfo:
    def GET(self):
        info = {}
        memory = memory_stat()
        info["memory"] = memory

        # cpu = processor_stat()
        # info["processor"] = cpu

        loadavg = load_stat()
        info["workload"] = loadavg

        uptime = uptime_stat()
        info["uptime"] = uptime

        net = net_stat()
        info["net"] = net

        disk = disk_stat()
        info["disk"] = disk

        date = date_stat()
        info["date"] = date

        # add new ...
        old_version = get_old_version()
        if not old_version:                 # if no '/etc/version', use default null value
            old_version['issue'] = ''
            old_version['kernel'] = ''
            old_version['cpu'] = ''
            old_version['base_board'] = ''
            old_version['video_adaptor'] = ''
            old_version['system_version'] = ''
            old_version['build_time'] = ''

        new_version = get_new_version()

        info['update_tool_version'] = new_version['update_tool_version']
        info['issue'] = {}
        info['kernel'] = {}
        info['cpu'] = {}
        info['base_board'] = {}
        info['video_adaptor'] = {}

        info['issue']['name'] = new_version['issue']
        if new_version['issue'] != old_version['issue']:
            info['issue']['warning'] = old_version['issue']

        info['kernel']['name'] = new_version['kernel']
        if new_version['kernel'] != old_version['kernel']:
            info['kernel']['warning'] = old_version['kernel']

        info['cpu']['name'] = new_version['cpu']
        if new_version['cpu'] != old_version['cpu']:
            info['cpu']['warning'] = old_version['cpu']

        info['base_board']['name'] = new_version['base_board']
        if new_version['base_board'] != old_version['base_board']:
            info['base_board']['warning'] = old_version['base_board']

        info['video_adaptor']['name'] = new_version['video_adaptor']
        if new_version['video_adaptor'] != old_version['video_adaptor']:
            info['video_adaptor']['warning'] = old_version['video_adaptor']

        # get managment tools version info
        mgmt_version = get_mamttools_version()
        info['restful-server'] = mgmt_version['restful-server']
        info['web-frontend'] = mgmt_version['web-frontend']
        info['sys_version'] = old_version['system_version'] if 'system_version' in old_version.keys() else ''
        info['build_time'] = old_version['build_time'] if 'build_time' in old_version.keys() else ''

        return json.dumps(info)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

class SystemInfoExt:
    def GET(self, arg):
        info = None
        if arg == "mem":
            info = memory_stat()
        if arg == "processor":
            info = processor_stat()
        if arg == "workload":
            info = load_stat()
        if arg == "uptime":
            info = uptime_stat()
        if arg == "net":
            info = net_stat()
        if arg == "disk":
            info = disk_stat()
        if arg == "date":
            info = date_stat()
        return json.dumps(info);

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

app = web.application(urls, locals())
