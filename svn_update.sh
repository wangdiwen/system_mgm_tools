#!/bin/bash

echo ''
echo 'SVN repo update ...'
echo 'diwen -> diwen'
echo ''

scp -r restful-server/* diwen@10.4.89.89:/home/diwen/work/base_system/restful-server
[ "$?" != "0" ] && {
	echo 'sync rest failed'
}
scp -r web-frontend/* diwen@10.4.89.89:/home/diwen/work/base_system/web-frontend
[ "$?" != "0" ] && {
	echo 'sync web frontend failed'
}

echo ''
echo 'update repo ok'
echo ''
