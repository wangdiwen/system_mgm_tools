#!/usr/bin/python2.7

import web
import json
import os, re, string
from M2Crypto.EVP import Cipher
import StringIO

from common import invoke_shell
from common.restfulclient import RestfulError

urls = (
    '', 'License',
    '/(.*)', 'LicenseExt'
)

def do_encrypt(file_name, encrypt_type):  # encrypt_type: 0->decrypt, 1->encrypt
    algorithm = 'bf_cbc'
    key = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
    iv = "\x01\x02\x03\x04\x05\x06\x07\x08"
    key_as_bytes = 0        # 0->use iv, 1->not use iv
    algo_method = 'md5'     # 'md5', 'sha1'
    salt = '12345678'
    iter_count = 1
    padding = 1

    if not os.path.isfile(file_name):
        return ''

    file = open(file_name, 'r')
    content = file.read()
    file.close()

    try:
        # constructor the EVP.Cipher obj
        cipher_obj = Cipher(algorithm, key, iv, encrypt_type, key_as_bytes, algo_method, salt, iter_count, padding)

        # use memory file obj
        out = StringIO.StringIO()
        out.write(cipher_obj.update(content))
        out.write(cipher_obj.final())
        return out.getvalue()
    except Exception as e:
        return ''

def get_license_file():
    cmd = 'ls /opt/system/license'
    status, stdout, stderr = invoke_shell(cmd)
    if status == 0:
        file_list = stdout.strip().split()
        return file_list
    return []

def get_all_license():
    data = {}
    license_file_list = get_license_file()
    if license_file_list:
        for license_file in license_file_list:
            decrypt_content = do_encrypt('/opt/system/license/'+license_file, 0)
            if decrypt_content:
                lines = decrypt_content.strip().split("\n")
                if lines:
                    for line in lines:
                        if line:
                            key_value = line.split("=")
                            if len(key_value) >= 2:
                                data[key_value[0]] = key_value[1]
    return data

def get_by_key(key):
    data = {}
    all_license = get_all_license()
    if not key in all_license.keys():
        msg = '580 has no such gpg key [' + key + ']'
        raise RestfulError(msg)
    data[key] = all_license[key]
    return data

###############################################################################
class License():
    def GET(self):
        ret = get_all_license()
        return json.dumps(ret)

    def PUT(self):
        pass
    def POST(self):
        pass
    def DELETE(self):
        pass

class LicenseExt():
    def GET(self, arg):
        data = get_by_key(arg)
        return json.dumps(data)

    def PUT(self, arg):
        pass
    def POST(self, arg):
        pass
    def DELETE(self, arg):
        pass

app = web.application(urls, locals())
