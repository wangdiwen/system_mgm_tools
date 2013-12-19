#!/usr/bin/python2.7

import web
import json
import re, os, string
from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Softinfo',
    "/(.*)", 'SoftinfoExt'
)

def get_installed():
    meta = get_meta_data()
    rpm_installed = meta['software']['installed']
    return rpm_installed

def get_softinfo(rpm_name):
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

class Softinfo:
    def GET(self):
        pass
    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

class SoftinfoExt:
    def GET(self, arg):
        if not arg in get_installed():
            msg = '580 has no such rpm package ' + arg
            raise RestfulError(msg)
        data = get_softinfo(arg)
        return json.dumps(data)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

app = web.application(urls, locals())
