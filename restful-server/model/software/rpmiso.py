#!/usr/bin/python2.7

import web
import re
import cgi

import os, shutil
import json
from common import invoke_shell, rpm_query, rpm_install, rpm_update, get_rpminfo, get_sys_startup_mode, new_get_sys_startup_mode
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

cgi.maxlen = 10 * 1024 * 1024 # 10MB

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

    print 'create_mem_partition ...'
    sta, out, err = invoke_shell('df -h | grep tmpfs | grep -E "isorepo$"')
    if sta != 0:  # already mounted
        mem_cmd = 'mount tmpfs ' + mount_point + ' -t tmpfs -o size=' + mem_size
        sta, out, err = invoke_shell(mem_cmd)
        if sta != 0:
            return False
    return True


def mount_iso(iso_file, mount_point):
    if not os.path.isfile(iso_file):
        raise RestfulError('580 Error: no such iso file ' + iso_file + ', upload failed')
    if not os.path.isdir(mount_point):
        raise RestfulError('580 Error: not such mount point ' + mount_point)

    print 'mount_iso ...'
    cmd = 'mount -o loop ' + iso_file + ' ' + mount_point
    sta, out, err = invoke_shell(cmd)
    if sta != 0:
        print err
        clean_all()
        raise RestfulError('580 Error: cannot mount iso file ' + iso_file + ' to ' + mount_point)
        return False
    return True

def create_iso_yum_repo():
    yum_repo_file = '/usr/local/restful-server/conf/iso-rpm.repo'
    if not os.path.isfile(yum_repo_file):
        raise RestfulError('580 Error: no such yum repo file, ' + yum_repo_file)
        return False

    print 'create_iso_yum_repo ...'
    cmd = 'cp ' + yum_repo_file + ' /etc/yum.repos.d'
    sta, out, err = invoke_shell(cmd)
    if sta != 0:
        return False
    return True

def recovery_rpmdb():
    rpmdb_bak_path = '/opt/system/conf/rpmdb_bak'
    if not os.path.isdir(rpmdb_bak_path):
        raise RestfulError('580 Error: cannot find rpm database path, no ' + rpmdb_bak_path)

    # recovery to first time
    print 'recovery_rpmdb ...'
    cmd = 'cp -ar ' + rpmdb_bak_path + '/* /opt/system/var/lib/rpm'
    sta, out, err = invoke_shell(cmd)
    if sta != 0:
        raise RestfulError('580 Error: recovery rpm db failed')
        return False
    return True

def recovery_product(iso_mount_point):
    # find 'Setup' product file in iso
    setup_file = iso_mount_point + '/Setup'
    if not os.path.isfile(setup_file):
        raise RestfulError('580: Error: cannot find Setup product file in ISO')

    print 'clean local VMediaX.repo ...'
    clean_vmediax_repo()

    product = ''
    sta, out, err = invoke_shell('cat ' + setup_file + ' | head -n 1')
    if sta == 0 and out:
        product = out.strip()
    if product:
        cmd_yum = 'yum clean all && yum -y install ' + product
        print cmd_yum
        sta, out, err = invoke_shell(cmd_yum)
        print '=========== YUM INFO ==========='
        print out
        print err
        if sta == 0:
            return True
    return False

def check_dev_mode():
    sta, out, err = invoke_shell('df -h | grep -E "^/dev/sd[a-z][0-9].*/$"')
    if sta == 0:
        return True
    return False

def install_iso_repo():
    mem_point = '/isorepo'
    iso_mount_point = mem_point + '/repo'

    iso_file_name = 'vmediax-rpm-repo.iso'
    iso_save_file = mem_point + '/' + iso_file_name

    print 'install_iso_repo ...'
    is_dev = check_dev_mode()
    if not is_dev:
        raise RestfulError("580 Error: Current Mode is Release, Switch to Develop Mode")

    if not os.path.isdir(iso_mount_point):
        os.makedirs(iso_mount_point)
    if not os.path.isdir(iso_mount_point):
        raise RestfulError('580 Error: create ' + iso_mount_point + ' failed')

    # mount iso file ...
    ret = mount_iso(iso_save_file, iso_mount_point)
    if ret:
        # return True   # for test
        # create yum repo file
        ret_repo = create_iso_yum_repo()
        if ret_repo:
            # recovery the rpm db to factory settings
            ret_1 = recovery_rpmdb()
            # recovery the iso product
            ret_2 = recovery_product(iso_mount_point)
            if ret_1 and ret_2:
                clean_all()
                return True
    return False

def recovery_vmediax_repo():
    repo = '/etc/yum.repos.d/VMediaX.repo'
    bak = '/etc/yum.repos.d/VMediaX.repo.bak'
    if os.path.isfile(bak):
        re_cmd = 'cp ' + bak + ' ' + repo
        sta, out, err = invoke_shell(re_cmd)
    return True
def clean_vmediax_repo():
    repo = '/etc/yum.repos.d/VMediaX.repo'
    bak = '/etc/yum.repos.d/VMediaX.repo.bak'
    if os.path.isfile(repo):
        cl_cmd = 'mv ' + repo + ' ' + bak
        sta, out, err = invoke_shell(cl_cmd)
    return True

def clean_all():
    print 'clean something ...'
    mem_point = '/isorepo'
    iso_mount_point = mem_point + '/repo'

    if os.path.isdir(iso_mount_point):
        cmd = 'umount -f ' + iso_mount_point
        sta, out, err = invoke_shell(cmd)

    if os.path.isfile('/isorepo/vmediax-rpm-repo.iso'):
        sta, our, err = invoke_shell('rm -f /isorepo/vmediax-rpm-repo.iso')

    if os.path.isdir(mem_point):
        cmd = 'umount -f ' + mem_point
        sta, out, err = invoke_shell(cmd)

    recovery_vmediax_repo()

    # clear yum repo file
    if os.path.isfile('/etc/yum.repos.d/iso-rpm.repo'):
        cmd = 'rm -f /etc/yum.repos.d/iso-rpm.repo'
        sta, out, err = invoke_shell(cmd)
    return True
##############################################################################
def save_stream_file(data):
    mem_point = '/isorepo'
    mem_size = '1G'
    iso_file_name = 'vmediax-rpm-repo.iso'
    iso_save_file = mem_point + '/' + iso_file_name

    ret = create_mem_partition(mem_point, mem_size)
    if not ret:
        raise RestfulError('580 Error: create mem partition failed, memory not enough !!!')
        return False

    if data.chunk == 0 \
        and os.path.isfile(iso_save_file):
        os.remove(iso_save_file)

    if 'upload_iso_file' in data:
        file_name = data.name.strip()
        if not re.compile('.*.iso$').match(file_name):
            msg = '580 Error: invalid iso file !!!'
            raise RestfulError(msg)

        print 'save upload iso file ...'
        file = open(iso_save_file, 'ab')
        file.write(data.file)
        file.close()
        print 'save upload iso file ... ok'
        return True
    return False
##############################################################################

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
        ret = install_iso_repo()
        if ret:
            return 'recovery from ISO success'
        else:
            raise RestfulError('560 Warning: recovery iso failed')
    def POST(self):
        ret = save_stream_file(web.input(upload_iso_file = {}))
        return ''

    def DELETE(self):
        pass

app = web.application(urls, locals())
