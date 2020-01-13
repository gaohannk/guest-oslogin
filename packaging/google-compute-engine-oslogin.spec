# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# For EL7, if building on CentOS, override dist to be el7.
%if 0%{?rhel} == 7
  %define dist .el7
%endif

Name:           google-compute-engine-oslogin
Epoch:          1
Version:        %{_version}
Release:        g1%{?dist}
Summary:        OS Login Functionality for Google Compute Engine

License:        ASL 2.0
Source0:        %{name}_%{version}.orig.tar.gz

BuildRequires:  boost-devel
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  libcurl-devel
BuildRequires:  json-c-devel
BuildRequires:  pam-devel

%if 0%{?rhel} == 6
Requires: crontabs
%else
BuildRequires: systemd
%endif

%if 0%{?rhel} == 8
BuildRequires:  python3-policycoreutils
Requires:  python3-policycoreutils
%else
BuildRequires:  policycoreutils-python
Requires:  policycoreutils-python
%endif

Requires: boost-regex
Requires: json-c

%description
This package contains several libraries and changes to enable OS Login functionality
for Google Compute Engine.

%global debug_package %{nil}

%prep
%setup

%build
make %{?_smp_mflags} LDLIBS="-lcurl -ljson-c -lboost_regex"

%install
rm -rf %{buildroot}
%if 0%{?rhel} == 6
make install DESTDIR=%{buildroot} LIBDIR=/%{_lib} VERSION=%{version} INSTALL_SELINUX=y INSTALL_CRON=y
%else
make install DESTDIR=%{buildroot} LIBDIR=/%{_lib} VERSION=%{version} INSTALL_SELINUX=y
%endif

%files
%doc
/%{_lib}/libnss_oslogin-%{version}.so
/%{_lib}/libnss_cache_oslogin-%{version}.so
/%{_lib}/libnss_oslogin.so.2
/%{_lib}/libnss_cache_oslogin.so.2
/%{_lib}/security/pam_oslogin_admin.so
/%{_lib}/security/pam_oslogin_login.so
/usr/bin/google_authorized_keys
/usr/bin/google_oslogin_control
/usr/bin/google_oslogin_nss_cache
/usr/share/selinux/packages/oslogin.pp
%{_mandir}/man8/nss-oslogin.8.gz
%{_mandir}/man8/libnss_oslogin.so.2.8.gz
%{_mandir}/man8/nss-cache-oslogin.8.gz
%{_mandir}/man8/libnss_cache_oslogin.so.2.8.gz
%if 0%{?rhel} == 6
%config(noreplace) /etc/cron.d/%{name}
%else
/lib/systemd/system/google-oslogin-cache.service
/lib/systemd/system/google-oslogin-cache.timer
/lib/systemd/system-preset/90-google-compute-engine-oslogin.preset
%endif

%post
%if 0%{?rhel} != 6
if [ $1 -eq 1 ]; then
  # Initial installation
  systemctl enable google-oslogin-cache.timer >/dev/null 2>&1 || :

  if [ -d /run/systemd/system ]; then
    systemctl daemon-reload >/dev/null 2>&1 || :
    systemctl start google-oslogin-cache.timer >/dev/null 2>&1 || :
  fi
fi
%endif

/sbin/ldconfig
if [ $1 -gt 1 ]; then  # This is an upgrade.
  if semodule -l | grep -qi oslogin.el6; then
    echo "Removing old SELinux module for OS Login."
    semodule -r oslogin.el6
  fi
fi

echo "Installing SELinux module for OS Login."
semodule -i /usr/share/selinux/packages/oslogin.pp
if [ -e /var/google-sudoers.d ]; then
  restorecon -r /var/google-sudoers.d
fi

%preun
%if 0%{?rhel} != 6
%systemd_preun google-oslogin-cache.timer
%endif

%postun
%if 0%{?rhel} != 6
%systemd_postun
%endif

/sbin/ldconfig
if [ $1 = 0 ]; then  # This is an uninstall.
  if semodule -l|grep -qi oslogin; then
    echo "Removing SELinux module for OS Login."
    semodule -r oslogin
  fi
fi


%changelog
