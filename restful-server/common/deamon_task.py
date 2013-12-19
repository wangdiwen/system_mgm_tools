import time, threading
from __init__ import invoke_shell

from global_helper import get_meta_data  # public helper functions

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
