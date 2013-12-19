import web
import os, re, json
import signal
from common import invoke_shell
from common.restfulclient import RestfulError

urls = (
  "(.*)", "SystemProcess",
)

def new_get_process_info(pid = ''):
    data = []
    shell = 'ps -eo user,pid,size,vsize,nice,rtprio,priority,trs,rss,time,stat,cmd'
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        filter_rule = re.compile("(?P<user>[\w]+)[ ]*(?P<pid>[\d]+)[ ]*" + \
                                "(?P<size>[\d.]+)[ ]*(?P<vsize>[\d.]+)[ ]*" + \
                                "(?P<nice>[\d\-]+)[ ]*(?P<rtprio>[\d\-]+)[ ]*(?P<priority>[\d\-]+)[ ]*" + \
                                "(?P<trs>[\d]+)[ ]*(?P<rss>[\d]+)[ ]*" + \
                                "(?P<time>[\d:]+)[ ]*" + \
                                "(?P<stat>[\w\<\+]+)[ ]*(?P<command>.*)"
                                );
        for line in stdout.split("\n"):
            exp_ret = filter_rule.match(line)
            if exp_ret:
                exp_dict = exp_ret.groupdict()
                if pid and exp_dict['pid'] == pid:
                    stat, out, err = invoke_shell("chrt -p " + pid +" | head -n 1 | awk -F\": \" \'{print $2}\'")
                    if stat == 0 and out:
                        exp_dict['priority_type'] = out
                    tmp_data = []
                    tmp_data.append(exp_dict)
                    return tmp_data
                else:
                    data.append(exp_dict)
    return data

def new_modify_process_nice(input_data):
    result = False
    field = input_data.keys()
    pid = input_data['pid'] if 'pid' in field else ''
    priority = input_data['priority'] if 'priority' in field else ''
    priority_type = input_data['priority_type'] if 'priority_type' in field else ''

    if pid and priority and priority_type:
        priority_type_map = {'SCHED_FIFO': '-f',
                            'SCHED_RR': '-r',
                            'SCHED_OTHER': '-o'
                            }
        if priority_type == 'SCHED_FIFO' or priority_type == 'SCHED_RR':
            cmd = 'chrt ' + priority_type_map[priority_type] + ' -p ' + priority + ' ' + pid
        elif priority_type == 'SCHED_OTHER':
            cmd = 'chrt ' + priority_type_map[priority_type] + ' -p 0' + pid
            cmd += ' && renice ' + priority + ' -p ' + pid
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            result = True
    return result

def new_send_process_signal(input_data):
    result = False
    field = input_data.keys()
    pid = input_data['pid'] if 'pid' in field else ''
    pid_signal = input_data['signal'] if 'signal' in field else ''

    if pid and signal and os.path.exists('/proc/'+pid):
        os.kill(int(pid), getattr(signal, pid_signal))
        result = True
    return result

class SystemProcess:
    def GET(self, args):
        if args == '':
            return json.dumps(new_get_process_info());
        else:
            return json.dumps(new_get_process_info(args[1:]));

    def PUT(self, args):
        input_data = json.loads(web.data())
        ret = new_modify_process_nice(input_data)
        if not ret:
            raise RestfulError("580 modify nice of process faild")
        return ''

    def POST(self, args):
        input_data = json.loads(web.data())
        ret = new_send_process_signal(input_data)
        if not ret:
            raise RestfulError("580 signal send faild")
        return ''

app = web.application(urls, locals())
