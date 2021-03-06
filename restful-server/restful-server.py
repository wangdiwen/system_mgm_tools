#!/usr/bin/python2.7

import os, json, re
import web
import threading
import cgi

web.config.debug = False
cgi.maxlen = 0                  # here, no limit the post upload file

from common import auth_list, invoke_shell
from common.restfulclient import RestfulError

from model.log.log import RestLog
from common.deamon_task import LogClear, NtpSync
from model.storage.raid import RaidMonitor
from model.storage.raid import ScsiMonitor

#################################################################

from common.global_helper import GlobalData, json_echo
# check system has init the meta data or not
from model.test.test import init_meta_data, detect_system_tools

#################################################################

#####
#model import
import model.system.info as model_system_info
import model.system.process as model_system_process
import model.system.systime as model_system_time
import model.system.disk as model_system_disk
import model.system.ntp as model_system_ntp
import model.system.syslog as model_system_syslog
import model.system.startup_mode as model_system_startup_mode
import model.system.manager as model_system_manager
import model.system.license as model_system_license
import model.system.env as model_system_env

import model.network.hostname as model_network_hostname
import model.network.adaptors as model_network_adaptors
import model.network.nameserver as model_network_nameserver
import model.network.route as model_network_route
import model.network.iptables as model_network_iptables
import model.network.ping as model_network_ping
import model.network.traceroute as model_network_traceroute

import model.software.softinfo as model_software_softinfo
import model.software.upload as model_software_upload
import model.software.uninstall as model_software_uninstall
import model.software.startup as model_software_startup
import model.software.service as model_software_service
import model.software.rpmiso as model_software_rpmiso

import model.storage.raid as model_storage_raid
import model.storage.storage as model_storage_storage

try:
    import model.extend.monitorsettinginface as model_extend_monitorsetting
except Exception as e:
    class _model_extend_monitorsetting:
        app = web.application((), locals())
    model_extend_monitorsetting = _model_extend_monitorsetting()

try:
    import model.extend.nvidiasettinginface as model_extend_nvidiasetting
except Exception as e:
    class _model_extend_nvidiasetting:
        app = web.application((), locals())
    model_extend_nvidiasetting = _model_extend_nvidiasetting()

try:
    import model.extend.atisettinginface as model_extend_atisetting
except Exception as e:
    class _model_extend_atisetting:
        app = web.application((), locals())
    model_extend_atisetting = _model_extend_atisetting()


import model.test.test as model_test_test

urls = (
    "/system/info", model_system_info.app,
    "/system/process", model_system_process.app,
    "/system/time", model_system_time.app,
    '/system/disk', model_system_disk.app,
    '/system/ntp', model_system_ntp.app,
    '/system/log', model_system_syslog.app,
    '/system/startup-mode', model_system_startup_mode.app,
    '/system/license', model_system_license.app,
    '/system/env', model_system_env.app,
    '/system', model_system_manager.app,

    '/network/hostname', model_network_hostname.app,
    '/network/adaptors', model_network_adaptors.app,
    '/network/nameserver', model_network_nameserver.app,
    '/network/route', model_network_route.app,
    '/network/iptables', model_network_iptables.app,
    '/network/ping', model_network_ping.app,
    '/network/traceroute', model_network_traceroute.app,

    '/software/upload', model_software_upload.app,
    '/software/uninstall', model_software_uninstall.app,
    '/software/startup', model_software_startup.app,
    '/software/service', model_software_service.app,
    '/software/rpminfo', model_software_softinfo.app,
    '/software/rpmiso', model_software_rpmiso.app,

    '/storage/raid', model_storage_raid.app,
    '/storage', model_storage_storage.app,

    '/extend/monitor-setting', model_extend_monitorsetting.app,
    '/extend/nvidia-setting', model_extend_nvidiasetting.app,
    '/extend/ati-setting', model_extend_atisetting.app,

    '/auth', 'Auth_user',

    '/test', model_test_test.app,
)

