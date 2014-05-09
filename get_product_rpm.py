#!/usr/bin/python

import os
import sys
import re, json, types, shutil
import time
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


def get_teminal_input(tips = 'Pls input', options = ['y', 'n', 'yes', 'no'], auto_answer = 'y'):
    if auto_answer in options:
        return auto_answer
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
    print '\033[0;3%dm%s\033[0m' % (Color.GREEN, '\t'+str)
def tips(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.GREEN, '\t'+str)
def error(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.RED, '\t'+str)
def warning(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.YELLOW, '\t'+str)
def quit(code = 0, msg = ''):
    if code == 0 and msg:
        print msg
    elif msg:
        print '\033[0;3%dm%s\033[0m' % (Color.RED, msg)
    sys.exit(code)
###############################################################################

###############################################################################
print ''
print '\t################### Auto Building Product rpm pkg ###################\n'
###############################################################################
########### Here, Define your functions and processes #########################

def get_product_info(pro_name = ''):
    if not pro_name:
        return False

    repo_list = [
        'centos-base',
        'vmediax',
        'zeroc-ice-i386',
        'zeroc-ice-x86_64',
    ]
    pkg_lines = []

    sta, out, err = shell_cmd('echo -e "N\n" | yum install ' + pro_name)
    if out:
        lines = out.split("\n")
        is_ok = False

        for line in lines:
            for repo in repo_list:
                if re.compile(".*" + repo + ".*").match(line):
                    is_ok = True
            if is_ok:
                pkg_lines.append(line.strip())
                is_ok = False
    if len(pkg_lines) > 1:
        return pkg_lines
    return False


def get_clean_set(list_val):
    data = []
    for item in list_val:
        if item:
            data.append(item)
    return data

def get_rpm_name_list(pro_lines):
    data = []                   # return rpm name
    if len(pro_lines) > 1:
        for line in pro_lines:
            tmp_list = line.strip().split(" ")
            clean_list = get_clean_set(tmp_list)

            # print clean_list
            data.append(clean_list[0])
    return data

def check_has_rpm(rpm_name):
    sta, out, err = shell_cmd('yum search ' + rpm_name)
    if sta == 0:
        return True
    return False

def download_rpm(rpm_list, path):
    if not os.path.isdir(path):
        os.makedirs(path)

    ok_count = 0

    sta = shell_cmd('which yumdownloader', True, 1)
    if sta != 0:
        # install tools
        sta = shell_cmd('yum -y install yumdownloader', True, 1)
        if sta != 0:
            quit(1, 'install yumdownloader tool failed')

    for item in rpm_list:
        cmd = 'yumdownloader ' + item + ' --destdir=' + path
        sta = shell_cmd(cmd, True, 1)
        if sta == 0:
            tips('download ' + item + ' ok')
            ok_count = ok_count + 1
        else:
            warning('download ' + item + ' failed')

    return ok_count


# ==============================================================================

product_name = 'mrs-4000-os'                            # define your product rpm name

has_pro = check_has_rpm(product_name)
if not has_pro:
    error('not find this product ' + product_name)
    quit(1, 'bye')

pro_lines = get_product_info(product_name)
if pro_lines:
    # for line in pro_lines:
        # print line
    print 'Total packages = %d' % len(pro_lines)

    print ''
    rpm_list = get_rpm_name_list(pro_lines)
    print 'Check final packages count = %d' % len(rpm_list)

    if len(pro_lines) == len(rpm_list):
        tips('====== > Check success !')
        print rpm_list
    else:
        error('Total packages cannot equal final packages')
        quit(1, 'quit ...')

    # download the rpm packages
    down_path = './repo'
    count = download_rpm(rpm_list, down_path)
    tips("")
    tips('=== total to download        : %d' % len(pro_lines))
    tips('=== success download packages: %d' % count)
    tips('=== download to rpm repo path: ' + down_path)
    tips('')

    tips('=== Now, Building ISO file ...')
    build_script = './build_iso_repo.sh'
    if os.path.isfile(build_script):
        sta, out, err = shell_cmd(build_script + ' -p ' + down_path)
        print out
        if sta == 0:
            tips("=== Building ISO success")
        else:
            warning('=== Building ISO failed')
    else:
        warning('cannot find build iso script ' + build_script)
    tips('over')
