#!/usr/bin/python2.7

import web
import json
import re
import os, string, shutil
from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions

urls = (
    '', 'Storage',
    '/(.*)', 'StorageExt'
)

def storage_info():
    data = []
    cmd = 'timeout 3 df -h'
    status, stdout, stderr = invoke_shell(cmd)
    if stdout:
        tmp_dict = {}
        tmp_dict['device'] = ''
        tmp_dict['size'] = ''
        tmp_dict['used'] = ''
        tmp_dict['avail'] = ''
        tmp_dict['use%'] = ''
        tmp_dict['mount-point'] = ''
        for line in stdout.split("\n"):
            if not re.compile("^Filesystem").match(line) \
                and not re.compile('.*error.*').match(line):
                list = line.split()
                length = len(list)
                if length == 1:
                    tmp_dict['device'] = list[0]
                    continue
                elif length == 5:
                    tmp_dict['size'] = list[0]
                    tmp_dict['used'] = list[1]
                    tmp_dict['avail'] = list[2]
                    tmp_dict['use%'] = list[3]
                    tmp_dict['mount-point'] = list[4]
                    dict = tmp_dict.copy()
                    data.append(dict)
                else:
                    tmp_dict['device'] = list[0]
                    tmp_dict['size'] = list[1]
                    tmp_dict['used'] = list[2]
                    tmp_dict['avail'] = list[3]
                    tmp_dict['use%'] = list[4]
                    tmp_dict['mount-point'] = list[5]
                    dict = tmp_dict.copy()
                    data.append(dict)
    return data

def device_list():
    storage_list = storage_info()
    device_list = []
    for info in storage_list:
        device_list.append(info['device'])
    return device_list

def mount_point_list():
    storage_list = storage_info()
    point_list = []
    for info in storage_list:
        point_list.append(info['mount-point'])
    return point_list

def error(msg):
    raise RestfulError("580 " + msg)
    return

def mount(info):
    type = info['type']
    device = ''
    device_type = ''
    mount_point = ''
    already_has_mount_point = False
    username = ''
    password = ''
    startup = ''
    permission = info['permission'] if 'permission' in info.keys() else ''

    if not 'device' in info.keys():
        error('error [device] info')
    else:
        device = info['device']
        if not device:
            error('error [device] info')

    if 'device-type' in info.keys():
        device_type = info['device-type']
        if not re.compile("^(ext2|ext3|ext4|nfs|vfat|ntfs|cifs|swap|ramfs|tmpfs|xfs)$").match(device_type):
            error('invalid device type, use [ext2|ext3|ext4|nfs|vfat|ntfs|cifs|swap|ramfs|tmpfs|xfs]')
    if not type == 'swap':
        if not 'mount-point' in info.keys():
            error('has no [mount-point] info')
        else:
            mount_point = info['mount-point']
            if not mount_point:
                error('invalid mount-point')

            # check already has this mount point
            if not os.path.isdir(mount_point):
                os.makedirs(mount_point)
                already_has_mount_point = True

    if 'username' in info.keys():
        username = info['username']
    if 'password' in info.keys():
        password = info['password']
    if 'startup' in info.keys():
        startup = info['startup']
        if not re.compile("^(on|off){1,1}$").match(startup):
            error('invalid startup [' + startup + ']')

    # print type
    if type == 'disk' or type == 'tmpfs':
        cmd = 'timeout 5 mount -t ' + device_type + ' ' + device + ' ' + mount_point
        # print cmd
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            if startup == 'on':
                has_fstab = has_mount_record(mount_point)
                if not has_fstab:
                    if not device_type:
                        fstab = device + ' ' + mount_point + ' ext3 defaults 0 0'
                    else:
                        fstab = device + ' ' + mount_point + ' ' + device_type + ' defaults 0 0'
                    # print fstab
                    record_mount_log(fstab)

            # add or config the new permission
            ret_permission = add_permission(type, mount_point, permission)
            if not ret_permission:
                msg = '580 config mount point permission failed'
                raise RestfulError(msg)
            return True
        else:
            # del the tmp mount point
            if already_has_mount_point:
                shutil.rmtree(mount_point)
            return False
    elif type == 'nfs':
        if not re.compile(".*:.*").match(device):
            return False
        cmd = 'timeout 5 mount -t nfs -o intr,soft,timeo=1,retrans=2,retry=0 ' + device + ' ' + mount_point
        # print cmd
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            if startup == 'on':
                has_fstab = has_mount_record(mount_point)
                if not has_fstab:
                    # fstab = device + ' ' + mount_point + ' nfs defaults 0 0'
                    fstab = device + ' ' + mount_point + ' nfs intr,bg,soft,timeo=1,retrans=2,retry=0 0 0'
                    # print fstab
                    record_mount_log(fstab)

            # add or config the new permission
            ret_permission = add_permission(type, mount_point, permission)
            if not ret_permission:
                msg = '580 config mount point permission failed'
                raise RestfulError(msg)
            return True
        else:
            # del the tmp mount point
            if already_has_mount_point:
                shutil.rmtree(mount_point)
            return False
    elif type == 'samba':
        if not re.compile("^\/\/").match(device):
            return False
        cmd = 'timeout 5 mount -t cifs ' + device + ' ' + mount_point + ' -o username=' + username + ',password=' + password +',uid=mmap,gid=mmap,intr,soft,timeo=1,retrans=1,retry=0'
        # print cmd
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            if startup == 'on':
                has_fstab = has_mount_record(mount_point)
                if not has_fstab:
                    fstab = device + ' ' + mount_point + ' cifs username=' + username + ',password=' + password + ',uid=mmap,gid=mmap,intr,bg,soft,timeo=1,retrans=1,retry=0' + '  0 0'
                    # print fstab
                    record_mount_log(fstab)

            # add or config the new permission
            ret_permission = add_permission(type, mount_point, permission)
            if not ret_permission:
                msg = '580 config mount point permission failed'
                raise RestfulError(msg)
            return True
        else:
            # del the tmp mount point
            if already_has_mount_point:
                shutil.rmtree(mount_point)
            return False
    elif type == 'raid':            ################## RAID can't support mount function
        return False
    elif type == 'swap':
        cmd = 'swapon ' + device
        status, stdout, stderr = invoke_shell(cmd)
        if status == 0:
            if startup == 'on':
                has_fstab = has_mount_record(device)
                if not has_fstab:
                    fstab = device + ' swap swap defaults 0 0'
                    record_mount_log(fstab)
            return True
        else:
            return False

    return True