def auth_user(user, passwd):
    user_list = auth_list()
    if not user in user_list.keys():
        raise RestfulError('570 no such user [' + user + ']')
    else:
        user_passwd = user_list[user]
        if not user_passwd == passwd:
            raise RestfulError('570 password wrong')
        else:
            return True
    return False

class Auth_user():
    def GET(self):
        name = web.cookies().get('user_name')
        passwd = web.cookies().get('user_passwd')

        if not name or not passwd:
            raise RestfulError('570 cookies error')

        # rule = re.compile("^[\w-]+$")
        # if not rule.match(name) or not rule.match(passwd):
        #     raise RestfulError('570 name or passwd just support [0-9a-zA-Z_-] characters')

        ret = auth_user(name, passwd)
        if ret:
            return ''
        else:
            raise RestfulError('570 auth failed')
    def PUT(self):
        pass
    def POST(self):
        if not web.data():
            err = '570 auth failed'
            raise RestfulError(err)
        input = json.loads(web.data())
        if not 'name' in input.keys() or not 'passwd' in input.keys():
            err = '570 name and passwd is empty'
            raise RestfulError(err)
        name = input['name']
        passwd = input['passwd']
        auth = auth_user(name, passwd)
        if auth:
            return ''
        else:
            msg = '570 auth failed'
            raise RestfulError(msg)
    def DELETE(self):
        pass

def auth_processor(handler):
    path = web.ctx.path
    method = web.ctx.method
    if path == '/auth' and (method == 'POST' or method == 'GET'):
        return handler()
    else:
        name = web.cookies().get('user_name')
        passwd = web.cookies().get('user_passwd')

        if not name or not passwd:
            raise RestfulError('570 cookies auth error')

        # Note:
        # 1. switch system model for develop or release, must auth 'admin' user,
        #     'user' user has no permission.
        # 2. shutdown or reboot the mechine, must auth the user, only 'admin' can do.
        if path in ['/system/shutdown', '/system/reboot'] \
            or (path == '/system/startup-mode' and method == 'PUT'):
            # check user is 'admin'
            if name != 'admin':
                raise RestfulError("580 Auth Error: No permission, only admin can do this!")


        # filter chinese and other characters
        # rule = re.compile("^[\w-]+$")
        # if not rule.match(name) or not rule.match(passwd):
        #     raise RestfulError('570 name or passwd just support [0-9a-zA-Z_-] characters')

        ret = auth_user(name, passwd)
        if ret:
            return handler()
        else:
            raise RestfulError('570 auth failed')

def unloadhook():
    RestLog.log()

def notfound():
    return web.notfound("Sorry, the page you were looking for was not found.")

app = web.application(urls, globals())
app.add_processor(auth_processor)
app.add_processor(web.unloadhook(unloadhook))
app.notfound = notfound

if __name__ == "__main__":
    os.environ["PORT"] = "88"
    cgi.maxlen = 0                  # here, no limit the post upload file

    # check sys version
    global_data = GlobalData()
    # root_path = os.getcwd()
    root_path = '/usr/local/restful-server'
    global_data.set_restful_root(root_path)
    global_data.set_template_path()

    # first, detect system tools...'
    det_ret = detect_system_tools()
    print json_echo(det_ret)
    # crawler the sys env, and init the global json meta data
    init_meta_data()

    # deamon thread task, settings time is 15s
    thread_lock = threading.Lock()
    logclear_process = LogClear(thread_lock, 'clear-log-disk')
    logclear_process.start()

    # deamon threading task, ntp sync
    ntp_process = NtpSync('ntp-sync')
    ntp_process.start()

    # monitor the raid device status
    # raid_thread_lock = threading.Lock()
    # raid_monitor_process = RaidMonitor(raid_thread_lock, 'monitor_raid')
    # raid_monitor_process.start()

    scsi_monitor = ScsiMonitor()
    scsi_monitor.init_scsi_raid_map()

    # start restful server
    app.run()
