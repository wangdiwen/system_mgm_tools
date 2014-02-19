#!/usr/bin/python2.7

import web
import os
import time
import subprocess
import re
import json

class RestLog():
    log_file = '/opt/system/log/restful-server/restful.log'

    def __init__(self):
        pass

    @staticmethod
    def log():
        # log format
        # [2013-05-30 11:09:55] (10.1.89.101) HTTP/1.1 GET /network/adaptors/eth0/workmode -- <http-code> <error msg>
        web_env = web.ctx
        cur_time = time.strftime('%Y-%m-%d %X', time.gmtime(time.time() + 8*60*60))     # time.time() is utc, +8 hours is shanghai timezone
        re_path = web_env['path']
        re_method = web_env['method']
        re_pro = web_env['protocol']
        # user_ip = web_env['ip']
        user_ip = web.cookies().get('ip') if web.cookies().get('ip') else web.ctx.env['REMOTE_ADDR']
        http_code = web_env['status'].replace("\n", "")

        input_data = web.data()
        input_data = input_data.replace("\n", "")

        log_msg = '['+cur_time+'] ('+user_ip+') '+re_pro.upper()+' '+re_method+' '+re_path+' Data: ['+input_data+']'+' -- '+http_code
        # print log_msg
        if not re_method == 'GET' and not re_path == '/auth':
            file = open(RestLog.log_file, 'a')
            file.write(log_msg.strip()+"\n")
            file.close()
