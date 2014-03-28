#!/usr/bin/python

import os
import sys
import re, json, types, shutil
import time
from subprocess import Popen, PIPE

###############################################################################
###############################################################################
def shell_cmd(cmd, wait = True, option = 0):
    # Note:
    # wait-> status=0; no wait-> status=None
    # option: 0, False > (status, stdout, stderr),
    #         1, True > status, 2 > stdout, 3 > stderr
    stdout = ''
    status = 0
    stderr = ''
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    if wait:
        process.wait()
    status = process.returncode
    stdout, stderr = process.communicate()
    if option in [0, False]:
        return (status, stdout.strip(), stderr.strip())
    elif option in [1, True]:
        return status
    elif option in [2]:
        return stdout.strip()
    elif option in [3]:
        return stderr.strip()
    return (status, stdout.strip(), stderr.strip())

def set_meta_data(json_dict):
    conf = '/opt/system/conf/restful-server/global_meta_data.json'
    if not json_dict:
        return False
    file = open(conf, 'w')
    context = json.dumps(json_dict)
    file.write(context)
    file.close()
    return True

def get_meta_data():
    conf = '/opt/system/conf/restful-server/global_meta_data.json'
    if os.path.isfile(conf):
        file = open(conf, 'r')
        context = file.read()
        file.close()
        if context:
            return json.loads(context)
    return {}


def get_teminal_input(tips = 'Pls input', options = ['y', 'n', 'yes', 'no'], auto_answer = 'y'):
    if auto_answer in options:
        return auto_answer
    data = ''
    while True:
        data = raw_input(tips + ': ')
        if data in options:
            break
    return data

class Color:
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4

def log(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.GREEN, '\t'+str)
def tips(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.GREEN, '\t'+str)
def error(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.RED, '\t'+str)
def warning(str = ''):
    print '\033[0;3%dm%s\033[0m' % (Color.YELLOW, '\t'+str)
def quit(code = 0, msg = ''):
    if code == 0 and msg:
        print msg
    elif msg:
        print '\033[0;3%dm%s\033[0m' % (Color.RED, msg)
    sys.exit(code)
###############################################################################

###############################################################################
print ''
print '\t################### Auto Building RAID Machine ###################\n'
###############################################################################
########### Here, Define your functions and processes #########################

def check_user():
    user = shell_cmd('whoami', True, 2)
    if user == 'root':
        log('login user is root')
        return True
    return False

def has_raid_aleady():
    md_count = shell_cmd('ls /dev/ | grep md0 | wc -l', True, 2)
    if md_count == '1':
        return True
    return False

def save_udev_config():
    udev_rule_path = '/etc/udev/rules.d'
    rule_name = '10-raid.rules'
    restful_file = '/opt/system/conf/restful-server/' + rule_name
    if not os.path.isfile(udev_rule_path + '/' + rule_name):
        if not os.path.isfile(restful_file):
            error('no raid udev config file ' + restful_file)
            quit(1, 'error')

        cmd = 'cp ' + restful_file + ' ' + udev_rule_path
        # log(cmd)
        ret = shell_cmd(cmd, True, 1)
        if ret != 0:
            return False
    return True

def check_ava_disk():
    data = []
    disk_list = shell_cmd('ls /dev/ | grep -v grep | grep "disk_[0-9]$"', True, 2)
    if disk_list:
        for item in disk_list.split("\n"):
            data.append(item)
    return data

def availabel_disk_partition():
    data = []
    all_disk = shell_cmd('ls /dev/ | grep -v grep | grep "^disk_[0-9]1$"', True, 2)
    if all_disk:
        for item in all_disk.split("\n"):
            data.append(item)
    return data

