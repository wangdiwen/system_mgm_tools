#!/usr/bin/python2.7

import web
import json
import re
import os, string
from common import invoke_shell
from common.restfulclient import RestfulError

urls = (
  "", "Disk",
)

def disk_device():
    device = []
    cmd = 'fdisk -l'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        for line in stdout.split("\n"):
            if re.compile("^Disk /dev/").match(line):
                tmp_list = line.split(":")
                dev = tmp_list[0].split()[1]
                if not re.compile(".*md.*").match(dev):
                    device.append(dev)
    return device

def disk_info():
    data = []
    dev_list = disk_device()
    for dev in dev_list:
        tmp_dict = {}

        cmd = 'smartctl -Hi -d ata ' + dev
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            for line in stdout.split("\n"):
                tmp_list = line.split(": ")
                length = len(tmp_list)
                if length >= 2:
                    key = tmp_list[0].lower()
                    key = key.replace(' is', '')
                    if re.compile(".*overall-health.*").match(key):
                        key = 'overall health'
                    tmp_dict[key] = string.join(tmp_list[1:length]).strip()
        if tmp_dict:
            tmp_dict['device name'] = dev
            data.append(tmp_dict)
    return data

class Disk:
    def GET(self):
        data = disk_info()
        return json.dumps(data)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

app = web.application(urls, locals())
