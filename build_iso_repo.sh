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

g_version=2.0

function usage() {
    cat << HELP
    Usge: ./build_iso_repo.sh -p <path to rpm repo dir> -n <iso name>
          -h | --help    : help
          -v | --version : check version of script
HELP
    exit 0
}

g_rpm_repo_dir=
g_iso_name=

function set_repo_path() {
    [ ! -d $1 ] || [ -z $1 ] && {
        error "No such rpm repo dir !!!"
        usage
    }

    g_rpm_repo_dir=$1
}
function set_repo_name() {
    [ -z $1 ] && {
        error "not give invalid iso name"
        usage
    }
    g_iso_name=$1
}

function build_iso_file() {
    tips "build iso file ..."

    which createrepo
    [ "$?" != "0" ] && {
        warning "not which createrepo sys tool, try to install it ..."
        yum -y install createrepo
    }

    sleep 1

    createrepo -p -d -o $g_rpm_repo_dir $g_rpm_repo_dir
    [ "$?" != "0" ] && {
        warning "createrepo $path failed ... Pls check something wrong !"
        exit 1
    }

    tips "Now, try to create ISO file ..."
    which mkisofs
    [ "$?" != "0" ] && {
        warning "not which mkisofs sys tool, try to install it ..."
        yum -y install genisoimage
    }

    tips 'create Setup config file in iso ...'
    local product=${g_iso_name%.*}
    echo "$product" > $g_rpm_repo_dir/Setup

    mkisofs -o $g_iso_name -N -no-iso-translate -J -R $g_rpm_repo_dir
    [ "$?" != "0" ] && {
        error "create iso file $g_iso_name failed ... Pls check something wrong !"
        exit 1
    }

    [ -d ./iso_repo ] && {
        tips "Move the ISO files to local NFS-ISO repo ./iso_repo"
        mv ./*.iso ./iso_repo
    }

    tips "create iso file $g_iso_name success"
}
###############################################################################
                    # The Logic Process
###############################################################################

[ "$#" -ne "4" ] && { error 'prams error !'; usage; exit 1; }

user=`whoami`
tips "Welcome ... $user"
[ "$user" != 'root' ] && { warning 'permission deny, only <root> can do this !'; exit 1; }

while [[ -n "$1" ]]; do
    #statements
    case "$1" in
        -h | --help ) usage; exit 0;
            ;;
        -p) set_repo_path $2; shift 2;
            ;;
        -n) set_repo_name $2; shift 2;
            ;;
    esac
done

build_iso_file