def init_raid_device(raid_type = '5', raid_name = 'md0', disk_list = []):
    if raid_type in ['0', '1', '5'] \
        and disk_list and raid_name in ['md0']:

        # check the min disk count for types
        disk_partition_count = len(disk_list)
        if raid_type == '5':
            if disk_partition_count < 3:
                error('raid5 need disk partition >= 3, available count are %d' % disk_partition_count)
                error('quit')
                quit(1)
            else:
                log('raid5: available disk partition count are %d' % disk_partition_count)
        elif raid_type in ['0', '1']:
            if disk_partition_count < 2:
                error('raid0 and raid1 need disk partition >= 2, available count are %d' % disk_partition_count)
                error('quit')
                quit(1)
            else:
                log('raid%s: available disk partition count are %d' % (raid_type,disk_partition_count))

        dev_count = len(disk_list)
        tmp_disk_list = []
        for item in disk_list:
            tmp_disk_list.append('/dev/' + item)
        disk_str = ' '.join(tmp_disk_list)

        ###################### Here, resolve the 'device or resource busy' problem ###################3
        # Note: helpful url http://dev.bizo.com/2012/07/mdadm-device-or-resource-busy.html

        #################################
        # shutdown the udev monitor queue
        ret_code = shell_cmd('udevadm control --stop-exec-queue', True, 1)
        if ret_code != 0:
            error('shutdown udev monitor queue, failed')
            quit(1)

        shell = 'echo -e "y\n" | mdadm -C /dev/%s -a yes -l %s -n %d %s' % (raid_name, raid_type, dev_count, disk_str)
        log(shell)
        status, stdout, stderr = shell_cmd(shell)
        if status == 0:

            ###################################
            # open the udev monitor queue again
            ret_code = shell_cmd('udevadm control --start-exec-queue', True, 1)
            if ret_code != 0:
                error('open udev monitor queue, failed')
                quit(1)

            print 'init the config file [/etc/mdadm.conf] ...'

            shell_conf = 'echo \"DEVICE ' + disk_str + '\" > /etc/mdadm.conf && mdadm -Ds >> /etc/mdadm.conf'
            log(shell_conf)
            ret_conf = shell_cmd(shell_conf, True, 1)
            if ret_conf == 0:
                log('init config file ok ...')
                print 'save config to restful-server config record ...'
                meta = get_meta_data()
                raid_meta = meta['raid']
                raid_meta['count'] = dev_count
                raid_meta['device'] = disk_list
                raid_meta['type'] = 'raid' + raid_type
                ret_set = set_meta_data(meta)
                if ret_set:
                    log('init restful meta data OK')
                return True
        else:
            error(stderr)
    else:
        error('param error, in init_raid_device func')
        error('exit !!!')
        quit(1)
    return False

def check_disk_volume(sys_disk_list):  # return number: 500, 1000 ...
    disk_vol = '500'
    vol_list = []
    for disk in sys_disk_list:  # disk like: disk_1/disk_2
        # cmd = 'parted -s /dev/'+ disk +' print | grep "^Disk" | awk \'{ print $3 }\''
        cmd = 'fdisk -l /dev/disk_1 | grep "^Disk" | head -1 | awk \'{ print $3 }\''
        sta, out, err = shell_cmd(cmd)
        if sta == 0 and out:
            tmp_str = out.strip()
            tmp_list = tmp_str.split('.')
            disk_vol = tmp_list[0]
            # disk_vol = disk_vol[0:-2]
            log(disk + ' ==> ' + disk_vol)
            vol_list.append(int(disk_vol))
    # get the minor invalid volume
    vol_list.sort()
    disk_vol = vol_list[0]
    if disk_vol < 500:
        error('Checking system disk, find one disk volume < 500G, cannot builded raid, quit ...')
    return disk_vol

def usage_help():
    usage = "Usage: ./build_raid.py [options]\n\
        options: \n\
                start => start raid\n\
                stop  => stop the current raid device\n\
                delete => delete the old raid device\n\
                build => build raid"
    tips(usage)
    quit(0)
###############################################################################
def start_raid():
    print 'start raid device ...'
    status = shell_cmd('cat /proc/mdstat | grep md0', True, 1)
    if status == 0:
        tips('md0 has aleady started ...')
    else:
        status = shell_cmd('mdadm -As', True, 1)
        if status == 0:
            tips('success')
        else:
            tips('failed')
    quit(0, 'bye ...')

def stop_raid():
    print 'stop raid device ...'
    print 'checking raid mount ...'
    out = shell_cmd('df -h | grep md0 | awk \'{ print $6 }\'', True, 2)
    if out:
        mounted_point = out.strip()
        print 'umount ' + mounted_point + ' ...'
        status = shell_cmd('umount ' + mounted_point, True, 1)
        if status == 0:
            tips('ok')
        else:
            error('cannot umount ' + mounted_point)
            quit(1, 'quit')

    status = shell_cmd('mdadm -D /dev/md0', True, 1)
    if status != 0:
        tips('md0 is not start, nothing to stop ...')
    else:
        status = shell_cmd('mdadm -S /dev/md0', True, 1)
        if status == 0:
            tips('success')
        else:
            tips('failed')
    quit(0, 'bye ...')

