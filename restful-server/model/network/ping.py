#!/usr/bin/python2.7

# from web.background import background, backgrounder
import web

import json
import subprocess, time, signal
import re, os
import threading

from common import invoke_shell, check_ip
from common.restfulclient import RestfulError

urls = (
    '', 'Ping',
    '/(.*)', 'PingExt'
)

class Ping_thread(threading.Thread):
    def __init__(self, thread_name, ip_addr, count):
        super(Ping_thread, self).__init__(name=thread_name)
        self._stop = threading.Event()
        self.ip_addr = ip_addr
        self.count = count
        return
    def run(self):
        Ping.ping_process = None
        Ping.ping_status = True
        Ping.ping_container = []
        Ping.ping_cur_index = -1
        Ping.ping_index = 0

        cmd = 'ping -c ' + self.count + ' ' + self.ip_addr
        Ping.ping_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while Ping.ping_process.poll() == None:  # the last is 0
            line = Ping.ping_process.stdout.readline()
            # print line.rstrip("\n")
            Ping.ping_container.append(line)
            Ping.ping_cur_index += 1

        final_data = Ping.ping_process.stdout.read()   # read final data
        return_code = Ping.ping_process.returncode
        # print final_data
        Ping.ping_container.append(final_data)
        Ping.ping_cur_index += 1

        Ping.ping_container.append('over')            # over flag
        Ping.ping_cur_index += 1
        Ping.ping_status = False
        return return_code
    def stop(self):
        ret = Ping.ping_process.send_signal(signal.SIGINT)
        Ping.ping_status = False
        self._stop.set()
        return

def start_ping(info):
    ip_addr = info['ip'] if 'ip' in info.keys() else ''
    count = info['count'] if 'count' in info.keys() else Ping.ping_max

    # check ip addr invalid
    ip_invalid = check_ip(ip_addr)
    if not ip_invalid:
        msg = '580 Error: invalid ip addr [' + ip_addr + ']'
        raise RestfulError(msg)
    if not count.isdigit():
        msg = '580 Error: invalid count, not a integer string'
        raise RestfulError(msg)

    if Ping.ping_status:
        return False

    # create ping single thread
    Ping.ping_thread = Ping_thread('ping-thread', ip_addr, count)
    Ping.ping_thread.start()

    return True

def stop_ping():
    if not Ping.ping_status:
        return
    Ping.ping_thread.stop()
    return

def get_ping_result():
    data = []
    if Ping.ping_container:
        if Ping.ping_index <= Ping.ping_cur_index:
            content = Ping.ping_container[Ping.ping_index]
            data.append(content)
            Ping.ping_index += 1
            if content == 'over':
                Ping.ping_container = []
                Ping.ping_cur_index = -1
                Ping.ping_index = 0
    return data

def get_multi_result(sequence):
    last_seq = int(sequence)
    data = {}

    if Ping.ping_container:
        if last_seq <= Ping.ping_cur_index:
            tmp_ret = Ping.ping_container[last_seq:Ping.ping_cur_index]
            if tmp_ret:
                data['result'] = ''.join(tmp_ret)
                data['sequence'] = Ping.ping_cur_index
            else:
                data['result'] = []
                data['sequence'] = -1
                # clear the cache zone
                Ping.ping_container = []
                Ping.ping_cur_index = -1
                Ping.ping_index = 0
    return data

####################################################################
class Ping:
    ping_thread = None     # child thread

    ping_process = None    # thread handle
    ping_status = False    # False: not running, True: running
    ping_container = []    # chace zone
    ping_max = '120'       # about 2 mins
    ping_cur_index = -1    # current cache zone pointer
    ping_index = 0         # record corrent get pointer

    def GET(self):
        data = get_ping_result()
        if data:
            return data[0]
        return ''

    def PUT(self):
        input = json.loads(web.data())
        ret = start_ping(input)
        return

    def POST(self):
        pass
    def DELETE(self):
        ret = stop_ping()
        return

class PingExt:
    def GET(self, arg):
        if not re.compile("^[0-9]+$").match(arg):
            msg = '580 Error: sequence must be integer type'
            raise RestfulError(msg)
        data = get_multi_result(arg)
        return json.dumps(data)

    def PUT(self, arg):
        pass
    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
