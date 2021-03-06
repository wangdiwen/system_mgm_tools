#!/usr/bin/python2.7

import web
import json
import re
import os, string, shutil
import time
import threading

from common import invoke_shell
from common.restfulclient import RestfulError

from common.global_helper import *  # public helper functions
from model.log.log import RestLog

urls = (
    '', 'Raid',
    '/(.*)', 'RaidExt'
)
###############################################################################

def has_raid_started():
    started = False
    shell = 'timeout 3 mdadm -D /dev/md0'
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        started = True
    return started

def available_system_disk():
    data = []

    shell = 'timeout 3 ls /dev/ | grep disk_[0-9]$'
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        for dev in stdout.split("\n"):
            data.append(dev)
    # print data

    meta = get_meta_data()
    raid_meta = meta['raid']
    has_used_disk = raid_meta['device']
    mod_used_disk = []
    for disk in has_used_disk:
        mod_used_disk.append(disk[0:6])
    # print mod_used_disk

    for new_dev in list(data):
        if new_dev in mod_used_disk:
            data.remove(new_dev)
    return data

def raid_base_info():
    data = {}
    dev = '/dev/md0'
    cmd = 'timeout 3 mdadm -D ' + dev
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        list_all = []
        for line in stdout.split("\n"):
            if line:
                if re.compile("^[0-9]+").match(line.strip()):
                    # print line
                    tmp_dict = {}
                    items = line.strip().split()
                    len_item = len(items)
                    # print items
                    tmp_dict['number'] = items[0]
                    tmp_dict['major'] = items[1]
                    tmp_dict['minor'] = items[2]
                    tmp_dict['raiddevice'] = items[3]
                    if len_item > 5:
                        tmp_dict['status'] = string.join(items[4:len_item])
                    else:
                        tmp_dict['status'] = items[4]
                    list_all.append(tmp_dict)
                else:
                    tmp_list = line.split(" : ")
                    length = len(tmp_list)
                    if length == 2:
                        # print tmp_list[0].strip().lower()
                        data[tmp_list[0].strip().lower()] = tmp_list[1].strip()
        data['devices'] = list_all
    if data:
        data['device name'] = dev
        # 'chunk size' and 'layout' and 'used dev size'
        if not 'used dev size' in data.keys():
            data['used dev size'] = ''
        if not 'chunk size' in data.keys():
            data['chunk size'] = ''
        if not 'layout' in data.keys():
            data['layout'] = ''
    return data

def status_info():
    data = {}
    raid_info = raid_base_info()
    if not raid_info:
        # raise RestfulError('580 Error: RAID device stop working !')
        # try to start the raid
        sta, out, err = invoke_shell('timeout 3 mdadm -As')
        if sta != 0:
            print 'try to start raid, failed'
        if err or out:
            print out.strip()
            print err.strip()
        return {}

    data['device name'] = raid_info['device name']

    raid_disk = raid_info['devices']
    if raid_disk:
        for disk in raid_disk:
            disk_status = disk['status']
            tmp_list = disk_status.split(' ')
            if len(tmp_list) > 1:
                status = tmp_list[0]
                dev_name = tmp_list[-1].split('/')[-1]

                if status == 'active':
                    data[dev_name] = 'A'
                elif status == 'spare':
                    data[dev_name] = 'S'
                elif status == 'faulty':
                    data[dev_name] = 'F'

    tmp_data = {}
    # raid -> disk map data
    raid2disk_map = raid_disk_map()
    map_keys = raid2disk_map.keys()
    rule = re.compile('^sd')
    cur_raid_disk_list = data.keys()

    for item in map_keys:
        if rule.match(raid2disk_map[item]) and raid2disk_map[item] in cur_raid_disk_list:
            tmp_data[item] = data[raid2disk_map[item]]
    return tmp_data

def get_force_removed():
    meta = get_meta_data()
    raid_meta = meta['raid']
    raid_list = raid_meta['device']

    # get cur raid disk list
    cur_disk_list = []
    cur_staus_info = status_info()
    cur_staus_info_keys = cur_staus_info.keys()
    rule = re.compile('^disk_')
    for item in cur_staus_info_keys:
        if rule.match(item):
            cur_disk_list.append(item + '1')

    # filter the data
    for dev in list(raid_list):
        if dev in cur_disk_list:
            raid_list.remove(dev)
    return raid_list

