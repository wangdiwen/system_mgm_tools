#!/usr/bin/python2.7

import json
import os, re, string
from M2Crypto.EVP import Cipher
import StringIO

def do_encrypt(in_file, out_file, encrypt_type):  # encrypt_type: 0->decrypt, 1->encrypt
    algorithm = 'bf_cbc'
    key = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
    iv = "\x01\x02\x03\x04\x05\x06\x07\x08"
    key_as_bytes = 0        # 0->use iv, 1->not use iv
    algo_method = 'md5'     # 'md5', 'sha1'
    salt = '12345678'
    iter_count = 1
    padding = 1

    if not os.path.isfile(in_file):
        print 'In file not exist, [' + in_file + ']'
        return False

    file = open(in_file, 'r')
    content = file.read()
    file.close()

    try:
        # constructor the EVP.Cipher obj
        cipher_obj = Cipher(algorithm, key, iv, encrypt_type, key_as_bytes, algo_method, salt, iter_count, padding)
        # use memory file obj
        out = StringIO.StringIO()
        out.write(cipher_obj.update(content))
        out.write(cipher_obj.final())
        encrypt_context = out.getvalue()

        file = open(out_file, 'w')
        file.write(encrypt_context)
        file.close()

    except Exception as e:
        print 'Oh, My God, Exception...'
        return False
    return True

def main():
    print ' ==================== ^_^ License Encrypt Small Tool ^_^ ==================='
    print ' ==================== Help: '
    print ' ==================== Do What Option: encrypt= 1, decrypt= 0 ==============='
    print ''

    while True:
        status = raw_input('Do you want to quit(y/n) ? ')
        if status == 'y' or status == 'y':
            break
        else:
            in_file = raw_input('In  File: ')
            out_file = raw_input('Out File: ')
            encrypt_type = raw_input('Do What: ')
            if not encrypt_type.isdigit():
                print 'Error: Do What must be 0/1'
                return
            en_type = int(encrypt_type)
            ret = do_encrypt(in_file, out_file, en_type)
            print ''
            if ret:
                print 'WOW, Success !!!'
            else:
                print 'Oh, Failed !!!'

# exec the program
main()
