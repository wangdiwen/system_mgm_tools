#!/usr/bin/python2.7

import web
import re
import os, shutil
import json
from common import invoke_shell, rpm_query, rpm_install, rpm_update, get_rpminfo, get_sys_startup_mode, new_get_sys_startup_mode
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Rpmiso'
)


def create_mem_partition(mount_point, mem_size):
    if not os.path.isdir(mount_point):
        os.makedirs(mount_point)

    if not os.path.isdir(mount_point):
        raise RestfulError('580 Error: create mount point ' + mount_point + ' failed')
    if not mem_size:
        raise RestfulError('580 Error: cannot distribute mem size')

    mem_cmd = 'mount tmpfs ' + mount_point + ' -t tmpfs -o size=' + mem_size
    sta, out, err = invoke_shell(mem_cmd)
    if sta != 0:
        clean_all()
        raise RestfulError('580 Error: mount tmpfs failed, mem not enough !')
    return True

def mount_iso(iso_file, mount_point):
    if not os.path.isfile(iso_file):
        raise RestfulError('580 Error: no such iso file ' + iso_file + ', upload failed')
    if not os.path.isdir(mount_point):
        raise RestfulError('580 Error: not such mount point ' + mount_point)

    cmd = 'mount -o loop ' + iso_file + ' ' + mount_point
    sta, out, err = invoke_shell(cmd)
    if sta != 0:
        clean_all()
        raise RestfulError('580 Error: cannot mount iso file ' + iso_file + ' to ' + mount_point)
        return False
    return True

def create_iso_yum_repo():
    yum_repo_file = '/usr/local/restful-server/conf/iso-rpm.repo'
    if not os.path.isfile(yum_repo_file):
        clean_all()
        raise RestfulError('580 Error: no such yum repo file, ' + yum_repo_file)
        return False

    cmd = 'cp ' + yum_repo_file + ' /etc/yum.repos.d'
    sta, out, err = invoke_shell(cmd)
    if not sta:
        clean_all()
        return False
    return True

def recovery_rpmdb():
    rpmdb_bak_path = '/opt/system/conf/rpmdb_bak'
    if not os.path.isdir(rpmdb_bak_path):
        raise RestfulError('580 Error: cannot find rpm database path, no ' + rpmdb_bak_path)

    # recovery to first time
    cmd = 'cp -ar ' + rpmdb_bak_path + '/* /opt/system/var/lib/rpm'
    sta, out, err = invoke_shell(cmd)
    if sta != 0:
        clean_all()
        raise RestfulError('580 Error: recovery rpm db failed')
        return False
    return True


def install_iso_repo(data):
    mem_point = '/isorepo'
    iso_mount_point = mem_point + '/repo'
    mem_size = '1G'

    iso_file_name = 'vmediax-rpm-repo.iso'
    iso_save_file = mem_point + '/' + iso_file_name

    print 'install_iso_repo ...'
    print 'First, try to clean something last time ...'
    clean_all()

    ret = create_mem_partition(mem_point, mem_size)
    if ret:
        if not os.path.isdir(iso_mount_point):
            os.makedirs(iso_mount_point)
        if not os.path.isdir(iso_mount_point):
            raise RestfulError('580 Error: create ' + iso_mount_point + ' failed')

        if 'upload_iso_file' in data:
            file_path = data.upload_iso_file.filename.replace('\\','/')
            file_name = file_path.split('/')[-1]
            if not re.compile('.*.iso$').match(file_name):
                msg = '580 Error: invalid iso file !!!'
                raise RestfulError(msg)

            # save the upload file
            file = open(iso_save_file, 'w')
            file.write(data.upload_iso_file.file.read())
            file.close()

    # mount iso file ...
    ret = mount_iso(iso_save_file, iso_mount_point)
    if ret:
        # create yum repo file
        ret_repo = create_iso_yum_repo()
        if ret_repo:
            # recovery the rpm db to factory settings
            ret = recovery_rpmdb()
            return True
    return False

def clean_all():
    mem_point = '/isorepo'
    iso_mount_point = mem_point + '/repo'

    if os.path.isdir(iso_mount_point):
        cmd = 'umount -f ' + iso_mount_point
        sta, out, err = invoke_shell(cmd)

        if os.path.isfile('/isorepo/vmediax-rpm-repo.iso'):
            sta, our, err = invoke_shell('rm -f /isorepo/vmediax-rpm-repo.iso')

        cmd = 'umount -f ' + mem_point
        sta, out, err = invoke_shell(cmd)

    # clear yum repo file
    if os.path.isfile('/etc/yum.repos.d/iso-rpm.repo'):
        cmd = 'rm -f /etc/yum.repos.d/iso-rpm.repo'
        sta, out, err = invoke_shell(cmd)

    return True


class Rpmiso:
    def GET(self):          # just for test
        web.header("Content-Type","text/html; charset=utf-8")
        html = """<html><head></head><body>
<form method="POST" enctype="multipart/form-data" action="">
<input type="file" name="upload_iso_file" />
<br/>
<input type="submit" />
</form>
</body></html>"""
        return html

    def PUT(self):
        pass
    def POST(self):
        data = web.input(upload_iso_file = {})
        ret = install_iso_repo(data)
        return ''

    def DELETE(self):
        ret = clean_all()
        return ''

app = web.application(urls, locals())
