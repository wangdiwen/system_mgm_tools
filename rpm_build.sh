#!/bin/sh

###############################################################################
                    # Author : wangdiwen
                    # Date   : 2013-
                    # License: LGPL
                    # Note   : build the mgmtool, restful-server and web-frontend

                    # Keep It Simple and Stupid
###############################################################################

###############################################################################
                    # Public Functions
###############################################################################
# Note: echo color log
COLOR_RED=$( echo -e "\e[31;49m" )
COLOR_GREEN=$( echo -e "\e[32;49m" )
COLOR_YELLOW=$( echo -e "\e[33;49m" )
COLOR_BLUE=$( echo -e "\e[34;49m" )
COLOR_RESET=$( echo -e "\e[0m" )

log() { echo "$*"; }
tips() { echo "${COLOR_GREEN}$*${COLOR_RESET}"; }
info() { echo "${COLOR_BLUE}$*${COLOR_RESET}"; }
warning() { echo "${COLOR_YELLOW}$*${COLOR_RESET}"; }
error() { echo "${COLOR_RED}$*${COLOR_RESET}"; }
###############################################################################

###############################################################################
                    # Define Your Functions Here
###############################################################################

function usage() {
    cat << HELP
    Usge: ./rpm_build.sh -v <version, 1.3.9rc1>
          -h | --help for help
HELP
}

rpm_version=''
rpm_spec_path='./rpm_spec'

function set_rpm_version() {
    rpm_version=$1  # 1.3.9rc1
}

function build_rpm_pkg() {
    tips 'rpm version = <'$rpm_version'>'
    # checking version valid
    str_list=`echo "$rpm_version" | awk -F. '{ print $1,$2,$3 }'`
    arr=($str_list)
    ver_1=${arr[0]}
    ver_2=${arr[1]}
    ver_3=${arr[2]}
    [ -n "$ver_1" ] || { error 'version error !'; exit 1; }
    [ -n "$ver_2" ] || { error 'version error !'; exit 1; }
    [ -n "$ver_3" ] || { error 'version error !'; exit 1; }

    ver_major=$ver_1'.'$ver_2
    ver_minor=$ver_3'.el6'

    tips $ver_major
    tips $ver_minor

    # modify the spec file
    rest_spec=$rpm_spec_path'/restful-server.spec'
    web_spec=$rpm_spec_path'/web-frontend.spec'
    tips $rest_spec
    tips $web_spec
    [ -f $rest_spec ] || { error 'no restful-server spec'; exit 1; }
    [ -f $web_spec ] || { error 'no web-frontend spec'; exit 1; }

    echo 'modify the spec version and Release ...'
    sed -i "s/^Version: .*/Version: $ver_major/g" $rest_spec
    sed -i "s/^Release: .*/Release: $ver_minor/g" $rest_spec

    sed -i "s/^Version: .*/Version: $ver_major/g" $web_spec
    sed -i "s/^Release: .*/Release: $ver_minor/g" $web_spec

    # set the rpm build env
    which rpmbuild > /dev/null 2>&1
    [ "$?" != "0" ] && { error 'not rpmbuild tool, quit ...'; \
		echo -e "y\n" | yum install rpm-build; \ 
		exit 1; }

    tips 'set rpm build env to local /root ...'
    echo "%_topdir $HOME/rpmbuild" > ~/.rpmmacros
    [ "$?" == "0" ] && { tips 'set rpm build env, OK'; }

    tips 'create rpm dirs ...'
    [ -d $HOME/rpmbuild/BUILD ] || { mkdir -p $HOME/rpmbuild/BUILD; }
    [ -d $HOME/rpmbuild/RPMS ] || { mkdir -p $HOME/rpmbuild/RPMS; }
    [ -d $HOME/rpmbuild/SOURCE ] || { mkdir -p $HOME/rpmbuild/SOURCE; }
    [ -d $HOME/rpmbuild/SPECS ] || { mkdir -p $HOME/rpmbuild/SPECS; }
    [ -d $HOME/rpmbuild/SRPMS ] || { mkdir -p $HOME/rpmbuild/SRPMS; }

    tips "sync spec file [restful-server and web-frontend] to $HOME/rpmbuild/SPECS ..."
    cp -a $rest_spec $HOME/rpmbuild/SPECS
    cp -a $web_spec $HOME/rpmbuild/SPECS

    tips 'sync src code ...'
    cp -a ./restful-server $HOME/rpmbuild/BUILD
    cp -a ./web-frontend $HOME/rpmbuild/BUILD

    tips 'clear old rpm pkg file ...'
    shred -zu $HOME/rpmbuild/RPMS/x86_64/restful-server*.rpm
    shred -zu $HOME/rpmbuild/RPMS/x86_64/web-frontend*.rpm

    tips 'building mgmtool ...'
    rpmbuild -bb $HOME/rpmbuild/SPECS/restful-server.spec
    [ "$?" != "0" ] && { warning 'building restful-server failed !'; exit 1; }
    rpmbuild -bb $HOME/rpmbuild/SPECS/web-frontend.spec
    [ "$?" != "0" ] && { warning 'building web-frontend failed !'; exit 1; }

    tips "copy rpm pkg to $HOME ..."
    mv $HOME/rpmbuild/RPMS/x86_64/restful-server*.rpm $HOME
    mv $HOME/rpmbuild/RPMS/x86_64/web-frontend*.rpm $HOME

    tips 'building restful-server and web-frontend rpm, OK'
    exit 0
}

###############################################################################


###############################################################################
                    # The Logic Process
###############################################################################

[ "$#" -ne "2" ] && { error 'prams error !'; usage; exit 1; }
user=`whoami`
tips "Welcome ... $user"
[ "$user" != 'root' ] && { warning 'permission deny, only <root> can do this !'; exit 1; }

while [[ -n "$1" ]]; do
    #statements
    case "$1" in
        -h | --help ) usage; exit 0;
            ;;
        -v) set_rpm_version $2; shift 2;
    esac
done

# building rpm pkg
build_rpm_pkg