def alarm_info():
    data = '0'
    has_started = has_raid_started()
    if not has_started:
        return '3'

    # checking disk faulty, md0 cannot work
    raid_info = raid_base_info()
    if not raid_info:               # {}, md0 not start
        return '3'

    state = raid_info['state'].strip()

    # just failed 1 device, or check other status info
    if 'failed devices' in raid_info.keys() \
        and raid_info['failed devices'] != '0':
        data = '1'
    else:
        if re.compile('.*recovering.*').match(state) \
                or re.compile('.*reshaping.*').match(state) \
                or re.compile('.*rebuilding.*').match(state):
            data = '4'

    # check raid is can work or not
    # here, removed or bad 2 disk, raid maybe not working when restart
    if state == 'clean, FAILED':
        data = '5'
    else:
        # checking has force removed disk, this situation is most important
        force_removed_disk_list = get_force_removed()
        # print force_removed_disk_list
        if len(force_removed_disk_list) >= 1:
            data = '2'

    return data

def new_raid_manager():
    # print 'getting raid status ...'
    has_started = has_raid_started()
    if not has_started:
        return ''
    return RaidExt.new_raid_data

def new_raid_refresh_status():
    # print 'raid monitor ...'
    # checking md start or not
    has_started = has_raid_started()
    if not has_started:
        return {}

    disk_status_map = status_info()
    cur_disk_list = disk_status_map.keys()
    sys_disk_list = system_disk_list()

    raid_config_disk_list = []
    meta = get_meta_data()
    raid_meta = meta['raid']
    for item in raid_meta['device']:
        raid_config_disk_list.append(item[0:6])

    print 'cur_disk_list ==> ' + ' '.join(cur_disk_list)
    print 'sys_disk_list ==> ' + ' '.join(sys_disk_list)
    print 'raid_config_disk_list ==> ' + ' '.join(raid_config_disk_list)

    global_raid_data = RaidExt.new_raid_data
    for key in global_raid_data.keys():
        # print '===================='
        device = global_raid_data[key]['device']
        status = global_raid_data[key]['status']
        grade_1 = '0'
        grade_2 = '0'
        RaidExt.new_raid_data[key]['state'] = 'not found'

        # checking the status of per disk
        is_in_raid = True if device in raid_config_disk_list else False
        is_in_sys = True if device in sys_disk_list else False
        if is_in_raid:
            grade_1 = '1'
            # checking grade 2 status
            if device in cur_disk_list:
                cur_status = disk_status_map[device]  # A, S, F
                if cur_status in ['A', 'S']:  # normal
                    grade_2 = '1'
                    if cur_status == 'A':
                        RaidExt.new_raid_data[key]['state'] = 'active sync'
                    elif cur_status == 'S':
                        RaidExt.new_raid_data[key]['state'] = 'spare rebuilding'
                elif cur_status == 'F':         # faulty
                    grade_2 = '2'
                    RaidExt.new_raid_data[key]['state'] = 'faulty'
            elif is_in_sys:
                grade_2 = '3'
                RaidExt.new_raid_data[key]['state'] = 'removed'
            else:
                grade_2 = '4'
                RaidExt.new_raid_data[key]['state'] = 'removed'
        elif is_in_sys:
            grade_1 = '2'
            # checking cur disk has skip or not
            pre_disk_key = int(key) - 1
            if pre_disk_key > 0:
                pre_disk = global_raid_data[str(pre_disk_key)]['device']
                is_pre_disk_in_sys = True if pre_disk in sys_disk_list else False
                if not is_pre_disk_in_sys:
                    grade_2 = '1'
                    RaidExt.new_raid_data[key]['state'] = 'new device'
        else:
            grade_1 = '3'

        status = grade_1 + grade_2  # change the status of each disk
        RaidExt.new_raid_data[key]['status'] = status
        # print device
        # print status
        # print '===================='
    # update the scsi info
    ret = new_update_scsi_num()
    return global_raid_data

def new_raid_test():
    time.sleep(5)
    return 'ok'

