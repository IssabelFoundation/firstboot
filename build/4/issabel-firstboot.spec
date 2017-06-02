%define modname firstboot
Summary: Issabel First Boot Setup
Name:    issabel-%{modname}
Version: 4.0.0
Release: 1
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
this script is to replace elastix-mysqldbdata until all RPMS are able to
either prepare their databases on their own, or delegate this task to this
package.

%prep
%setup -n %{name}_%{version}-%{release}

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/init.d/
mkdir -p $RPM_BUILD_ROOT/var/spool/elastix-mysqldbscripts/
mkdir -p $RPM_BUILD_ROOT/usr/share/elastix-firstboot/
mkdir -p $RPM_BUILD_ROOT/usr/bin/
mkdir -p $RPM_BUILD_ROOT/usr/sbin/
cp elastix-firstboot $RPM_BUILD_ROOT/etc/init.d/
cp change-passwords elastix-admin-passwords $RPM_BUILD_ROOT/usr/bin/
mv compat-dbscripts/ $RPM_BUILD_ROOT/usr/share/elastix-firstboot/

%post

if [ -d /etc/systemd ] ; then
    cat > /usr/lib/systemd/system/elastix-firstboot.service <<'ELASTIXFIRSTBOOT'
[Unit]
Description=elastix-firstboot.service
After=getty@tty2.service
After=mariadb.service
Before=asterisk.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c "chvt 2 && /usr/bin/elastix-admin-passwords --init && chvt 1"
ExecStartPre=/usr/bin/echo -e \033%G
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
ELASTIXFIRSTBOOT
    systemctl enable elastix-firstboot.service
else
    chkconfig --del elastix-firstboot
    chkconfig --add elastix-firstboot
    chkconfig --level 2345 elastix-firstboot on
fi

# The following scripts are placed in the spool directory if the corresponding
# database does not exist. This is only temporary and should be removed when the
# corresponding package does this by itself.
if [ ! -d /var/lib/mysql/asteriskcdrdb ] ; then
	cp /usr/share/elastix-firstboot/compat-dbscripts/01-asteriskcdrdb.sql /usr/share/elastix-firstboot/compat-dbscripts/02-asteriskuser-password.sql /var/spool/elastix-mysqldbscripts/
fi

# If installing, the system might have mysql running (upgrading from a RC).
# The default password is written to the configuration file.
if [ $1 -eq 1 ] ; then
	if [ -e /var/lib/mysql/mysql ] ; then
		if [ ! -e /etc/elastix.conf ] ; then
			echo "Installing in active system - legacy password written to /etc/elastix.conf"
			echo "mysqlrootpwd=eLaStIx.2oo7" >> /etc/elastix.conf
		fi
                if [ -f /etc/elastix.conf  ] ; then
                        grep 'cyrususerpwd' /etc/elastix.conf &> /dev/null
                        res=$?
                        if [ $res != 0 ] ; then
                            echo "cyrususerpwd=palosanto" >> /etc/elastix.conf
                        fi
                fi

	fi
fi

# If updating, and there is no /etc/elastix.conf , a default file is generated with
# legacy password so new modules continue to work.
if [ $1 -eq 2 ] ; then
	if [ ! -e /etc/elastix.conf ] ; then
		echo "Updating in active system - legacy password written to /etc/elastix.conf"
		echo "mysqlrootpwd=eLaStIx.2oo7" >> /etc/elastix.conf
	fi
	if [ -f /etc/elastix.conf  ] ; then
		grep 'cyrususerpwd' /etc/elastix.conf &> /dev/null
		res=$?
		if [ $res != 0 ] ; then
		    echo "cyrususerpwd=palosanto" >> /etc/elastix.conf
		fi
	fi
fi

# If updating, ensure elastix-firstboot now runs at shutdown
if [ $1 -eq 2 ] ; then
    touch /var/lock/subsys/elastix-firstboot
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root)
%attr(755, root, root) /etc/init.d/*
%dir %{_localstatedir}/spool/elastix-mysqldbscripts/
/usr/share/elastix-firstboot/compat-dbscripts/01-asteriskcdrdb.sql
/usr/share/elastix-firstboot/compat-dbscripts/02-asteriskuser-password.sql
/usr/bin/change-passwords
/usr/bin/elastix-admin-passwords

%changelog
