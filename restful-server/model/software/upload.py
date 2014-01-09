#!/usr/bin/python2.7

import web
import re
import os, shutil
from common import invoke_shell, rpm_query, rpm_install, rpm_update, get_rpminfo, get_sys_startup_mode, new_get_sys_startup_mode
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Upload'
)

def is_rpm_file(file):
    if os.path.isfile(file):
        cmd = 'file ' + file
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            if re.compile(".*RPM.*bin.*").match(stdout):
                return True
    return False

def is_gpg_file(file):
    if os.path.isfile(file):
        cmd = 'file ' + file
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            if re.compile(".*GPG encrypted.*").match(stdout):
                return True
    return False

def has_gpg_secret_key():
    cmd = "gpg -K | grep ^uid | grep \"" + "VmediaX Builder" + "\" | wc -l"
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        if stdout == '1':
            return True
    return False

def rpm_decrypt(infile):
    # import the gpg secret key
    has_key = has_gpg_secret_key()
    if not has_key:
        key_file = '/opt/system/conf/restful-server/rpm-secret-key'
        if not os.path.isfile(key_file):
            msg = '580 system has no gpg decrypt key'
            raise RestfulError(msg)
        key_cmd = 'gpg --import ' + key_file
        status, stdout, stderr = invoke_shell(key_cmd)
        if not status == 0:
            msg = '580 import the gpg key failed [' + key_file + ']'
            raise RestfulError(msg)

    gpg_file = infile + '.gpg'
    if os.path.isfile(infile):
        cmd = "cp " + infile + " " + gpg_file + " && rm -f " + infile + " && " + "/usr/bin/gpg -o " + infile + " -d " + gpg_file + " && rm -f " + gpg_file;
        # print cmd
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            return True
    return False

def upload_install(data):
    save_dir = '/opt/program/upload'
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    save_file = ''
    file_name = ''
    if 'upload_file' in data:
        file_path = data.upload_file.filename.replace('\\','/')
        file_name = file_path.split('/')[-1]
        if not re.compile('.*.rpm$').match(file_name):
            msg = '580 invalid rpm package, the suffix is not .rpm'
            shutil.rmtree(save_dir)
            raise RestfulError(msg)
        # save the upload file
        save_file = save_dir + '/' + file_name
        file = open(save_file, 'w')
        file.write(data.upload_file.file.read())
        file.close()

    # check the file is gpg file or not
    is_gpg = is_gpg_file(save_file)
    if is_gpg:
        ret = rpm_decrypt(save_file)
        if not ret:
            msg = '580 gpg encrypted file is bad'
            shutil.rmtree(save_dir)
            raise RestfulError(msg)

    # check the file is rpm or not
    is_rpm = is_rpm_file(save_file)
    if not is_rpm:
        msg = '580 invaild file, is not a rpm package'
        shutil.rmtree(save_dir)
        raise RestfulError(msg)

    # install the upload rpm package
    rpm_name = ''
    rpm_version = ''
    rpm_info = get_rpminfo(save_file)
    if rpm_info:
        rpm_name = rpm_info['name']
        rpm_version = rpm_info['version']
        rpm_release_version = rpm_info['release']

    print '===================================='
    print 'RPM Package Name   : [' + rpm_name + ']'
    print 'RPM Package Version: [' + rpm_version + ']'
    print 'RPM Package Release: [' + rpm_release_version + ']'
    print '===================================='

    if not rpm_name:
        msg = '580 RPM package name is wrong, break rules'
        raise RestfulError(msg)

    ret = False
    msg = ''
    has_installed = rpm_query(rpm_name)
    if not has_installed:
        ret = rpm_install(save_file)
        if ret:
            record_rpm_log(rpm_name)
            msg = 'install ' + rpm_name + ' success'
        else:
            msg = '580 install [' + rpm_name + '] failed'
            shutil.rmtree(save_dir)
            raise RestfulError(msg)
    else:
        old_rpm_info = get_rpminfo(rpm_name)
        old_version = old_rpm_info['version']
        old_release_version = old_rpm_info['release']

        if (rpm_version > old_version) \
            or (rpm_version == old_version and rpm_release_version > old_release_version):
            # Here, handle special, for system manager tool,
            # It has restful-server and web-frontend
            nodeps = False
            if old_rpm_info['name'] == 'restful-server' or old_rpm_info['name'] == 'web-frontend':
                # sys_startup_mode = get_sys_startup_mode()  # old interface
                sys_startup_mode = new_get_sys_startup_mode()  # new iface
                if sys_startup_mode == 'release':
                    raise RestfulError('580 Error: Current system mode is release, Cannot upgrade system manager tool')
                nodeps = True
            ret = rpm_update(save_file, nodeps)
            if ret:
                msg = 'upgrade ' + rpm_name + ' success'
            else:
                msg = '580 upgrade failed ' + rpm_name
                shutil.rmtree(save_dir)
                raise RestfulError(msg)
        else:
            msg = '580 upgrade failed: RPM['+ rpm_name +'] current version '\
                + rpm_version + '-' + rpm_release_version + ' is less than ' + old_version + '-' + old_release_version
            shutil.rmtree(save_dir)
            raise RestfulError(msg)

    # delete the upload rpm package
    os.remove(save_file)
    shutil.rmtree(save_dir)
    return True

class Upload:
    def GET(self):
        web.header("Content-Type","text/html; charset=utf-8")
        html = """<html><head></head><body>
<form method="POST" enctype="multipart/form-data" action="">
<input type="file" name="upload_file" />
<br/>
<input type="submit" />
</form>
</body></html>"""
        return html

    def PUT(self):
        pass
    def POST(self):
        data = web.input(upload_file = {})
        ret = upload_install(data)
        return ''

    def DELETE(self):
        pass

app = web.application(urls, locals())