def raid_stop():
    shell = 'timeout 5 mdadm -Ss'
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        return True
    else:
        # try to stop raid not use config file
        shell_try = 'timeout 5 mdadm -S /dev/md0'
        sta, out, err = invoke_shell(shell_try)
        if sta == 0:
            return True
    return False

def raid_start():
    # check has started or not
    has_started = has_raid_started()
    if has_started:
        raise RestfulError('580 Error: Raid has started !')

    shell = 'timeout 5 mdadm -As'
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        return True
    else:
        # try to not use conf to start the raid
        meta = get_meta_data()
        raid_meta = meta['raid']
        raid_disk = raid_meta['device']
        if raid_disk:
            new_disk = []
            for dev in raid_disk:
                new_disk.append('/dev/' + dev)
            shell_try = 'timeout 5 mdadm -A /dev/md0 ' + ' '.join(new_disk)
            sta, out, err = invoke_shell(shell_try)
            if sta == 0:
                # update the config file '/etc/mdadm.conf'
                temp_conf = template_name('mdadm.conf')
                map_dict = {
                    'DEVICE': ' '.join(new_disk)
                }
                run_file = '/etc/mdadm.conf'
                ret_render = engine_render_template(temp_conf, map_dict, run_file)
                ret_sync = sync_run_config_file(run_file)
                if ret_render:
                    shell_add = 'mdadm -Ds >> /etc/mdadm.conf'
                    sta, out, err = invoke_shell(shell_add)

                return True
    return False

def raid_disk_map():
    data = {}
    status, stdout, stderr = invoke_shell('timeout 5 ls -l /dev/disk_* | awk \'{ print $9,$11 }\' | awk -F/ \'{ print $3 }\' | grep -v grep | grep "^disk_[0-9][0-9]"')
    if status == 0:
        # print stdout
        for line in stdout.split("\n"):
            tmp_list = line.split(' ')
            # print tmp_list
            if len(tmp_list) >= 2:
                data[tmp_list[0][0:6]] = tmp_list[1]
    return data

def disk_raid_map():
    data = {}
    status, stdout, stderr = invoke_shell('timeout 5 ls -l /dev/disk_* | awk \'{ print $9,$11 }\' | awk -F/ \'{ print $3 }\' | grep -v grep | grep "^disk_[0-9][0-9]"')
    if status == 0:
        # print stdout
        for line in stdout.split("\n"):
            tmp_list = line.split(' ')
            # print tmp_list
            if len(tmp_list) >= 2:
                data[tmp_list[1]] = tmp_list[0][0:6]
    return data

def system_disk_list():
    data = []
    status, stdout, stderr = invoke_shell('timeout 5 ls -l /dev/disk_* | awk \'{ print $9,$11 }\' | awk -F/ \'{ print $3 }\' | grep -v grep | grep "^disk_[0-9] sd"')
    if status == 0:
        for line in stdout.split("\n"):
            tmp_list = line.split(' ')
            if len(tmp_list) >= 2:
                data.append(tmp_list[0])
    return data

def remove_faulty_dev(dev_name):  # disk_1
    if not dev_name:
        raise RestfulError('580 Error: no faulty dev name')

    dev_name = dev_name + '1'  # revise the partition disk like: disk_11

    # checking cur raid status, if status is recovering, not add new disk to raid
    raid_status = raid_base_info()
    if not raid_status:  # {}, md0 not start
        raise RestfulError('580 Warnning: Raid maybe not started !')
        return False

    cur_status = raid_status['state']
    if re.compile('.*recovering.*').match(cur_status) \
        or re.compile('.*reshaping.*').match(cur_status):
        raise RestfulError('580 Warnning: Raid is rebuilding, cannot force remove disk')
        return False

    faulty_dev_list = []
    raid_status_info = status_info()  # like 'disk_1' => 'F/A/S'
    for key in raid_status_info.keys():
        if raid_status_info[key] == 'F':
            faulty_dev_list.append(key + '1')

    # remove the faulty disk
    # first, set the disk faulty
    set_cmd = 'timeout 5 mdadm -f /dev/md0 /dev/' + dev_name
    status, stdout, stderr = invoke_shell(set_cmd)
    print 'set the disk faulty ' + dev_name
    print set_cmd
    if stderr:
        print stderr.strip()

    print 'remove faulty disk ...'
    shell = 'timeout 5 mdadm -r /dev/md0 /dev/' + dev_name
    print shell
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        # remember the lastest faulty remove disk name
        RaidExt.faulty_disk_name = dev_name[0:6]

        print 'stop this scsi disk ' + dev_name
        ret = stop_scsi_disk(dev_name[0:6])
        if not ret:
            raise RestfulError('580 Error: stop scsi disk failed')
        return True
    else:
        if stderr:
            raise RestfulError('580 Error: ' + stderr.strip())
    return False

