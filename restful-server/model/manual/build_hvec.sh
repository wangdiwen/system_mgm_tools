#!/bin/sh

###############################################################################
                    # Author : wangdiwen
                    # Date   : 2013-
                    # License: LGPL
                    # Note   : build the hvec rpm pkg

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
g_hvec_path=""
g_hvec_version=""

function usage() {
    cat << HELP
    Usge: ./build_hvec.sh -p <hvec path> -v <version, 1.0.1>
          -h | --help for help
HELP
}
function set_path() {
    g_hvec_path=$1
}
function set_version() {
    g_hvec_version=$1
}
function build_hvec() {
    tips 'build_hvec ...'
    tips 'path    = '$g_hvec_path
    tips 'version = '$g_hvec_version  # like: 1.0.1

    # checking length of version
    [ -d "$g_hvec_path" ] || { error 'hvec path error !'; exit 1; }

    str_list=`echo "$g_hvec_version" | awk -F. '{ print $1,$2,$3 }'`
    arr=($str_list)
    ver_1=${arr[0]}
    ver_2=${arr[1]}
    ver_3=${arr[2]}
    [ -n "$ver_1" ] || { error 'version error !'; exit 1; }
    [ -n "$ver_2" ] || { error 'version error !'; exit 1; }
    [ -n "$ver_3" ] || { error 'version error !'; exit 1; }

    # substr the version
    ver_major=$ver_1'.'$ver_2
    ver_minor=$ver_3
    # tips $ver_major
    # tips $ver_minor
    # exit 1

    # checking path is invalid ?
    [ -f "$g_hvec_path/boot.scr" ] || { error "no such file: $g_hvec_path/boot.scr"; exit 1; }
    [ -f "$g_hvec_path/ramdisk.gz" ] || { error "no such file: $g_hvec_path/ramdisk.gz"; exit 1; }
    [ -f "$g_hvec_path/u-boot.bin" ] || { error "no such file: $g_hvec_path/u-boot.bin"; exit 1; }
    [ -f "$g_hvec_path/uImage" ] || { error "no such file: $g_hvec_path/uImage"; exit 1; }
    [ -f "$g_hvec_path/vmx_encoder.ko" ] || { error "no such file: $g_hvec_path/vmx_encoder.ko"; exit 1; }
    [ -f "$g_hvec_path/api/libhvec_api.so" ] || { error "no such file: $g_hvec_path/api/libhvec_api.so"; exit 1; }

    # checking has 'rpmbuild' tool
    which rpmbuild > /dev/null 2>&1
    [ "$?" != '0' ] && { warning 'not install rpmbuild tool, prepare to installing ...'; \
                                tips 'installing rpmbuild ...'; \
                                echo -e "y\n" | yum install rpm-build; }

    # set rpm build path
    tips 'set rpm new build path to local ...'
    echo %_topdir $HOME/rpmbuild > ~/.rpmmacros
    [ "$?" == "0" ] && { tips 'set OK'; }

    # create dirs
    mkdir -p $HOME/rpmbuild/BUILD
    mkdir -p $HOME/rpmbuild/RPMS
    mkdir -p $HOME/rpmbuild/SOURCE
    mkdir -p $HOME/rpmbuild/SPECS
    mkdir -p $HOME/rpmbuild/SRPMS

    # create hvec build path and copy file
    mkdir -p $HOME/rpmbuild/BUILD/hvec
    cp -a $g_hvec_path/{boot.scr,ramdisk.gz,u-boot.bin,uImage,vmx_encoder.ko} $HOME/rpmbuild/BUILD/hvec
    cp -a $g_hvec_path/api/libhvec_api.so $HOME/rpmbuild/BUILD/hvec

    # create spec file
    echo "
# Example of spec file for rpm build

Summary: hvec rpm pkg
Name: hvec
Version: $ver_major
Release: $ver_minor.el5
License: GPL
Group: Application/System
Vendor: Vmediax.com
Source: hvec
URL: http://vmediax.com/download/hvec.tar.gz
Distribution: CentOS 6.4
Packager: wangdiwen <wangdiwen@vmediax.com>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Prefix: /

%define install_path            /
%define opt_path            /opt/hvec
%define lib_path            /usr/lib
%define package_name        hvec

%description
hvec rpm package.

%prep
#%setup
#setup -q
#setup -c %{name}-%{version}

#%patch

%build

%install
rm -rf \$RPM_BUILD_ROOT
mkdir -p \$RPM_BUILD_ROOT%{install_path}
mkdir -p \$RPM_BUILD_ROOT%{opt_path}
mkdir -p \$RPM_BUILD_ROOT%{lib_path}

cp -a %{package_name}/boot.scr \$RPM_BUILD_ROOT%{opt_path}
cp -a %{package_name}/ramdisk.gz \$RPM_BUILD_ROOT%{opt_path}
cp -a %{package_name}/u-boot.bin \$RPM_BUILD_ROOT%{opt_path}
cp -a %{package_name}/uImage \$RPM_BUILD_ROOT%{opt_path}
cp -a %{package_name}/vmx_encoder.ko \$RPM_BUILD_ROOT%{opt_path}

cp -a %{package_name}/libhvec_api.so \$RPM_BUILD_ROOT%{lib_path}

%clean
rm -rf \$RPM_BUILD_ROOT

%pre
%post
%preun
[ -d %{opt_path} ] && rm -rf %{opt_path}
[ -d %{lib_path} ] && rm -rf %{lib_path}

%files
%{opt_path}
%{lib_path}

%defattr(-, root, root)

%changelog
" > $HOME/rpmbuild/SPECS/hvec.spec

    [ "$?" == '0' ] && { tips 'create spec file, OK !'; }

    # build rpm pkg
    tips 'build ...'
    cd ~
    rpmbuild -bb $HOME/rpmbuild/SPECS/hvec.spec #> /dev/null 2>&1
    [ "$?" == '0' ] && { tips 'build hvec rpm package, OK !'; }
    cd -

    pkg_name="hvec-$ver_major-$ver_minor.el5.x86_64.rpm"
    [ -f "$HOME/rpmbuild/RPMS/x86_64/$pkg_name" ] && { mv "$HOME/rpmbuild/RPMS/x86_64/$pkg_name" ./; }
    tips "build file is ./$pkg_name"
    exit 0;
}
###############################################################################


###############################################################################
                    # The Logic Process
###############################################################################

[ $# -ne 4 ] && { usage; exit 1; }

while [[ -n "$1" ]]; do
    #statements
    case $1 in
        # Todo...
        -p) set_path $2; shift 2
            ;;
        -v) set_version $2; shift 2
            ;;
        -h|--help ) usage; exit
            ;;
    esac
done

build_hvec
