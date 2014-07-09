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
    msg = '\033[0;3%dm%s\033[0m' % (Color.GREEN, '\t'+str)
    print >>sys.stdout, msg
def tips(str = ''):
    msg = '\033[0;3%dm%s\033[0m' % (Color.GREEN, '\t'+str)
    print >>sys.stdout, msg
def error(str = ''):
    msg = '\033[0;3%dm%s\033[0m' % (Color.RED, '\t'+str)
    print >>sys.stdout, msg
def warning(str = ''):
    msg = '\033[0;3%dm%s\033[0m' % (Color.YELLOW, '\t'+str)
    print >>sys.stdout, msg
def quit(code = 0, msg = ''):
    if code == 0 and msg:
        print >>sys.stdout, msg
    elif msg:
        msg = '\033[0;3%dm%s\033[0m' % (Color.RED, msg)
        print >>sys.stdout, msg
    sys.exit(code)
###############################################################################

###############################################################################
print ''
print '\t################### Auto Update VmediaX Repo ###################\n'
###############################################################################
########### Here, Define your functions and processes #########################

def exec_repo_up():
    sh_file = './create-repo.sh'
    if os.path.isfile(sh_file):
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sta = shell_cmd('bash ' + sh_file + ' >/dev/null 2>&1', True, 1)
        if sta == 0:
            tips('[' + cur_time + ']: Update repo success')
            return True
        else:
            warning('[' + cur_time + ']: Update repo failed')
    return False

def detect_file_change():
    is_exec = False
    sta, out, err = shell_cmd('ls -l /var/www/html/vmediax | grep -v repodata | awk \'{print $6,$7,$8,$9}\'')
    if sta == 0 and out:
        line_list = out.split("\n")
        for line in line_list:
            tmp_list = line.split(" ")
            if len(tmp_list) > 3:
                # print tmp_list
                tmp_file = tmp_list[3]
                tmp_time = tmp_list[0] + '-' + tmp_list[1] + '-' + tmp_list[2]
                if tmp_file in g_data.keys():
                    if tmp_time != g_data[tmp_file]:
                        is_exec = True
                        break
                else:
                    g_data[tmp_file] = tmp_time
                    is_exec = True
                    break
    return is_exec

def init_data():
    sta, out, err = shell_cmd('ls -l /var/www/html/vmediax | grep -v repodata | awk \'{print $6,$7,$8,$9}\'')
    if sta == 0 and out:
        line_list = out.split("\n")
        for line in line_list:
            tmp_list = line.split(" ")
            # print tmp_list
            if len(tmp_list) > 3:
                tmp_file = tmp_list[3]
                tmp_time = tmp_list[0] + '-' + tmp_list[1] + '-' + tmp_list[2]
                g_data[tmp_file] = tmp_time
    return True

def main():
    init_data()
    while 1:
        # print 'detect ...'
        is_exec = detect_file_change()
        if is_exec:
            # print 'Detect need to Update ...'
            time.sleep(30)
            ret = exec_repo_up()
            if not ret:
                quit(1, 'Update Script Something Wrong, quit.')
        time.sleep(5)

# ==============================================================================
g_data = {}                 # global var, like: {'file name': 'time stamp', ...}
main()