def active_new_disk(dev_name):  # like 'disk_1'
    # this function just for 'remove_faulty_dev' func
    is_started = has_raid_started()
    if not is_started:
        raise RestfulError('580 Error: Raid has not started')

    # checking cur raid disk volume, just '500' or '1000' or '2000'
    invalid_vol = check_new_disk_vol(dev_name)  # unit is 'G'
    if invalid_vol == 0:   # new disk is lower
        raise RestfulError('580 Error: New disk volume is too lower, cannot support')
        return False

    # checking parted tool process
    status, stdout, stderr = invoke_shell('ps -ef | grep parted | grep -v grep')
    if status != 0:  # has process id
        # find pid and kill them all
        status, stdout, stderr = invoke_shell('ps -ef | grep parted | grep -v grep | awk \'{ print $2 }\' | xargs kill -9')

    # 1, clear old partition info
    clear_partion_cmd = 'parted -s /dev/' + dev_name + ' mklabel gpt &'
    print clear_partion_cmd
    status, stdout, stderr = invoke_shell(clear_partion_cmd)
    if status == 0:
        time.sleep(1)
        # 2, part new partition again
        disk_volume = '%dG' % invalid_vol  # 500G or 1000G
        new_part_cmd = 'parted -s /dev/'+ dev_name +' mkpart primary 0 ' + disk_volume
        print new_part_cmd
        status, stdout, stderr = invoke_shell(new_part_cmd)
        if status == 0:
            time.sleep(1)
            # checking mkfs.xfs tool has exist ?\
            status, stdout, stderr = invoke_shell('which mkfs.xfs')
            if status != 0:
                raise RestfulError('580 Error: system has no mkfs.xfs tool 1')

            # 3, format the new partition
            for_cmd = 'mkfs.xfs -f /dev/' + dev_name + '1 &'
            status, stdout, stderr = invoke_shell(for_cmd)
            time.sleep(1)
            if status == 0:
                # print 'format new partition success'
                ###################### Here, resolve the 'device or resource busy' problem ###################3
                # Note: helpful url http://dev.bizo.com/2012/07/mdadm-device-or-resource-busy.html

                #################################
                # shutdown the udev monitor queue
                status, stdout, stderr = invoke_shell('udevadm control --stop-exec-queue')
                if status != 0:
                    RestLog.debug('add_spare_disk: [udevadm control --stop-exec-queue] failed')

                # 2, add to md0
                sta, out, err = invoke_shell('mdadm -a /dev/md0 /dev/' + dev_name + '1')
                if sta == 0:
                    ###################################
                    # open the udev monitor queue again
                    status, stdout, stderr = invoke_shell('udevadm control --start-exec-queue')
                    if status != 0:
                        RestLog.debug('add_spare_disk: [udevadm control --start-exec-queue] failed')

                    # clear the lastest faulty disk record
                    RaidExt.faulty_disk_name = ''
                    # save the cur raid config
                    # get raid meta
                    meta = get_meta_data()
                    raid_meta = meta['raid']

                    # save the etc conf
                    tmp_dev_list = []
                    for item in raid_meta['device']:
                        tmp_dev_list.append('/dev/' + item)

                    device_str = ' '.join(tmp_dev_list)
                    temp_conf = template_name('mdadm.conf')
                    map_dict = {
                        'DEVICE': device_str
                    }
                    run_file = '/etc/mdadm.conf'
                    ret_render = engine_render_template(temp_conf, map_dict, run_file)
                    ret_sync = sync_run_config_file(run_file)
                    if ret_render:
                        shell_add = 'mdadm -Ds >> /etc/mdadm.conf'
                        sta, out, err = invoke_shell(shell_add)

                    # here, update_scsi_num id
                    # ret = update_scsi_num(dev_name)
                    ret = new_update_scsi_num()
                    # here, raise md0 XFS filesystem
                    ret = resize_raid_fs()
                    return True
                else:
                    # print out.strip()
                    # print err.strip()
                    raise RestfulError('580 Error: ' + out.strip() + ' ' + err.strip())
            else:
                raise RestfulError('580 Error: format new partition failed')
        else:
            raise RestfulError('580 Error: part new partition failed')
    else:
        raise RestfulError('580 Error: clear partition info failed')

    return False

