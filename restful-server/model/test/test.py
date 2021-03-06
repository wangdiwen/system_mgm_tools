import os
import sys
import re, json
import web

from common.global_helper import *
from model.network.adaptors import get_all_iface

#################################################################
urls = (
    '', 'Test',
    '/(.*)', 'TestExt'
)
#################################################################
def detect_systool():
    data = {}
    sys_tool_list = ['ethtool', 'ifconfig', 'hostname', 'iptables', 'ping', 'route', 'traceroute', \
                    'service', 'rpm', 'gpg', 'df', 'mount', 'umount', 'swapon', 'chown', 'swapoff', \
                    'fdisk', 'dmidecode', 'lspci', 'ntpdate', 'chrt', 'renice', 'tail', 'date', 'sed', \
                    'mkfs.xfs', 'parted', 'mdadm', 'resize2fs', 'udevadm', 'smartctl']
    for tool in sys_tool_list:
        data[tool] = 'no'
        shell = 'which ' + tool
        status, stdout, stderr = shell_cmd(shell)
        if status == 0:
            data[tool] = 'yes'

    return data

def crawler_sys_meta():
    # init the meta data
    meta = {
        'system': {},
        'network': {
            'adaptors': {},
            'nameserver': [],
            'hostname': '',
            'default_gateway': '10.1.0.1',
            'route': [],
            'iptables': [],
        },
        'software': {},
        'storage': {},
        'extend': {},
        'env': {},
        'restful': {},
        'raid': {},
    }

    # crawler sys meta data

    # 1. hostname
    shell = 'hostname'
    status, stdout, stderr = shell_cmd(shell)
    if status == 0:
        meta['network']['hostname'] = stdout.strip()

    # 2. nameserver DNS
    conf = '/etc/resolv.conf'
    nameserver_list = engine_text_parse(conf, ['nameserver'], ' ', 'list')
    meta['network']['nameserver'] = nameserver_list

    # 3. adaptors ethx:x
    adaptors = get_all_iface()
    for adaptor in adaptors:
        conf = '/etc/sysconfig/network-scripts/ifcfg-%s' % adaptor
        filter_exp = ['^DEVICE', '^BOOTPROTO', '^GATEWAY', '^HWADDR', '^IPADDR', '^NETMASK', '^ONBOOT', '^ETHTOOL_OPTS']
        eth_info = engine_text_parse(conf, filter_exp, '=', 'dict')
        for key in eth_info.keys():
            eth_info[key] = eth_info[key].replace("\"", '')
        # check ethtool_opts exist or not
        if re.compile('^eth[0-9]$').match(adaptor):
            if not 'ETHTOOL_OPTS' in eth_info.keys():
                # eth_info['ETHTOOL_OPTS'] = 'speed 1000 duplex full autoneg on'
                eth_info['ETHTOOL_OPTS'] = 'autoneg on'    # just auto, by diwen
        meta['network']['adaptors'][adaptor] = eth_info

    # 4. iptables and route
    meta['network']['iptables'] = []
    meta['network']['route'] = []

    # 5. software part
    meta['software']['installed'] = []
    meta['software']['startup'] = []
    meta['software']['service'] = []

    # 6. storage mount device
    meta['storage']['device'] = []

    # 7. restful itself
    meta['restful']['log-disk-ratio'] = 90

    # 8. ntp server
    meta['system']['ntp-server'] = {}
    meta['system']['ntp-server']['status'] = 'off'
    meta['system']['ntp-server']['ntp'] = []
    meta['system']['ntp-server']['ntp'].append('1.cn.pool.ntp.org')
    meta['system']['ntp-server']['ntp'].append('130.149.17.21')
    meta['system']['ntp-server']['ntp'].append('2.asia.pool.ntp.org')
    meta['system']['ntp-server']['ntp'].append('3.asia.pool.ntp.org')

    # 9. others
    meta['extend'] = {}

    # 10. copy '/etc/sysctl.conf' config file to template path
    template_path = get_template_path()
    if os.path.isdir(template_path):
        shell = 'cp /etc/sysctl.conf ' + template_path \
                + ' && sed -i \'s/net.ipv4.ip_forward = 1/net.ipv4.ip_forward = \{\{IPFORWARD\}\}/g\'' \
                + ' ' + template_path + '/sysctl.conf'
        status, stdout, stderr = shell_cmd(shell)
        if status == 0:
            print 'init sysctl.conf template_path file, set IPFORWARD field'

    # 11. copy '/etc/profile' as a template file
    if os.path.isdir(template_path):
        shell = 'cp /etc/profile ' + template_path
        status, stdout, stderr = shell_cmd(shell)
        if status == 0:
            print 'copy [ /etc/profile ] to template_path ' + template_path

    # 12. int raid info
    meta['raid']['type'] = ''    # 'raid5', 'raid0', 'raid1', 'raid10'
    meta['raid']['count'] = 0   # raid5 >= 3, raid0 >= 2, raid1 >= 2, raid10 >= 4
    meta['raid']['device'] = []  # like: ['sda1', 'sdb1', 'sdc1']

    # save to meta data
    return set_meta_data(meta)

def render_test_conf():  # test example
    conf = GlobalData.g_template_path+'/'+'test.conf'
    save = GlobalData.g_template_path+'/'+'new_test.conf'
    map_dict = {
        'HOSTNAME':'bogon',
        'TEST':'test',
        'NAME':'diwen',
    }
    return render_template(conf, map_dict, save)

