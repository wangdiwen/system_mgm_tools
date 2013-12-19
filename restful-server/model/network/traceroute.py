#!/usr/bin/python2.7

import web
import json
import subprocess, time, signal
import re
import threading

from common import invoke_shell, check_ip
from common.restfulclient import RestfulError

urls = (
    '', 'Traceroute',
    '/(.*)', 'TracerouteExt'
)

class Trace_thread(threading.Thread):
    def __init__(self, thread_name, cmd):
        super(Trace_thread, self).__init__(name=thread_name)
        self._stop = threading.Event()
        self.trace_cmd = cmd
        return

    def run(self):
        # init the Traceroute.trace_* vars
        Traceroute.trace_process = None
        Traceroute.trace_status = True
        Traceroute.trace_container = []
        Traceroute.trace_cur_index = -1
        Traceroute.trace_index = 0

        # start child process
        Traceroute.trace_process = subprocess.Popen(self.trace_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while Traceroute.trace_process.poll() == None:
            line = Traceroute.trace_process.stdout.readline()
            # print 'here: ' + line.rstrip()
            if line:
                Traceroute.trace_container.append(line)
                Traceroute.trace_cur_index += 1

        final_data = Traceroute.trace_process.stdout.read()
        return_code = Traceroute.trace_process.returncode
        # print final_data
        Traceroute.trace_container.append(final_data)
        Traceroute.trace_cur_index += 1

        Traceroute.trace_container.append('over')
        Traceroute.trace_cur_index += 1
        Traceroute.trace_status = False
        return

    def stop(self):
        # ret = Traceroute.trace_process.terminate()  # stop process
        ret = Traceroute.trace_process.send_signal(signal.SIGINT)
        Traceroute.trace_status = False
        self._stop.set()
        return

def get_interface():
    data = []
    cmd = 'ls /etc/sysconfig/network-scripts | grep \"^ifcfg-eth[0-9]$\"'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        for inter in stdout.split("\n"):
            tmp_list = inter.split("-")
            if len(tmp_list) > 1:
                data.append(tmp_list[1])
    return data

def start_traceroute(info):
    # example: traceroute -I/-T/-U -i eth0 -p 33434 -w 5.0 -q 3 -s 10.4.89.102 -z 0.05 61.135.169.125 56
    field = info.keys()
    traceroute_to = info['traceroute-to'] if 'traceroute-to' in field else ''
    packet_size = info['packet-size'] if 'packet-size' in field else ''
    packet_count = '3'              # traceroute send packet count every
    packet_interval = '0.05'        # pre setting
    timeout = info['timeout'] if 'timeout' in field else ''
    protocol = info['protocol'] if 'protocol' in field else ''
    port = info['port'] if 'port' in field else ''
    src_addr = info['src-address'] if 'src-address' in field else ''
    interface = info['interface'] if 'interface' in field else ''

    # check the input data valid or not
    if not traceroute_to or not protocol:
        msg = '580 Error: less argument [traceroute-to] and [protocol] must be give'
        raise RestfulError(msg)
    if not check_ip(traceroute_to):
        msg = '580 Error: traceroute-to ipaddr wrong'
        raise RestfulError(msg)
    if not protocol in ['icmp', 'tcp', 'udp']:
        msg = '580 Error: [protocol] wrong, use icmp/tcp/udp'
        raise RestfulError(msg)

    if interface:
        interface_list = get_interface()
        # print interface_list
        if not interface in interface_list:
            msg = '580 Error: interface wrong [' + interface + '], '
            for inter in interface_list:
                msg += inter + ' '
            msg += 'just can be use'
            raise RestfulError(msg)
            return

    protocol_map = {}
    protocol_map['icmp'] = '-I'
    protocol_map['tcp'] = '-T'
    protocol_map['udp'] = '-U'

    cmd = 'traceroute ' + protocol_map[protocol]
    if interface:
        cmd += ' -i ' + interface
    if port:
        cmd += ' -p ' + port
    if timeout:
        cmd += ' -w ' + timeout
    if packet_count:
        cmd += ' -q ' + packet_count
    if src_addr:
        cmd += ' -s ' + src_addr
    if packet_interval:
        cmd += ' -z ' + packet_interval
    if traceroute_to:
        cmd += ' ' + traceroute_to
    if packet_size:
        cmd += ' ' + packet_size
    # print cmd       # test cmd value

    # check progress
    if Traceroute.trace_status:
        return False
    # create single traceroute thread
    Traceroute.trace_thread = Trace_thread('traceroute-thread', cmd)
    Traceroute.trace_thread.start()

    return True

def get_traceroute():
    data = []
    if Traceroute.trace_container:
        if Traceroute.trace_index <= Traceroute.trace_cur_index:
            content = Traceroute.trace_container[Traceroute.trace_index]
            data.append(content)
            Traceroute.trace_index += 1

            if content == 'over':
                Traceroute.trace_container = []
                Traceroute.trace_cur_index = -1
                Traceroute.trace_index = 0
    return data

def get_multi_traceroute(sequence):
    last_seq = int(sequence)
    data = {}
    if Traceroute.trace_container:
        if last_seq <= Traceroute.trace_cur_index:
            tmp_ret = Traceroute.trace_container[last_seq:Traceroute.trace_cur_index]
            if tmp_ret:
                data['sequence'] = Traceroute.trace_cur_index
                data['result'] = ''.join(tmp_ret)
            else:
                if not Traceroute.trace_status:  # process quit, revise timeout bug
                    data['sequence'] = -1
                    data['result'] = []
                    # clear the cache zone
                    Traceroute.trace_container = []
                    Traceroute.trace_cur_index = -1
                    Traceroute.trace_index = 0
    return data

def stop_traceroute():
    if not Traceroute.trace_status:
        return
    Traceroute.trace_thread.stop()
    return

####################################################################
class Traceroute:
    trace_thread = None   # child thread

    trace_process = None  # thread process handle
    trace_status = False  # False: not run, True: running
    trace_container = []  # cache zone
    trace_cur_index = -1  # current cache zone pointer
    trace_index = 0       # record corrent get pointer

    def GET(self):
        data = get_traceroute()
        if data:
            return data[0]
        return ''

    def PUT(self):
        input = json.loads(web.data())
        ret = start_traceroute(input)
        return

    def POST(self):
        pass
    def DELETE(self):
        ret = stop_traceroute()
        return

class TracerouteExt:
    def GET(self, arg):
        if not re.compile("^[0-9]+$").match(arg):
            msg = '580 Error: sequence must be integer type'
            raise RestfulError(msg)
        data = get_multi_traceroute(arg)
        return json.dumps(data)

    def PUT(self, arg):
        pass
    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