def check_new_disk_vol(dev_name):
    raid_vol = '500'
    cur_vol = '500'  # default minor vol

    remove_disk_name = RaidExt.faulty_disk_name  # like: disk_1
    child_disk_name = remove_disk_name + '1'  # like: disk_11
    # get cur raid conf
    meta = get_meta_data()
    raid_meta = meta['raid']
    cur_raid_disk_list = raid_meta['device']
    for item in list(cur_raid_disk_list):
        if item == child_disk_name:
            cur_raid_disk_list.remove(item)
    # filter the removed disk and get other ok disk name
    if not cur_raid_disk_list:
        raise RestfulError('580 Error: deadly error, cannot find valid first disk partition, in check_new_disk_vol() function !!')
    other_child_disk_name = cur_raid_disk_list[0]  # get default other list ones

    status, stdout, stderr = invoke_shell('parted -s /dev/'+ other_child_disk_name[0:6] +' print | grep "^[ 0-9]" | awk \'{ print $4 }\'')
    if status == 0 and stdout:
        cur_vol = stdout.strip()
        cur_vol = cur_vol[0:-2]
    status, stdout, stderr = invoke_shell('parted -s /dev/' + dev_name + ' print | grep ^Disk | awk \'{ print $3 }\'')
    if status == 0 and stdout:
        raid_vol = stdout.strip()
        raid_vol = raid_vol[0:-2]
    diff = int(cur_vol) - int(raid_vol)
    if diff >= 0:
        return int(raid_vol)
    else:
        return 0

