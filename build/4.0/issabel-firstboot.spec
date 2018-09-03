%define modname firstboot
Summary: Issabel First Boot Setup
Name:    issabel-%{modname}
Version: 4.0.0
Release: 3
License: GPL
Group:   Applications/System
Source0: %{modname}_%{version}-%{release}.tgz
BuildRoot: %{_tmppath}/%{modname}-%{version}-root
BuildArch: noarch
Requires: mysql, mysql-server, dialog
Requires: sed, grep
Requires: coreutils
Conflicts: elastix-mysqldbdata
Requires(post): chkconfig, /bin/cp
Obsoletes: elastix-firstboot
Provides: elastix-firstboot

# commands: /bin/chvt
Requires: kbd

Requires: /usr/sbin/saslpasswd2

%description
This module contains (or should contain) utilities and configurations that
cannot be prepared at install time from the ISO image, and are therefore
delayed until the first boot of the newly installed system. The main aim of
this script is to wait until all RPMS are able to either prepare their 
databases on their own, or delegate this task to this package.

%prep
%setup -n %{name}_%{version}-%{release}

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/init.d/
mkdir -p $RPM_BUILD_ROOT/var/spool/issabel-mysqldbscripts/
mkdir -p $RPM_BUILD_ROOT/usr/share/issabel-firstboot/
mkdir -p $RPM_BUILD_ROOT/usr/bin/
mkdir -p $RPM_BUILD_ROOT/usr/sbin/
cp issabel-firstboot $RPM_BUILD_ROOT/etc/init.d/
cp change-passwords issabel-admin-passwords $RPM_BUILD_ROOT/usr/bin/
mv compat-dbscripts/ $RPM_BUILD_ROOT/usr/share/issabel-firstboot/

%post

if [ -d /etc/systemd ] ; then
    cat > /usr/lib/systemd/system/issabel-firstboot.service <<'ISSABELFIRSTBOOT'
[Unit]
Description=issabel-firstboot.service
After=getty@tty2.service
After=mariadb.service
Before=asterisk.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c "chvt 2 && /usr/bin/issabel-admin-passwords --init && chvt 1"
ExecStartPre=-/bin/bash -c "chvt 2 && /usr/src/geoip_install.sh && chvt 1"
ExecReload=/bin/kill -HUP $MAINPID
RemainAfterExit=no
WorkingDirectory=/
Environment=TERM=linux
StandardInput=tty
StandardOutput=tty
TTYPath=/dev/tty2
TTYReset=yes
TTYVHangup=yes

[Install]
WantedBy=default.target
ISSABELFIRSTBOOT
    systemctl enable issabel-firstboot.service

    cat > /usr/lib/systemd/system/amportal-reload.service <<'AMPORTALRELOAD'
[Unit]
Description=amportal-reload.service
After=asterisk.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/amportal a r
RemainAfterExit=no
WorkingDirectory=/

[Install]
WantedBy=default.target

AMPORTALRELOAD
    systemctl enable amportal-reload.service
else
    chkconfig --del issabel-firstboot
    chkconfig --add issabel-firstboot
    chkconfig --level 2345 issabel-firstboot on
fi

# The following scripts are placed in the spool directory if the corresponding
# database does not exist. This is only temporary and should be removed when the
# corresponding package does this by itself.
if [ ! -d /var/lib/mysql/asteriskcdrdb ] ; then
	cp /usr/share/issabel-firstboot/compat-dbscripts/01-asteriskcdrdb.sql /usr/share/issabel-firstboot/compat-dbscripts/02-asteriskuser-password.sql /var/spool/issabel-mysqldbscripts/
fi

# If installing, the system might have mysql running (upgrading from a RC).
# The default password is written to the configuration file.
if [ $1 -eq 1 ] ; then
	if [ -e /var/lib/mysql/mysql ] ; then
		if [ ! -e /etc/issabel.conf ] ; then
			echo "Installing in active system - legacy password written to /etc/issabel.conf"
			echo "mysqlrootpwd=iSsAbEl.2o17" >> /etc/issabel.conf
		fi
                if [ -f /etc/issabel.conf  ] ; then
                        grep 'cyrususerpwd' /etc/issabel.conf &> /dev/null
                        res=$?
                        if [ $res != 0 ] ; then
                            echo "cyrususerpwd=issabel" >> /etc/issabel.conf
                        fi
                fi

	fi
fi

# If updating, and there is no /etc/issabel.conf , a default file is generated with
# legacy password so new modules continue to work.
if [ $1 -eq 2 ] ; then
	if [ ! -e /etc/issabel.conf ] ; then
		echo "Updating in active system - legacy password written to /etc/issabel.conf"
		echo "mysqlrootpwd=iSsAbEl.2o17" >> /etc/issabel.conf
	fi
	if [ -f /etc/issabel.conf  ] ; then
		grep 'cyrususerpwd' /etc/issabel.conf &> /dev/null
		res=$?
		if [ $res != 0 ] ; then
		    echo "cyrususerpwd=issabel" >> /etc/issabel.conf
		fi
	fi
fi

# If updating, ensure issabel-firstboot now runs at shutdown
if [ $1 -eq 2 ] ; then
    touch /var/lock/subsys/issabel-firstboot
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root)
%attr(755, root, root) /etc/init.d/*
%dir %{_localstatedir}/spool/issabel-mysqldbscripts/
/usr/share/issabel-firstboot/compat-dbscripts/01-asteriskcdrdb.sql
/usr/share/issabel-firstboot/compat-dbscripts/02-asteriskuser-password.sql
/usr/bin/change-passwords
/usr/bin/issabel-admin-passwords

%changelog
