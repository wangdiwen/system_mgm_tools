#!/usr/bin/python2.7

import httplib
import re, json

def program_tips():
    print ''
    print ' =========================================================='
    print '         RESTful API test program for python'
    print '          Developer: develop-3@vmediax.com'
    print '           Version : 2.7.0'
    print '              Date : 2013-05'
    print '             ^__^ Good Luck ^__^'
    print ' =========================================================='
    print ''

def auth_user(name, password):
    data = {}
    data['name'] = name
    data['passwd'] = password

    conn = httplib.HTTPConnection('127.0.0.1', 88)
    conn.request('POST', '/auth', json.dumps(data))
    res = conn.getresponse()
    if res.status != 200:
        return False
    else:
        return True

def http_request(method, url, params, user_name, user_passwd):
    headers = {}
    headers["Cookie"] = 'user_name=' + user_name + ';user_passwd=' + user_passwd + ';'
    # print headers["Cookie"]

    conn = httplib.HTTPConnection('127.0.0.1', 88)
    conn.request(method.upper(), url, params, headers)
    res = conn.getresponse()

    print ''
    print ' Respose Result'
    print ' =================================================================='
    print '      status : %d' % res.status
    print '      reason : ' + res.reason
    print '        body : ' + res.read()
    print ' =================================================================='
    print ''
    conn.close()

def handle_http():
    # global vars
    user_name = ''
    user_passwd = ''

    # user auth...
    print ' Now, Authentication ===>'
    while True:
        user_name = raw_input('               user name: ')
        user_passwd = raw_input('           user password: ')
        ret = auth_user(user_name, user_passwd)
        if ret:
            print ''
            print ' Authentication Success ^ _ ^'
            print ''
            break
        else:
            print ''
            print ' Authentication Failed @ _ @'
            print ''
            print ' Authentication Again ===>'
    print ''

    # handle http request...
    while True:
        method = 'get'
        url = ''
        params = ''

        print ' Pls input http request infomation:'
        method_input = raw_input('      Method [get, post, put, delete] (get): ')
        if method_input:
            if not re.compile("^(get|post|put|delete)$").match(method_input):
                method_input = raw_input(' Http method wrong, Pls input again: ')
            method = method_input
        url = raw_input("      URL: ")
        params = raw_input('      Data: ')

        http_request(method, url, params, user_name, user_passwd)

def main():
    program_tips()
    handle_http()

# exec the main program
main()