def init_vmx_rpm_list(global_meta):
    rpm_list = [
        'activemq', 'apache-vmx', 'aria2c', 'as', 'configures', 'hvec', 'jre-vmx',
        'logread', 'media-mounts', 'mrs-as-backend', 'mrs-frontend', 'mysql-conf',
        'net-snmp-vmx', 'openoffice-conf', 'python27', 'restful-server', 'rsyncd',
        'shellexecutor', 'sigar-vmx', 'swftools', 'usbkey', 'videotools', 'web-frontend',
        'mrs-oss-backend', 'mrs-4000-os', 'mrs-4000-as',
        'tvwall-backend', 'tvwall-webcontent', 'tvwall-frontend', 'tvwall-mysql-conf',
        'libX11', 'SDL', 'libX11-common', 'tvwall-config', 'libXrender',
        'libpcap', 'nvidia-driver',
    ]

    if 'software' in global_meta.keys():
        global_meta['software']['installed'] = []
        for item in rpm_list:
            global_meta['software']['installed'].append(item)

        # save the meta data
        ret = set_meta_data(global_meta)
        if ret:
            return True
    return False

def init_vmx_startup(global_meta):
    # '/opt/program/bin/' dir name -> rpm pkg name, map data
    # all_rpm = {
    #     'hvec': 'hvec',
    #     'wowza': 'as',
    #     'rss': 'mrs-as-backend/mrs-oss-backend',
    #     'tomcat': 'mrs-frontend',
    #     'apache': 'apache-vmx',
    # }
    all_rpm = ['hvec', 'wowza', 'rss', 'tomcat', 'apache']
    has_mod = False
    sta, out, err = shell_cmd('find /opt/program/bin/ -type f -name \".init\" | awk -F\"/\" \'{ print $5 }\'')
    # out like: 'apache  hvec  lost+found  rss  tomcat  videotools  wowza'
    if sta == 0 and out:
        name_list = out.strip().split("\n")
        if len(name_list) > 0 and 'software' in global_meta.keys():
            global_meta['software']['startup'] = []

            other_rpm = []
            for item in name_list:
                if not item in all_rpm:
                    other_rpm.append(item)

            for item in all_rpm:
                if item in name_list:
                    global_meta['software']['startup'].append(item + '|on')
                else:
                    global_meta['software']['startup'].append(item + '|off')

            for item in other_rpm:
                global_meta['software']['startup'].append(item + '|on')

            # create 'startup' conf file
            conf_file = '/opt/system/conf/restful-server/startup'
            ret = create_conf_by_list(conf_file, global_meta['software']['startup'], '', '')

            has_mod = True

        if has_mod:
            ret = set_meta_data(global_meta)
            if ret:
                return True
    return False

def init_meta_data():
    print '=========================================================='
    print 'Now, checking global meta data...'

    meta = get_meta_data()
    has_data = True if 'restful' in meta.keys() else False
    if not has_data:
        print 'System tool is first to run in this machine !'
        print 'Start to init global meta data...'
        ret = crawler_sys_meta()
        print 'Init global meta data OK !'
    else:
        # Here, modify the dns
        run_file = '/etc/resolv.conf'
        ret = create_conf_by_list(run_file, meta['network']['nameserver'], 'nameserver', ' ')
        ret = sync_run_config_file(run_file)

        print 'Warning: System already has meta, no need to init !'

    # init vmediax's rpm pkg list data
    # meta = get_meta_data()              # get the new meta again
    # ret = init_vmx_rpm_list(meta)
    # if ret:
    #     print 'init vmediax rpm pkg list OK'

    # ret = init_vmx_startup(meta)
    # if ret:
        # print 'init vmediax startup software OK'

    print '=========================================================='
    return True

def detect_system_tools():
    print 'Now, detecting the Linux system tools...'
    print '============ Result Below =================================='
    data = {'total': 0,
            'success': 0,
            'failed': 0,
            'result': {}
            }
    det_ret = detect_systool()
    if det_ret:
        tool_name_list = det_ret.keys()
        success_count = 0
        failed_count = 0
        for name in tool_name_list:
            value = det_ret[name]
            if value == 'yes':
                success_count += 1
            else:
                failed_count += 1
        data['total'] = len(tool_name_list)
        data['success'] = success_count
        data['failed'] = failed_count
        data['result'] = det_ret

    if data:
        shell = 'echo \"' + json_echo(data) + '\" > /opt/system/conf/restful-server/system_detect_tools.log'
        status, stdout, stderr = shell_cmd(shell)
    return data

def revise_meta_data():
    meta = get_meta_data()
    # self define func
    # meta['network']['route'] = []
    ret = remove_dict_by_key(meta['network']['adaptors'], 'eth0:4')

    return set_meta_data(meta)

#################################################################
class Test():
    def GET(self):
        # return json_echo(template_name('hosts'))
        meta = get_meta_data()
        return json_echo(meta)

    def PUT(self):
        ret = revise_meta_data()
        return 'revise_meta_data...'

    def POST(self):
        ret = crawler_sys_meta()
        meta = get_meta_data()
        return json_echo(meta)

    def DELETE(self):
        pass

class TestExt():
    def GET(self, arg):
        if arg == 'detect_systool':
            data = detect_system_tools()
            return json_echo(data)
        return ''

    def PUT(self, arg):
        pass
    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
