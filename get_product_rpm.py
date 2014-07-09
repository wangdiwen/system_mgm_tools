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
        stdout, stderr = process.communicate()
    status = process.returncode
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

def get_input(tips = 'Pls input'):
    data = ''
    while True:
        data = raw_input(tips + ': ')
        if data.strip():
            break
    return data.strip()

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
        error('get_product_info: invalid product name, quit .')
        return False

    repo_list = [
        'centos-base',
        'vmediax',
        'zeroc-ice-i386',
        'zeroc-ice-x86_64',
    ]
    pkg_lines = []

    sta, out, err = shell_cmd('echo -e "N\n" | yum install ' + pro_name)
    print out
    if out:
        lines = out.split("\n")
        is_ok = False
        is_installed = False

        for line in lines:
            if re.compile(".*already installed.*").match(line):
                is_installed = True
                break

            for repo in repo_list:
                if re.compile(".*" + repo + ".*").match(line):
                    is_ok = True
            if is_ok:
                pkg_lines.append(line.strip())
                is_ok = False
        if is_installed:
            warning("software " + pro_name + ' has already installed')
            warning('You can find a machine not installed ' + pro_name)
            return False
    if len(pkg_lines) > 1:
        return pkg_lines
    return False

def get_rpm_ver(pro_name):
    cmd = 'yum info ' + pro_name + ' | grep Version | awk \'{print $3}\''
    out = shell_cmd(cmd, True, 2)
    if out:
        return out.strip()
    return ''


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
    print out
    print err
    if sta == 0:
        # check has many software ?
        data = []
        rule = re.compile('^' + rpm_name)
        lines = out.split("\n")
        for line in lines:
            if rule.match(line):
                data.append(line)
        print lines
        print data
        if len(data) > 1:
            warning('check too many software, which do your choice ?')
            i = 0
            for item in data:
                i = i + 1
                warning("%d : %s" % (i, item))
        else:
            print 'find valid software !'
            return True
    return False

def download_rpm(rpm_list, path):
    if not os.path.isdir(path):
        os.makedirs(path)

    ok_count = 0

    sta = shell_cmd('which yumdownloader', True, 1)
    if sta != 0:
        # install tools
        sta = shell_cmd('yum -y install yum-utils', True, 1)
        if sta != 0:
            quit(1, 'install yumdownloader tool failed')

    for item in rpm_list:
        cmd = 'yumdownloader ' + item + ' --destdir=' + path
        sta = shell_cmd(cmd, True, 1)
        if sta == 0:
            tips('download ' + item + "\t\t OK")
            ok_count = ok_count + 1
        else:
            warning('download ' + item + "\t\t Failed")

    return ok_count


# ==============================================================================

product_name = ''                            # define your product rpm name
product_name = get_input('Pls input your product software name')
tips('Your product software is : ' + product_name)

has_pro = check_has_rpm(product_name)
if not has_pro:
    error('not find valid product ' + product_name)
    quit(1, 'bye')

pro_lines = get_product_info(product_name)
if pro_lines:
    print 'Total packages = %d' % len(pro_lines)

    print ''
    rpm_list = get_rpm_name_list(pro_lines)
    print 'Check final packages count = %d' % len(rpm_list)

    if len(pro_lines) == len(rpm_list):
        tips('====== > Check success !')
        tips('Check valid dependency rpm pkgs ===>')
        print rpm_list
    else:
        error('Total packages cannot equal final packages')
        quit(1, 'quit ...')

    # get the product version info
    ver = get_rpm_ver(product_name)
    if not ver:
        error('Get ' + product_name + ' version info, failed')
        quit(1, 'check something wrong ... quit ...')

    # download the rpm packages
    down_path = './repo'
    iso_name = product_name + '-' + ver + '.iso'

    count = download_rpm(rpm_list, down_path)
    tips("")
    tips('=== total to download        : %d' % len(pro_lines))
    tips('=== success download packages: %d' % count)
    tips('=== download to rpm repo path: ' + down_path)
    tips('')

    tips('=== Now, Building ISO file ...')
    tips('=== ISO Name : ' + iso_name)


    build_script = './build_iso_repo.sh'
    if os.path.isfile(build_script):
        # check build shell script ?
        err = shell_cmd('bash -n ' + build_script, True, 3)
        if err:
            error(err)
            quit(1, 'script error !')
        sta, out, err = shell_cmd(build_script + ' -p ' + down_path + ' -n ' + iso_name)
        print out
        if sta == 0:
            tips("=== Building ISO success")
        else:
            error('=== Building ISO failed')
    else:
        warning('cannot find build iso script ' + build_script)
    tips('clean tmp files ...')
    if os.path.isdir(down_path):
        sta = shell_cmd('rm -rf ' + down_path, True, 1)
    tips('=== over ===')
else:
    warning("check something warning ...")