def add_permission(device_type, mount_point, permission):
    if not os.path.isdir(mount_point):
        msg = '580 error: mount point not exist'
        raise RestfulError(msg)

    if not device_type in ['disk', 'nfs', 'samba']:
        return True

    if not permission in ['', 'read-only', 'read-write', 'read-exec', 'read-write-exec']:
        msg = '580 error: permission items just in read-only, read-write, read-exec, read-write-exec'
        raise RestfulError(msg)

    # check device type
    # if dev type is 'samba', then no need to change permission
    if device_type == 'samba':
        return True

    per_map = {}
    per_map['read-only'] = '754'
    per_map['read-write'] = '756'
    per_map['read-exec'] = '755'
    per_map['read-write-exec'] = '757'

    if not permission:
        cmd = 'chown -R mmap.mmap ' + mount_point \
                 + ' && ' + 'chmod -R ' + per_map['read-exec'] + ' ' + mount_point
    else:
        cmd = 'chown -R mmap.mmap ' + mount_point \
                 + ' && ' + 'chmod -R ' + per_map[permission] + ' ' + mount_point
    status, stdout, stderr = invoke_shell(cmd)
    # if status != 0:         # drop this permission error
    #     return False
    return True

def swap_device_list():
    data = []
    cmd = 'cat /proc/swaps'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        if stdout:
            for line in stdout.split("\n"):
                if line:
                    if re.compile("^\/").match(line):
                        tmp_list = line.split()
                        data.append(tmp_list[0])
    return data

def umount(info):
    mount_point = ''
    if 'mount-point' in info.keys():
        mount_point = info['mount-point']

    if not mount_point or not (mount_point in mount_point_list() or mount_point in swap_device_list()):
        error('system has no such mount-point [' + mount_point + ']')

    if mount_point in swap_device_list():
        cmd = 'swapoff ' + mount_point
    else:
        cmd = 'umount -f ' + mount_point
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        # print 'umount ' + mount_point + ' success'
        has_fstab = has_mount_record(mount_point)
        if has_fstab:
            delete_mount_log(mount_point)
    else:
        msg = 'Error: ' + stdout.strip() + ' ' + stderr.strip()
        error(msg);
    return

###############################################################################
class Storage:
    def GET(self):
        data = storage_info()
        return json.dumps(data)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        input = json.loads(web.data())
        umount(input)
        return

class StorageExt:
    def GET(self, arg):
        pass
    def PUT(self, arg):
        pass
    def POST(self, arg):
        if not re.compile("^(disk|nfs|samba|raid|tmpfs){1,1}$").match(arg):
            error('invalid arg [' + arg + '], use disk|nfs|samba|raid|tmpfs')

        input = json.loads(web.data())
        input['type'] = arg
        ret = mount(input)
        if ret:
            return
        else:
            error('mount failed')

    def DELETE(self, arg):
        if arg:
            error('invalid arg [' + arg + '], DELETE method has no params')
            return

app = web.application(urls, locals())
