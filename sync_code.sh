#!/bin/bash

echo 'sync restful and web code to /usr/local ...'
cp -a ./restful-server/* /usr/local/restful-server
cp -a ./web-frontend/* /usr/local/web-frontend/

echo 'ok'
