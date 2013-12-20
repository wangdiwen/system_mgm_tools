#
# Example of spec file for rpm build
#

Summary: Web Frontend Program
Name: web-frontend
Version: 1.3
Release: 9rc1.el6
License: GPL
Group: Application/System
Vendor: Vmediax.com
Source: web-frontend
URL: http://vmediax.com/download/web-frontend-1.3.1.tar.gz
Distribution: CentOS 6.4 5.9 x86_64
Packager: wangdiwen <wangdiwen@vmediax.com>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Prefix: /

%define install_path		/
%define etc_path			/etc/rc.d/init.d
%define main_path			/usr/local/web-frontend
%define common_path			/usr/local/web-frontend/common
%define view_path			/usr/local/web-frontend/view
%define package_name		web-frontend

%description
This is web manager program for new base system. 

%prep
#%setup
#setup -q
#setup -c %{name}-%{version}

#%patch

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{install_path}
mkdir -p $RPM_BUILD_ROOT%{etc_path}
mkdir -p $RPM_BUILD_ROOT%{common_path}
mkdir -p $RPM_BUILD_ROOT%{view_path}

cp -a %{package_name}/web-frontend.py $RPM_BUILD_ROOT%{main_path}
cp -a %{package_name}/web-frontend $RPM_BUILD_ROOT%{etc_path}
cp -a %{package_name}/common/* $RPM_BUILD_ROOT%{common_path}
cp -a %{package_name}/view/* $RPM_BUILD_ROOT%{view_path}

%clean
rm -rf $RPM_BUILD_ROOT

%post
# create soft link of start scripts
if [ ! -f $RPM_INSTALL_PREFIX/etc/rc.d/rc3.d/S90web-frontend ];then
	/bin/ln -s ../init.d/web-frontend $RPM_INSTALL_PREFIX/etc/rc.d/rc3.d/S90web-frontend
fi
if [ ! -f $RPM_INSTALL_PREFIX/etc/rc.d/rc5.d/S90web-frontend ];then
	/bin/ln -s ../init.d/web-frontend $RPM_INSTALL_PREFIX/etc/rc.d/rc5.d/S90web-frontend
fi
# set startup
#chkconfig --add web-frontend

%preun
# delete soft link of start scripts
# uninstall
if [ "$1" = "0" ];then
#chkconfig --del web-frontend
	rm -f $RPM_INSTALL_PREFIX/etc/rc.d/init.d/web-frontend
	rm -f $RPM_INSTALL_PREFIX/etc/rc.d/rc3.d/S90web-frontend
	rm -f $RPM_INSTALL_PREFIX/etc/rc.d/rc5.d/S90web-frontend
fi
%postun
if [ "$1" = "0" ];then
	if [ -d /usr/local/web-frontend ];then
		rm -rf /usr/local/web-frontend
	fi
fi

%files
%{install_path}

%defattr(-, root, root)

%changelog