def delete_raid():
    print 'checking raid mount ...'
    out = shell_cmd('df -h | grep md0 | awk \'{ print $6 }\'', True, 2)
    if out:
        mounted_point = out.strip()
        print 'umount ' + mounted_point + ' ...'
        status = shell_cmd('umount ' + mounted_point, True, 1)
        if status == 0:
            tips('ok')
        else:
            error('cannot umount ' + mounted_point)
            quit(1, 'quit')

    status = shell_cmd('mdadm -D /dev/md0', True, 1)
    if status != 0:
        tips('md0 is not start, nothing to stop ...')
    else:
        print 'try to stop the raid device ...'
        status = shell_cmd('mdadm -S /dev/md0', True, 1)
        if status == 0:
            tips('ok')
        else:
            error('stop md0 failed')
            tips('try to set the raid disk false ...')
            meta = get_meta_data()
            raid_disk_list = meta['raid']['device']  # like: disk_11
            for item in raid_disk_list:
                tips('set fault ' + item)
                sta = shell_cmd('mdadm -f /dev/md0 /dev/' + item, True, 1)
                if sta != 0:
                    tips('failed')
                else:
                    tips('ok')

            sta = shell_cmd('mdadm -S /dev/md0', True, 1)
            if sta != 0:
                error('stop md0 failed, nothing to do !')
                error('Note: ============================> You can reboot system, and try it again !!!')
                quit(1, 'quit')

    print 'clean raid disk info ...'
    disk_str = ''
    sys_disk = check_ava_disk()
    if sys_disk:
        tmp_disk_list = []
        for item in sys_disk:
            tmp_disk_list.append('/dev/' + item)
        disk_str = ' '.join(tmp_disk_list)
    status = shell_cmd('mdadm --zero-superblock ' + disk_str, True, 1)
    if status == 0:
        tips('success')

    # clean persistence config file
    status = shell_cmd('rm -f /opt/system/etc/mdadm.conf', True, 1)
    if status == 0:
        tips('clean /opt/system/etc/mdadm.conf ok')

    quit(0, 'bye ...')
###############################################################################
###############################################################################
###############################################################################

############################ Main Process #####################################

param_len = len(sys.argv)
param = ''
if param_len != 2:
    usage_help()
else:
    param = sys.argv[1]
if not param in ['start', 'stop', 'delete', 'build']:
    usage_help()

if param == 'start':
    start_raid()
elif param == 'stop':
    stop_raid()
elif param == 'delete':
    delete_raid()
else:
    print 'Prepareing build raid now ...'

# quit(0, 'test...')

print 'Checking user ...'
is_root = check_user()
if not is_root:
    error('Only root user can do this !')
    quit(1)
###############################################################################

print 'Checking has builded raid device or not ...'
has_raid = has_raid_aleady()
# has_raid = False                                            # here, test ...
if has_raid:
    warning('Warnning: has builded RAID device /dev/md0')

    print 'checking mount raid device ? ...'
    out = shell_cmd('df -h | grep md0 | wc -l', True, 2)
    if out.strip() != '0':  # has mounted
        tips('has mounted')
        mounted_point = shell_cmd('df -h | grep md0 | awk \'{ print $6 }\'', True, 2)
        if mounted_point:
            print 'try to umount the raid device ...'
            status = shell_cmd('umount ' + mounted_point, True, 1)
            if status == 0:
                tips('success')
            else:
                warning('umount raid failed, maybe some program is using the mount point ' + mounted_point)
                print 'call professional guy to solve this problem !'
                quit(0, 'bye ...')
        else:
            warning('cannot find valid mount point !')
            print 'call professional guy to solve this problem !'
            quit(0, 'bye ...')
    print 'try to stop the old raid ...'
    status = shell_cmd('mdadm -Ss', True, 1)
    if status == 0:
        tips('stop success')
    else:
        warning('stop failed')
        warning('call professional guy to solve problem ...')
        quit(1, 'bye ...')
else:
    log('not raid')

#quit(0, 'test ...')
###############################################################################

