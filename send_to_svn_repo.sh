#!/bin/bash

echo ''
echo 'send rest and web mgm tools to svn repo ...'
echo 'diwen -> diwen'
echo ''

echo '====== Trans restful ...'
rest_tool=`ls | grep -E "rest" | sort -r | head -n 1`
scp $rest_tool diwen@10.4.89.89:/home/diwen/work/github_base_system/update/tools
echo ''
[ "$?" == "0" ] && { echo 'sync rest tool, ok'; }

echo ''
echo '====== Trans web frontend ...'
web_tool=`ls | grep -E "web" | sort -r | head -n 1`
scp $web_tool diwen@10.4.89.89:/home/diwen/work/github_base_system/update/tools
echo ''
[ "$?" == "0" ] && { echo 'sync web tool, ok'; }
