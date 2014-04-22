import time, threading
from __init__ import invoke_shell

from global_helper import get_meta_data, get_ntp_server  # public helper functions

def get_log_disk_ratio():
    meta = get_meta_data()
    if 'log-disk-ratio' in meta['restful'].keys():
        return meta['restful']['log-disk-ratio']
    else:
        return 90

class LogRatio():
    log_ratio = 80
    def __init__(self):
        LogRatio.log_ratio = get_log_disk_ratio()

    def set_ratio(self, ratio):
        LogRatio.log_ratio = ratio
        return

def log_disk_ratio():
    cmd = "df -h | grep \"/opt/program/log\" | head -n 1 | awk \'{ print $5 }\' | sed \"s/%//g\""
    if not cmd:
        return 0
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        disk_ratio = stdout.strip()
        if disk_ratio.isdigit():
            ratio = int(disk_ratio)
            return ratio
    return 0

def clear_log_disk():
    cur_ratio = log_disk_ratio()
    if cur_ratio >= LogRatio.log_ratio:
        # get all file in /opt/program/log
        all_log_file = []
        cmd = 'find /opt/program/log/ -type f'
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            for line in stdout.split("\n"):
                all_log_file.append(line)

        for log_file in all_log_file:
            cmd = '/usr/sbin/lsof ' + log_file
            status, stdout, stderr = invoke_shell(cmd)
            if status != 0 or not stdout:
                rm_cmd = '/usr/bin/shred -u -z ' + log_file
                sta, out, err = invoke_shell(rm_cmd)
    return True

def ntp_sync():
    ntp_info = get_ntp_server()
    if ntp_info:
        status = ntp_info['status']
        server_list = ntp_info['ntp']
        if status == 'on':
            # check network, has connect to internet
            # '1.cn.pool.ntp.org' is china ntp server center
            status, stdout, stderr = invoke_shell('ping -c 1 -i 0.5 -w 1 -I eth0 1.cn.pool.ntp.org')
            # print stdout
            if status == 0 and len(server_list) > 0:
                for addr in server_list:
                    print 'sync time from : ' + addr + ' ...'
                    sta, out, err = invoke_shell('ntpdate ' + addr)
                    if sta == 0:
                        print 'sync time from ' + addr + ' success'
                        # put the system time to CMOS
                        print 'record the system to CMOS ...'
                        sta, out, err = invoke_shell('clock -w')
                        if sta == 0:
                            print 'record the sys to CMOS, success'
                        break
                    else:
                        continue
    return True

class LogClear(threading.Thread):
    def __init__(self, lock, thread_name):
        super(LogClear, self).__init__(name=thread_name)
        self.lock = lock

    def run(self):
        logratio_obj = LogRatio()
        while True:
            # self.lock.acquire()         # add lock
            ret = clear_log_disk()        # clear handle
            # self.lock.release()         # release lock
            time.sleep(15)

class NtpSync(threading.Thread):
    """docstring for NtpSync"""
    def __init__(self, thread_name):
        super(NtpSync, self).__init__(name=thread_name)

    def run(self):
        # sync ntp server, just sync once when server run
        ntp_sync()