def add_spare_disk(dev_name):                   # like: disk_1
    available_disk = available_system_disk()
    # print 'available_disk ...'
    # print available_disk
    if not dev_name in available_disk:
        raise RestfulError('580 Error: no disk device')

    is_started = has_raid_started()
    if not is_started:
        raise RestfulError('580 Error: Raid has not started')
        return False

    # checking cur raid status, if status is recovering, not add new disk to raid
    raid_status = raid_base_info()
    if not raid_status:  # {}, md0 not start
        raise RestfulError('580 Warnning: RAID maybe not started !')
        return False

    cur_status = raid_status['state']
    if re.compile('.*recovering.*').match(cur_status) or re.compile('.*reshaping.*').match(cur_status):
        raise RestfulError('580 Warnning: Raid is rebuilding, cannot add new disk')
        return False

    # checking cur raid disk volume, just '500' or '1000' or '2000'
    invalid_vol = check_new_disk_vol(dev_name)  # unit is 'G'
    if invalid_vol == 0:   # new disk is lower
        raise RestfulError('580 Error: New disk volume is too lower, cannot support')
        return False

    # checking parted tool process
    status, stdout, stderr = invoke_shell('ps -ef | grep parted | grep -v grep')
    if status != 0:  # has process id
        # find pid and kill them all
        status, stdout, stderr = invoke_shell('ps -ef | grep parted | grep -v grep | awk \'{ print $2 }\' | xargs kill -9')

    # 1, clear old partition info
    status, stdout, stderr = invoke_shell('parted -s /dev/' + dev_name + ' mklabel gpt &')
    if status == 0:
        time.sleep(1)
        # 2, part new partition again
        disk_volume = '%dG' % invalid_vol  # 500G or 1000G
        status, stdout, stderr = invoke_shell('parted -s /dev/'+ dev_name +' mkpart primary 0 ' + disk_volume)
        if status == 0:
            time.sleep(1)
            # checking mkfs.xfs tool has exist ?\
            status, stdout, stderr = invoke_shell('which mkfs.xfs')
            if status != 0:
                raise RestfulError('580 Error: system has no mkfs.xfs tool 1')

            # 3, format the new partition
            for_cmd = 'mkfs.xfs -f /dev/' + dev_name + '1 &'
            status, stdout, stderr = invoke_shell(for_cmd)
            time.sleep(1)
            if status == 0:
                print 'format new partition success'
            else:
                raise RestfulError('580 Error: format new partition failed')
        else:
            raise RestfulError('580 Error: part new partition failed')
    else:
        raise RestfulError('580 Error: clear partition info failed')

    # get raid meta
    meta = get_meta_data()
    raid_meta = meta['raid']

    ###################### Here, resolve the 'device or resource busy' problem ###################3
    # Note: helpful url http://dev.bizo.com/2012/07/mdadm-device-or-resource-busy.html

    #################################
    # shutdown the udev monitor queue
    status, stdout, stderr = invoke_shell('udevadm control --stop-exec-queue')
    if status != 0:
        RestLog.debug('add_spare_disk: [udevadm control --stop-exec-queue] failed')

    shell = 'mdadm -G /dev/md0 -a -n %d %s' % (raid_meta['count'] + 1, '/dev/' + dev_name + '1')
    status, stdout, stderr = invoke_shell(shell)
    if status == 0:
        ###################################
        # open the udev monitor queue again
        status, stdout, stderr = invoke_shell('udevadm control --start-exec-queue')
        if status != 0:
            RestLog.debug('add_spare_disk: [udevadm control --start-exec-queue] failed')

        raid_meta['count'] = raid_meta['count'] + 1
        raid_meta['device'].append(dev_name + '1')
        # save raid meta
        ret_save = set_meta_data(meta)
        if ret_save:
            # save the etc conf
            tmp_dev_list = []
            for item in raid_meta['device']:
                tmp_dev_list.append('/dev/' + item)

            device_str = ' '.join(tmp_dev_list)
            temp_conf = template_name('mdadm.conf')
            map_dict = {
                'DEVICE': device_str
            }
            run_file = '/etc/mdadm.conf'
            ret_render = engine_render_template(temp_conf, map_dict, run_file)
            if ret_render:
                shell_add = 'mdadm -Ds >> /etc/mdadm.conf'
                sta, out, err = invoke_shell(shell_add)
            ret_sync = sync_run_config_file(run_file)

        # here, update_scsi_num id ...
        # ret = update_scsi_num(dev_name)
        ret = new_update_scsi_num()
        # here, resize the md0 XFS file system
        ret = resize_raid_fs()
        return True
    else:
        if stderr:
            raise RestfulError('580 Error: ' + stderr.strip())
    return False

def stop_scsi_disk(dev_name):  # like: 'disk_1'
    global_raid_data = RaidExt.new_raid_data
    control_str = ''
    ret = False

    for key in global_raid_data.keys():
        device = global_raid_data[key]['device']
        if device == dev_name:
            control_str = global_raid_data[key]['scsi']
            break
    if control_str:
        shell = 'echo \"scsi remove-single-device '+ control_str +'\" > /proc/scsi/scsi'
        print shell
        sta, out, err = invoke_shell(shell)
        if sta == 0:
            ret = True
    else:
        raise RestfulError('580 Warnning: Not find valid scsi id, Maybe not stop the disk '+ dev_name)
    return ret

# Note:
#     1, old system disk is dom, so the 'proc/scsi' show scsi0 and scsi1;
#     2, now system is 60G KINGSTON disk, 'proc/scsi' info is scsi6 and scsi7;
def find_system_scsi_id_max(option = 0):  # option: 0 -> scsi6, 1 -> scsi7
    option = 6 if option == 0 else 7        # checking ...

    shell = 'cat /proc/scsi/scsi | grep scsi'+ str(option) +' | awk \'{ print $6 }\' | cut -c2'
    sta, out, err = invoke_shell(shell)
    if sta == 0 and out:
        tmp_num_list = []
        lines = out.split("\n")
        for item in lines:
            tmp_num_list.append(int(item))
        tmp_num_list.sort()
        max_num = tmp_num_list[-1]
        return max_num
    else:
        return -1

