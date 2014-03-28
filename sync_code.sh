#!/bin/bash

echo 'sync restful and web code to /usr/local ...'
cp -a ./restful-server/* /usr/local/restful-server/
rm -f /usr/local/restful-server/restful-server
cp -a ./web-frontend/* /usr/local/web-frontend/

echo 'ok'

echo ''
echo 'restart the tools ...'
#/etc/init.d/restful-server restart
#/etc/init.d/web-frontend restart