print 'Checking system available disk ...'
disk_volume = '500G'  # default vol
sys_disk = check_ava_disk()
if sys_disk:
    log('System available disk are: [' + ' '.join(sys_disk) + ']')

    if len(sys_disk) < 3:
        error('RAID must give 3 disks to builded, quit !')

    print 'Stop mdadm device ...'
    status, stdout, stderr = shell_cmd('mdadm -Ss')
    if stdout:
        log(stdout.strip())
    if stderr:
        log(stderr.strip())

    print 'clear the super block ...'
    super_disk = ''
    for item in sys_disk:
        super_disk += '/dev/' + item + ' '
    clear_super_cmd = 'mdadm --zero-superblock ' + super_disk
    status, stdout, stderr = shell_cmd(clear_super_cmd)
    if stdout:
        log(stdout.strip())
    if stderr:
        log(stderr.strip())

    print 'Checking Xfs tools ...'
    status = shell_cmd('which mkfs.xfs', True, 1)
    if status != 0:  # not install tools
        status, stdout, stderr = shell_cmd('yum -y install xfsprogs xfsprogs-devel xfsdump kmod-xfs')
        if stdout or stderr:
            print stdout
            print stderr
        if status != 0:
            error('YUM error: install XFS tools failed')
            quit(1, 'quit ...')
    # checking again
    status = shell_cmd('which mkfs.xfs', True, 1)
    if status != 0:
        error('install XFS system tools failed, quit ...')
        quit(1, 'bye')

    # check disk volume
    invalid_vol = check_disk_volume(sys_disk)
    disk_volume = '%dG' % invalid_vol

    agree = get_teminal_input('Do you want to clear partition info ? [ y | n ]', ['y', 'n'], 'y')
    if agree == 'n':
        quit(0, 'bye')
    elif agree == 'y':
        log('Prepareing to clear partition info, wait some seconds ...')
        time.sleep(2)
        # quit(1, 'test ...')

        for item in sys_disk:
            print 'clear partition info disk : ' + item + ' ...'
            print 'start time :' + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            status, stdout, stderr = shell_cmd('parted -s /dev/' + item + ' mklabel gpt')
            print 'end time :' + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            if stdout:
                print 'out data : ' + stdout.strip()
            if stderr:
                print 'error data: ' + stderr.strip()
            if status == 0:
                log('ok')
            else:
                log('failed')

        log('Prepareing to partition the disk, wait some seconds ...')
        time.sleep(2)
        # disk_volume = '500M'                        # defined first partition volume
        for item in sys_disk:
            print 'parting the disk ' + item + ' ...'
            status, stdout, stderr = shell_cmd('parted -s /dev/'+ item +' mkpart primary 0 ' + disk_volume)
            if status == 0:
                log('ok')
            else:
                log('failed, quit ...')
                quit(1, 'bye')

        log('Prepareing to format the first partition, wait some seconds ...')
        time.sleep(2)
        for item in sys_disk:
            print 'formating the disk ' + item + '1 ...'
            format_disk_cmd = 'mkfs.xfs -f /dev/' + item + '1 &'
            log(format_disk_cmd)
            status, stdout, stderr = shell_cmd(format_disk_cmd)
            if status == 0:
                log('ok')
            else:
                log('failed, quit ...')
                quit(1, 'bye')
else:
    warning('Not find any system disk ...')
    print 'Reseting the RAID Udev config file ...'
    ret_udev = save_udev_config()
    if ret_udev:
        log('success')
        log('tips: if first run build script, try to reboot the system ...')
        quit(0, 'try to reboot system !!!')
    else:
        quit(1, 'config the udev rules failed, quit !!!')
    quit(1, 'quit ...')

###############################################################################

print 'Checking available disk partition ...'
ava_disk = availabel_disk_partition()
if ava_disk:
    log('The available partition are: [ ' + ' '.join(ava_disk) + ']')
else:
    warning('No available partition in system ! exit ...')
    quit(1, 'quit ...')

###############################################################################

agree = get_teminal_input('Do you want them join in RAID ? [ y | n ]', ['y', 'n'], 'y')
if agree == 'n':
    quit(0, 'bye')
elif agree == 'y':
    log('Now, Prepareing to build RAID device, Pls wait ...')

raid_type = get_teminal_input('Now, choose raid type ? [ 0 | 1 | 5 ]', ['0','1', '5'], '5')
if raid_type in ['0', '1']:
    warning('Oh, raid0 and raid1 type, not support, exit ...')

    # todo ...

elif raid_type == '5':
    print 'Prepare to build the raid, do not stop this script !!!'
    log('building ...')
    ret_build = init_raid_device(raid_type, 'md0', ava_disk)
    if ret_build:
        log('building success')
    else:
        error('building error')
        quit(1, 'quit ...')

# make md0 to gpt partition
status = shell_cmd('parted -s /dev/md0 mklabel gpt', True, 1)
if status != 0:
    error('make md0 to gpt partition, failed')
    quit(1, 'quit ...')

# formating the raid device
print 'RAID format to Xfs file system ...'
status = shell_cmd('mkfs.xfs -f /dev/md0 &', True, 1)
if status == 0:
    log('congratulations, raid is working ok ^_^')
else:
    warning('oh, maybe something was wrong ...')
    warning('You can call wangdiwen to solve problem, bye')


print ''
print '\t################### Auto Building RAID Machine ###################\n'