def update_scsi_num(dev_name):
    global_raid_data = RaidExt.new_raid_data
    cur_raid_key = ''

    # find scsi_master id
    num = dev_name[5]
    if num in ['1', '2', '3', '4']:
        scsi_master = '0'
    else:
        scsi_master = '1'
    # find scsi_id
    for key in global_raid_data.keys():
        device = global_raid_data[key]['device']
        if device == dev_name:
            cur_raid_key = key
            break
    # here, find current system scsi_id max num
    system_scsi_id_max = find_system_scsi_id_max(int(scsi_master))
    update_num = ''

    # update this position scsi id, find the scsi_master max num+1
    if cur_raid_key != '':
        scsi_num_list = []
        tmp_num_list = []
        if scsi_master == '0':
            tmp_num_list = ['1','2','3','4']
        else:
            tmp_num_list = ['5','6','7','8']
        for num in tmp_num_list:
            raid_obj = global_raid_data[num]
            if raid_obj['scsi']:
                scsi_num_list.append(raid_obj['scsi'])
        if scsi_num_list:
            scsi_num_list.sort()
            max_num = scsi_num_list[-1]
            update_num = str(int(max_num) + 1)
        else:
            update_num = '0'
        # special here
        # if found when computer scsi_id > current system scsi_id, then not update
        if system_scsi_id_max != -1 and update_num != '' and int(update_num) <= system_scsi_id_max:
            RaidExt.new_raid_data[cur_raid_key]['scsi'] = update_num
        return True
    return False

def new_update_scsi_num():
    global_raid_data = RaidExt.new_raid_data
    sd_to_disk = disk_raid_map()  # item like: 'sdf1 disk_1'

    # clear cur raid scsi info
    for item in global_raid_data.keys():
        global_raid_data[item]['scsi'] = ''

    raid_base = raid_base_info()
    if not raid_base:  # {}, md0 not start
        return False

    device_info = raid_base['devices']
    for dev in device_info:
        status = dev['status']
        tmp_list = status.split(" ")
        disk_name = tmp_list[-1]
        tmp_list = disk_name.split("/")
        disk_name = tmp_list[-1]            # like: sdf1

        major_id = dev['major']
        minor_id = dev['minor']
        dev_id_str = major_id + ':' + minor_id      # like: '8:81'

        # find scsi id info
        scsi_id_str = ''
        devpath_info_cmd = 'udevadm info --query=all --path=/dev/block/'+ dev_id_str +' | grep DEVPATH'
        status, stdout, stderr = invoke_shell(devpath_info_cmd, True)
        if status == 0 and stdout:
            tmp_list = stdout.split("/")
            tmp_str = tmp_list[-4]
            tmp_list = tmp_str.split(":")
            scsi_id_str = ' '.join(tmp_list)

        # set global_raid_data -> scsi flag
        if scsi_id_str != '' and disk_name and sd_to_disk:
            disk_key = sd_to_disk[disk_name] if disk_name in sd_to_disk.keys() else ''
            if disk_key:
                for key in global_raid_data.keys():
                    dev_name = global_raid_data[key]['device']
                    if dev_name == disk_key:
                        RaidExt.new_raid_data[key]['scsi'] = scsi_id_str
                        break
    return True

def resize_raid_fs():
    # check has started or not
    has_started = has_raid_started()
    if not has_started:
        raise RestfulError('580 Error: Raid has not started !')

    status, stdout, stderr = invoke_shell('xfs_growfs /dev/md0', True)
    # if stderr:
    #     raise RestfulError('580 Warnning: You can ignore this alarm ! ' + stderr.strip().replace("\n", ' '))
    if status == 0:
        return True
    return False

def raid_sync_progress():
    progress = '100%'
    status, stdout, stderr = invoke_shell('timeout 5 cat /proc/mdstat | grep finish | head -n 1 | awk \'{ print $4 }\'', True)
    if stdout:
        progress = stdout.strip()
    return progress
###############################################################################
class RaidMonitor(threading.Thread):
    def __init__(self, lock, thread_name):
        super(RaidMonitor, self).__init__(name=thread_name)
        self.lock = lock

    def run(self):
        while True:
            # self.lock.acquire()         # add lock
            ret = new_raid_refresh_status() # refresh the raid disk status
            # self.lock.release()         # release lock
            time.sleep(3)

