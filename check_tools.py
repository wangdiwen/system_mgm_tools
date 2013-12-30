#!/usr/bin/python

import os
import sys
import re, json, types, shutil, time
from subprocess import Popen, PIPE

###############################################################################
###############################################################################
def shell_cmd(cmd, wait = True, option = 0):
    # Note:
    # wait-> status=0; no wait-> status=None
    # option: 0, False > (status, stdout, stderr),
    #         1, True > status, 2 > stdout, 3 > stderr
    stdout = ''
    status = 0
    stderr = ''
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    if wait:
        process.wait()
    status = process.returncode
    stdout, stderr = process.communicate()
    if option in [0, False]:
        return (status, stdout.strip(), stderr.strip())
    elif option in [1, True]:
        return status
    elif option in [2]:
        return stdout.strip()
    elif option in [3]:
        return stderr.strip()
    return (status, stdout.strip(), stderr.strip())

def get_teminal_input(tips = 'Pls input', options = ['y', 'n', 'yes', 'no']):
    data = ''
    while True:
        data = raw_input(tips + ': ')
        if data in options:
            break
    return data

class Color:
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4

def log(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.GREEN, str)
def error(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.RED, str)
def warning(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.YELLOW, str)
def quit(code = 0, msg = ''):
    if msg:
        print msg
    sys.exit(code)
###############################################################################

###############################################################################
print ''
print '\t################### Checking System Software Tools ###################\n'
###############################################################################
########### Here, Define your functions and processes #########################

sys_tool_list = {
    'parted': 'parted.x86_64',
    'mdadm': 'mdadm.x86_64',
    'mkfs.xfs': 'xfsprogs kmod-xfs',
    'ntpdate': 'ntpdate.x86_64',
    'lspci': 'pciutils.x86_64 pciutils-libs.x86_64',
    'traceroute': 'traceroute',
    'dmidecode': 'dmidecode.x86_64',
    'ethtool': 'ethtool',
}

failed_tool = []

for tool in sys_tool_list.keys():
    print 'Checking system tool ' + tool + ' ...'
    ret = shell_cmd('which ' + tool, True, 1)
    if ret != 0:  # not installed
        log('not installed')
        time.sleep(1)
        print 'try to install ' + tool + ' ...'
        ret_ins = shell_cmd('echo -e "y\n" | yum install ' + sys_tool_list[tool])
        if ret_ins == 0:
            log('success')
        else:
            warning('install failed')
            failed_tool.append(tool)

log('=========== Install failed tools =============')
if failed_tool:
    for item in failed_tool:
        warning('failed ==> ' + item)
