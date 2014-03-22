#
# Example of spec file for rpm build
#

Summary: Restful Server Program
Name: restful-server
Version: 1.4
Release: 0.el6
License: GPL
Group: Application/System
Vendor: Vmediax.com
Source: restful-server
URL: http://vmediax.com/download/restful-server-1.3.1.tar.gz
Distribution: CentOS 6.4 5.9 x86_64
Packager: wangdiwen <wangdiwen@vmediax.com>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Prefix: /

%define install_path		/
%define etc_path			/etc/rc.d/init.d
%define etc_path_conf		/opt/system/etc/rc.d/init.d
%define main_path			/usr/local/restful-server
%define common_path			/usr/local/restful-server/common
%define model_path			/usr/local/restful-server/model
%define template_path		/usr/local/restful-server/template
%define conf_path			/opt/system/conf/restful-server
%define log_path			/opt/system/log/restful-server
%define package_name		restful-server

%description
This is restful server program, it provide RESTful API of web manager tools.

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
mkdir -p $RPM_BUILD_ROOT%{etc_path_conf}
mkdir -p $RPM_BUILD_ROOT%{common_path}
mkdir -p $RPM_BUILD_ROOT%{model_path}
mkdir -p $RPM_BUILD_ROOT%{template_path}
mkdir -p $RPM_BUILD_ROOT%{conf_path}
mkdir -p $RPM_BUILD_ROOT%{log_path}

cp -a %{package_name}/restful-server.py $RPM_BUILD_ROOT%{main_path}
cp -a %{package_name}/restful-server $RPM_BUILD_ROOT%{etc_path}
cp -a %{package_name}/restful-server $RPM_BUILD_ROOT%{etc_path_conf}
cp -a %{package_name}/common/* $RPM_BUILD_ROOT%{common_path}
cp -a %{package_name}/model/* $RPM_BUILD_ROOT%{model_path}
cp -a %{package_name}/template/* $RPM_BUILD_ROOT%{template_path}
cp -a %{package_name}/conf/auth_user $RPM_BUILD_ROOT%{conf_path}
cp -a %{package_name}/conf/global_meta_data.json $RPM_BUILD_ROOT%{conf_path}
#cp -a %{package_name}/conf/install_log $RPM_BUILD_ROOT%{conf_path}
#cp -a %{package_name}/conf/ntp_server $RPM_BUILD_ROOT%{conf_path}
cp -a %{package_name}/conf/rpm-secret-key $RPM_BUILD_ROOT%{conf_path}
cp -a %{package_name}/conf/startup $RPM_BUILD_ROOT%{conf_path}
cp -a %{package_name}/conf/10-raid.rules $RPM_BUILD_ROOT%{conf_path}
#cp -a %{package_name}/conf/json_config $RPM_BUILD_ROOT%{conf_path}
cp -a %{package_name}/conf/restful.log $RPM_BUILD_ROOT%{log_path}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%post
# creatae soft link of start script
if [ ! -f $RPM_INSTALL_PREFIX/etc/rc.d/rc3.d/S90restful-server ];then
	/bin/ln -s ../init.d/restful-server $RPM_INSTALL_PREFIX/etc/rc.d/rc3.d/S90restful-server
fi
if [ ! -f $RPM_INSTALL_PREFIX/etc/rc.d/rc5.d/S90restful-server ];then
	/bin/ln -s ../init.d/restful-server $RPM_INSTALL_PREFIX/etc/rc.d/rc5.d/S90restful-server
fi
# set startup
#chkconfig --add restful-server

# create static route script
if [ ! -f $RPM_INSTALL_PREFIX/etc/sysconfig/static-routes ]; then
	touch $RPM_INSTALL_PREFIX/etc/sysconfig/static-routes
fi
# modify the network config file
sed -i "s/\(.*\)add -\$args$/\1add \$args/g" $RPM_INSTALL_PREFIX/etc/rc.d/init.d/network

%preun
# delete soft link of start script
# uninstall
if [ "$1" = "0" ];then
#chkconfig --del restful-server
#rm -rf $RPM_INSTALL_PREFIX%{main_path}
	rm -f $RPM_INSTALL_PREFIX/etc/rc.d/init.d/restful-server
	rm -f $RPM_INSTALL_PREFIX/etc/rc.d/rc3.d/S90restful-server
	rm -f $RPM_INSTALL_PREFIX/etc/rc.d/rc5.d/S90restful-server
fi

%postun
if [ "$1" = "0" ];then
	if [ -d /usr/local/restful-server ];then
		rm -rf /usr/local/restful-server
	fi
fi
if [ "$1" = "1" ];then
	if [ -f "/opt/system/conf/restful-server/ntp_server" ];then
		rm -f /opt/system/conf/restful-server/ntp_server
	fi
	if [ -f "/opt/system/conf/restful-server/json_config" ];then
		rm -f /opt/system/conf/restful-server/json_config
	fi
	if [ -f "/opt/system/conf/restful-server/install_log" ];then
		rm -f /opt/system/conf/restful-server/install_log
	fi
fi

%files
%{install_path}

%config(noreplace) %{log_path}/restful.log
#%config %{etc_path_conf}/restful-server
%config(noreplace) %{conf_path}/global_meta_data.json
%config %{conf_path}/rpm-secret-key
%config(noreplace) %{conf_path}/startup
#%config %{conf_path}/auth_user

%defattr(-, root, root)

%changelog