class ScsiMonitor():
    def __init__(self):
        pass
    def init_scsi_raid_map(self):
        global_raid_data = RaidExt.new_raid_data
        # init scsi0 devices
        status, stdout, stderr = invoke_shell('cat /proc/scsi/scsi | grep scsi6 | awk \'{ print $6 }\' | cut -c2')
        if status == 0 and stdout:
            lines = stdout.split("\n")  # like: 0,1,2,3
            length = len(lines)
            for item in [1, 2, 3, 4]:
                if item <= length:
                    global_raid_data[str(item)]['scsi'] = '6 0 ' + str(item - 1) + ' 0'
        # init scsi1 devices
        status, stdout, stderr = invoke_shell('cat /proc/scsi/scsi | grep scsi7 | awk \'{ print $6 }\' | cut -c2')
        if status == 0 and stdout:
            lines = stdout.split("\n")  # like: 0,1,2,3
            length = len(lines)
            for item in [5, 6, 7, 8]:
                if item <= length:
                    global_raid_data[str(item)]['scsi'] = '7 0 ' + str(item - 1) + ' 0'

        json_data = json.dumps(RaidExt.new_raid_data, indent = 4)
        print json_data
        shell = 'echo \"' + json_data + '\" > /opt/system/conf/restful-server/init_scsi_raid_map.log'
        status, stdout, stderr = shell_cmd(shell)
        return True

class Raid:
    def GET(self):
        base_info = raid_base_info()
        return json.dumps(base_info, indent = 4)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

class RaidExt:
    faulty_disk_name = ''  # remember the lastest remove faulty disk
    new_raid_data = {
        '1': {
            'device': 'disk_1',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '2': {
            'device': 'disk_2',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '3': {
            'device': 'disk_3',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '4': {
            'device': 'disk_4',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '5': {
            'device': 'disk_5',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '6': {
            'device': 'disk_6',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '7': {
            'device': 'disk_7',
            'status': '00',
            'state': '',
            'scsi': ''
        },
        '8': {
            'device': 'disk_8',
            'status': '00',
            'state': '',
            'scsi': ''
        }
    }

    def GET(self, arg):
        if arg == 'status':
            info = status_info()
            return json.dumps(info, indent = 4)
        elif arg == 'alarm':
            info = alarm_info()
            return info
        elif arg == 'spare':
            ava_disk = available_system_disk()
            return json.dumps(ava_disk, indent = 4)
        elif arg == 'removed':
            force_removed_disk = get_force_removed()
            return json.dumps(force_removed_disk, indent = 4)
        elif arg == 'perfect':
            return json.dumps(new_raid_manager(), indent = 4)
        elif arg == 'refresh':
            ret = new_raid_refresh_status()
            return json.dumps(ret, indent = 4)
        elif arg == 'test':
            ret = new_raid_test()
            return json.dumps(ret, indent = 4)
        elif arg == 'sync':
            return raid_sync_progress()
        return ''

    def PUT(self, arg):
        # web_data = web.data()
        # input_data = json.loads(web_data) if web_data else {}
        if arg == 'start':
            ret = raid_start()
            if ret:
                return 'start raid success'
            else:
                raise RestfulError('580 Error: start raid failed')
        elif arg == 'stop':
            ret = raid_stop()
            if ret:
                return 'stop raid success'
            else:
                raise RestfulError('580 Error: stop raid failed')
        elif arg == 'resizefs':
            ret = resize_raid_fs()
            if ret:
                return 'resize raid file system success'
            else:
                raise RestfulError('580 Error: resize raid file system failed')
        elif arg == 'active':
            web_data = web.data()
            input_data = json.loads(web_data) if web_data else {}
            if not 'active' in input_data.keys():
                raise RestfulError('580 Error: input data not has [active] field')

            ret = active_new_disk(input_data['active'])
            if ret:
                return 'active new replace disk success'
            else:
                raise RestfulError('580 Error: active new replace disk failed')
        return ''

    def POST(self, arg):
        if arg:
            ret = add_spare_disk(arg)
            if ret:
                return 'add new disk success'
            else:
                raise RestfulError('580 Error: add new disk failed')
        return ''

    def DELETE(self, arg):
        if arg:
            # ret = remove_faulty_dev(arg.strip())
            ret = stop_scsi_disk(arg.strip())
            if not ret:
                raise RestfulError('580 Error: remove faulty disk failed')
        return ''

app = web.application(urls, locals())
