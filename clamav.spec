#global prerelease  rc1
%global with_unrar    1
%global with_bytecode    1

%bcond_with     systemd
%bcond_with     tmpfiles

%global _hardened_build 1

%ifnarch s390 s390x
%global have_ocaml  1
%else
%global have_ocaml  0
%endif

%global username    clam
%global homedir        %_var/lib/clamav
%global freshclamlog    %_var/log/clamav/freshclam.log
%global pkgdatadir    %_datadir/%name

%global scanuser    clam
%global scanstatedir    %_var/run/clamav

%{?with_noarch:%global noarch   BuildArch:  noarch}
%{!?_unitdir:%global _unitdir /lib/systemd/system}
%{!?release_func:%global release_func() %%{?prerelease:0.}%1%%{?prerelease:.%%prerelease}%%{?dist}}
%{!?apply:%global  apply(p:n:b:) %patch%%{-n:%%{-n*}} %%{-p:-p %%{-p*}} %%{-b:-b %%{-b*}} \
%nil}
%{!?systemd_reqs:%global systemd_reqs \
Requires(post):      /bin/systemctl\
Requires(preun):     /bin/systemctl\
Requires(postun):    /bin/systemctl\
%nil}
%{!?systemd_install:%global systemd_install()\
%post %1\
%systemd_post %2 \
%preun %1\
%systemd_preun %2 \
%postun %1\
%systemd_postun_with_restart %2 \
%nil}


Summary:    End-user tools for the Clam Antivirus scanner
Name:       clamav
Version:    0.99.3
Release:    1%{?dist}
License:    %{?with_unrar:proprietary}%{!?with_unrar:GPLv2}
Group:      Applications/File
URL:        http://www.clamav.net
%if 0%{?with_unrar:1}
Source0:    http://download.sourceforge.net/sourceforge/clamav/%name-%version%{?prerelease}.tar.gz
Source999:  http://download.sourceforge.net/sourceforge/clamav/%name-%version%{?prerelease}.tar.gz.sig
%else
# Unfortunately, clamav includes support for RAR v3, derived from GPL
# incompatible unrar from RARlabs. We have to pull this code out.
# tarball was created by
#  make clean-sources NAME=clamav VERSION=<version> TARBALL=clamav-<version>.tar.gz TARBALL_CLEAN=clamav-<version>-norar.tar.xz
Source0:    %name-%version%{?prerelease}-norar.tar.xz
%endif
# Sources:
# - http://db.local.clamav.net/main.cvd
# - http://db.local.clamav.net/daily.cvd
# - http://db.local.clamav.net/bytecode.cvd
Source10:    main-20180130.cvd
Source11:    daily-20180130.cvd
Source12:    bytecode-20180130.cvd
Source13:    freshclam.conf
Source14:    clamd.conf

Patch24:    clamav-0.99-private.patch
Patch27:    clamav-0.98-umask.patch
# https://llvm.org/viewvc/llvm-project/llvm/trunk/lib/ExecutionEngine/JIT/Intercept.cpp?r1=128086&r2=137567
Patch30:    llvm-glibc.patch
Patch31:    clamav-0.99.1-setsebool.patch
Patch33:    clamav-0.99.2-temp-cleanup.patch
BuildRoot:    %_tmppath/%name-%version-%release-root
Requires:    clamav-lib = %version-%release
Requires:    data(clamav)
Provides:   clamav-update
Obsoletes:   clamav-update
BuildRequires:  pcre-devel
BuildRequires:    zlib-devel bzip2-devel gmp-devel curl-devel
BuildRequires:    ncurses-devel openssl-devel libxml2-devel
BuildRequires:    %_includedir/tcpd.h
%{?with_bytecode:BuildRequires:    bc tcl groff graphviz}
%if %{have_ocaml}
%{?with_bytecode:BuildRequires:    ocaml}
%endif

%package filesystem
Summary:    Filesystem structure for clamav
Group:        Applications/File
Provides:    user(%username)  = 4
Provides:    group(%username) = 4
# Prevent version mix
Conflicts:    %name < %version-%release
Conflicts:    %name > %version-%release
Requires(pre):  shadow-utils
%{?noarch}

%package lib
Summary:    Dynamic libraries for the Clam Antivirus scanner
Group:        System Environment/Libraries
Requires:    data(clamav)

%package devel
Summary:    Header files and libraries for the Clam Antivirus scanner
Group:        Development/Libraries
Requires:    clamav-lib        = %version-%release
Requires:    clamav-filesystem = %version-%release
Requires:    openssl-devel

%package data
Summary:    Virus signature data for the Clam Antivirus scanner
Group:        Applications/File
Requires(pre):        clamav-filesystem = %version-%release
Requires(postun):    clamav-filesystem = %version-%release
Provides:        data(clamav) = full
Conflicts:        data(clamav) < full
Conflicts:        data(clamav) > full
%{?noarch}

%package server
Summary:    Clam Antivirus scanner server
Group:        System Environment/Daemons
Source3:    clamd.logrotate
Source203:    clamav-update.logrotate
Source1000: clamd.service
Provides:   clamav-server-systemd
Requires:    crontabs
Requires:    data(clamav)
Requires:    clamav-filesystem = %version-%release
Requires:    clamav-lib        = %version-%release
Requires:    nc coreutils
Requires(pre):        /etc/cron.d
Requires(postun):    /etc/cron.d
Requires(post):        %__chown %__chmod
Requires(post):        group(%username)

%description
Clam AntiVirus is an anti-virus toolkit for UNIX. The main purpose of this
software is the integration with mail servers (attachment scanning). The
package provides a flexible and scalable multi-threaded daemon, a command
line scanner, and a tool for automatic updating via Internet. The programs
are based on a shared library distributed with the Clam AntiVirus package,
which you can use with your own software. The virus database is based on
the virus database from OpenAntiVirus, but contains additional signatures
(including signatures for popular polymorphic viruses, too) and is KEPT UP
TO DATE.

%description filesystem
This package provides the filesystem structure and contains the
user-creation scripts required by clamav.

%description lib
This package contains dynamic libraries shared between applications
using the Clam Antivirus scanner.

%description devel
This package contains headerfiles and libraries which are needed to
build applications using clamav.

%description data
This package contains the virus-database needed by clamav. This
database should be updated regularly; the 'clamav-update' package
ships a corresponding cron-job.

%description server
This package contains files which are needed to execute the clamd-daemon.

%prep
%setup -q -n %{name}-%{version}%{?prerelease}

%apply -n24 -p1 -b .private
%apply -n27 -p1 -b .umask
%apply -n30 -p1
%apply -n31 -p1 -b .setsebool
%{?apply_end}

mkdir -p libclamunrar{,_iface}
%{!?with_unrar:touch libclamunrar/{Makefile.in,all,install}}

sed -ri \
    -e 's!^#?(LogFile ).*!#\1/var/log/clamav!g' \
    -e 's!^#?(LocalSocket ).*!#\1/var/run/clamav/clamd.sock!g' \
    -e 's!^(#?PidFile ).*!\1/var/run/clamav/clamd.pid!g' \
    -e 's!^#?(User ).*!\1<USER>!g' \
    -e 's!^#?(AllowSupplementaryGroups|LogSyslog).*!\1 yes!g' \
    -e 's! /usr/local/share/clamav,! %homedir,!g' \
    etc/clamd.conf.sample

sed -ri \
    -e 's!^#?(UpdateLogFile )!#\1!g;' \
    -e 's!^#?(LogSyslog).*!\1 yes!g' \
    -e 's!(DatabaseOwner *)clamav$!\1%username!g' etc/freshclam.conf.sample


## ------------------------------------------------------------

%build
CFLAGS="$RPM_OPT_FLAGS -Wall -W -Wmissing-prototypes -Wmissing-declarations -std=gnu99"
CXXFLAGS="$RPM_OPT_FLAGS -std=gnu++98"
export LDFLAGS='%{?__global_ldflags} -Wl,--as-needed'
# HACK: remove me...
export FRESHCLAM_LIBS='-lz'
# IPv6 check is buggy and does not work when there are no IPv6 interface on build machine
export have_cv_ipv6=yes
%configure \
    --disable-static \
    --disable-rpath \
    --disable-silent-rules \
    --disable-clamav \
    --with-user=%username \
    --with-group=%username \
    --with-libcurl=%{_prefix} \
    --with-dbdir=/var/lib/clamav \
    --disable-milter \
    --enable-clamdtop \
    %{!?with_bytecode:--disable-llvm} \
    %{!?with_unrar:--disable-unrar}

# TODO: check periodically that CLAMAVUSER is used for freshclam only


# build with --as-needed and disable rpath
sed -i \
    -e 's! -shared ! -Wl,--as-needed\0!g'                    \
    -e '/sys_lib_dlsearch_path_spec=\"\/lib \/usr\/lib /s!\"\/lib \/usr\/lib !/\"/%_lib /usr/%_lib !g'    \
    libtool

make %{?_smp_mflags}


## ------------------------------------------------------------

%install
rm -rf "$RPM_BUILD_ROOT" _doc*
make DESTDIR="$RPM_BUILD_ROOT" install

install -d -m 0755 \
    $RPM_BUILD_ROOT%_sysconfdir/{mail,clamd.d,logrotate.d} \
    $RPM_BUILD_ROOT%_tmpfilesdir \
    $RPM_BUILD_ROOT%_var/{log,run} \
    $RPM_BUILD_ROOT%pkgdatadir \
    $RPM_BUILD_ROOT%homedir \
    $RPM_BUILD_ROOT%scanstatedir \
    $RPM_BUILD_ROOT/usr/lib/tmpfiles.d

rm -f    $RPM_BUILD_ROOT%_sysconfdir/clamd.conf.sample \
    $RPM_BUILD_ROOT%_libdir/*.la


#touch $RPM_BUILD_ROOT%homedir/daily.cld
#touch $RPM_BUILD_ROOT%homedir/main.cld

install -D -m 0644 -p %SOURCE10        $RPM_BUILD_ROOT%homedir/install/main.cvd
install -D -m 0644 -p %SOURCE11        $RPM_BUILD_ROOT%homedir/install/daily.cvd
%{?with_bytecode:install -D -m 0644 -p %SOURCE12        $RPM_BUILD_ROOT%homedir/install/bytecode.cvd}

install -D -m 0644 -p %SOURCE13        $RPM_BUILD_ROOT%_sysconfdir/freshclam.conf
install -D -m 0644 -p %SOURCE14        $RPM_BUILD_ROOT%_sysconfdir/clamd.conf

install -D -p -m 0644 %SOURCE1000        $RPM_BUILD_ROOT/lib/systemd/system/clamd.service


## prepare the update-files
install -D -m 0644 -p %SOURCE3    $RPM_BUILD_ROOT%_sysconfdir/logrotate.d/clamd
install -D -m 0644 -p %SOURCE203    $RPM_BUILD_ROOT%_sysconfdir/logrotate.d/freshclam
mkdir -p $RPM_BUILD_ROOT%_var/log/clamav
touch $RPM_BUILD_ROOT%freshclamlog

cat << EOF > $RPM_BUILD_ROOT/usr/lib/tmpfiles.d/clamd.conf
d %scanstatedir 0775 %scanuser %scanuser
EOF

rm -f $RPM_BUILD_ROOT%{_sysconfdir}/freshclam.conf.sample
rm -f $RPM_BUILD_ROOT%{_mandir}/man8/clamav-milter.*
rm -fv $RPM_BUILD_ROOT/usr/lib/systemd/system/clamav-daemon.service
rm -fv $RPM_BUILD_ROOT/usr/lib/systemd/system/clamav-daemon.socket
rm -fv $RPM_BUILD_ROOT/usr/lib/systemd/system/clamav-freshclam.service


## ------------------------------------------------------------

%check
make check

## ------------------------------------------------------------

%clean
rm -rf "$RPM_BUILD_ROOT"

## ------------------------------------------------------------

%preun data
if [ $1 -eq 0 ]; then
    [ -e %homedir/daily.cld ] && rm %homedir/daily.cld
    [ -e %homedir/main.cld ] && rm %homedir/main.cld
    [ -e %homedir/bytecode.cld ] && rm %homedir/bytecode.cld
    [ -e %homedir/daily.cvd ] && rm %homedir/daily.cvd
    [ -e %homedir/main.cvd ] && rm %homedir/main.cvd
    [ -e %homedir/bytecode.cvd ] && rm %homedir/bytecode.cvd
fi

exit 0

%post data
[ ! -e %homedir/daily.cvd ] && cp %homedir/install/daily.cvd %homedir/daily.cvd
[ ! -e %homedir/main.cvd ] && cp %homedir/install/main.cvd %homedir/main.cvd
[ ! -e %homedir/bytecode.cvd ] && cp %homedir/install/bytecode.cvd %homedir/bytecode.cvd

exit 0

%pre filesystem
getent group %{username} >/dev/null || groupadd -r %{username}
getent passwd %{username} >/dev/null || \
    useradd -r -g %{username} -d %{homedir} -s /sbin/nologin \
    -c "Clamav database update user" %{username}
exit 0

%preun server
%systemd_preun clamd.service 

%post server
/bin/systemd-tmpfiles --create /usr/lib/tmpfiles.d/clamd.conf || :
%systemd_post clamd.service

test -e %freshclamlog || {
    touch %freshclamlog
    %__chmod 0664 %freshclamlog
    %__chown root:%username %freshclamlog
    ! test -x /sbin/restorecon || /sbin/restorecon %freshclamlog
}

%postun server
%systemd_postun_with_restart clamd.service

%post   lib -p /sbin/ldconfig
%postun lib -p /sbin/ldconfig


%files
%defattr(-,root,root,-)
%doc AUTHORS BUGS COPYING ChangeLog FAQ NEWS README UPGRADE
%doc docs/*.pdf
%_bindir/*
%_mandir/man[15]/*
%exclude %_bindir/clamav-config
%attr(-,%username,%username) %dir %_var/log/clamav/
%config(noreplace) %verify(not mtime)    %_sysconfdir/freshclam.conf
%config(noreplace) %verify(not mtime)    %_sysconfdir/logrotate.d/*
%ghost %attr(0664,root,%username) %verify(not size md5 mtime) %freshclamlog

## -----------------------

%files lib
%defattr(-,root,root,-)
%_libdir/*.so.*

## -----------------------

%files devel
%defattr(-,root,root,-)
%_includedir/*
%_libdir/*.so
%_libdir/pkgconfig/*
%_bindir/clamav-config

## -----------------------

%files filesystem
%attr(-,%username,%username) %dir %homedir
%attr(-,root,root)           %dir %pkgdatadir

## -----------------------

%files data
%defattr(-,%username,%username,-)
%homedir/install/*.cvd

%files server
%defattr(-,root,root,-)
%config(noreplace) %_sysconfdir/clamd.conf
/usr/lib/tmpfiles.d/clamd.conf
%_mandir/man[58]/clamd*
%_sbindir/*
/lib/systemd/system/clamd.service
%dir %_sysconfdir/clamd.d
%ghost %dir %attr(0755,%username,%username) %scanstatedir


%changelog
* Thu Jun 02 2016 ClearFoundation <developer@clearfoundation.com> - 0.99.2-1.clear
- Merged 0.99.2

* Tue Mar 29 2016 Robert Scheck <robert@fedoraproject.org> - 0.99.1-1
- Upgrade to 0.99.1 and updated main.cvd and daily.cvd (#1314115)
- Complain about antivirus_use_jit rather clamd_use_jit (#1295473)

* Tue Mar 29 2016 Robert Scheck <robert@fedoraproject.org> - 0.99-4
- Link using %%{?__global_ldflags} for hardened builds (#1321173)
- Build using -std=gnu++98 (#1307378, thanks to Yaakov Selkowitz)

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.99-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Sun Dec 06 2015 Robert Scheck <robert@fedoraproject.org> - 0.99-2
- Require openssl-devel for clamav-devel
- Change clamav-milter unit for upstream changes (#1287795)

* Wed Dec 02 2015 Robert Scheck <robert@fedoraproject.org> - 0.99-1
- Upgrade to 0.99 and updated daily.cvd (#1287327)

* Tue Jun 30 2015 Robert Scheck <robert@fedoraproject.org> - 0.98.7-3
- Move /etc/tmpfiles.d/ to /usr/lib/tmpfiles.d/ (#1126595)
>>>>>>> epel7

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.98.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Apr 29 2015 Robert Scheck <robert@fedoraproject.org> - 0.98.7-1
- Upgrade to 0.98.7 and updated daily.cvd (#1217014)

* Tue Mar 10 2015 Adam Jackson <ajax@redhat.com> 0.98.6-2
- Drop sysvinit subpackages in F23+

* Thu Jan 29 2015 Robert Scheck <robert@fedoraproject.org> - 0.98.6-1
- Upgrade to 0.98.6 and updated daily.cvd (#1187050)

* Wed Nov 19 2014 Robert Scheck <robert@fedoraproject.org> - 0.98.5-2
- Corrected summary of clamav-server-systemd package (#1165672)

* Wed Nov 19 2014 Robert Scheck <robert@fedoraproject.org> - 0.98.5-1
- Upgrade to 0.98.5 and updated daily.cvd (#1138101)

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.98.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 21 2014 Robert Scheck <robert@fedoraproject.org> - 0.98.4-1
- Upgrade to 0.98.4 and updated daily.cvd (#1111811)
- Add build requirement to libxml2 for DMG, OpenIOC and XAR

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.98.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sat May 10 2014 Robert Scheck <robert@fedoraproject.org> - 0.98.3-1
- Upgrade to 0.98.3 and updated daily.cvd (#1095614)
- Avoid automatic path detection breakage regarding curl
- Added build requirement to openssl-devel for hasing code
- Added clamsubmit to main package

* Wed Jan 15 2014 Robert Scheck <robert@fedoraproject.org> - 0.98.1-1
- Upgrade to 0.98.1 and updated daily.cvd (#1053400)

* Wed Oct 09 2013 Dan Horák <dan[at]danny.cz> - 0.98-2
- Use fanotify from glibc instead of the limited hand-crafted version

* Sun Oct 06 2013 Robert Scheck <robert@fedoraproject.org> - 0.98-1
- Upgrade to 0.98 and updated main.cvd and daily.cvd (#1010168)

* Wed Aug 07 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.97.8-4
- Add a missing requirement on crontabs to spec file
- Fix RHBZ#988605

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.97.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu May 2 2013 Nick Bebout <nb@fedoraproject.org> - 0.97.8-1
- Update to 0.97.8

* Wed Apr 10 2013 Jon Ciesla <limburgher@gmail.com> - 0.97.7-2
- Migrate from fedora-usermgmt to guideline scriptlets.

* Sat Mar 23 2013 Nick Bebout <nb@fedoraproject.org> - 0.97.7-1
- Update to 0.97.7

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.97.6-1901
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Sep 22 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.6-1900
- updated to 0.97.6
- use %%systemd macros

* Tue Aug 14 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.5-1900
- disabled upstart support

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.97.5-1801
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jun 16 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.5-1800
- updated to 0.97.5
- CVE-2012-1457: allows to bypass malware detection via a TAR archive
  entry with a length field that exceeds the total TAR file size
- CVE-2012-1458: allows to bypass malware detection via a crafted
  reset interval in the LZXC header of a CHM file
- CVE-2012-1459: allows to bypass malware detection via a TAR archive
  entry with a length field corresponding to that entire entry, plus
  part of the header of the next entry
- ship local copy of virus database; it was removed by accident from
  0.97.5 tarball
- removed sysv compat stuff

* Fri Apr 13 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.4-1801
- build with -fPIE

* Fri Mar 16 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.4-1800
- updated to 0.97.4

* Sun Feb  5 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.3-1703
- fixed SELinux restorecon invocation
- added trigger to fix SELinux contexts of logfiles created by old
  packages
- fixed build with recent gcc/glibc toolchain

* Sat Jan 21 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.3-1703
- rewrote clamav-notify-servers to be init system neutral
- set PrivateTmp systemd option (#782488)

* Sun Jan  8 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.3-1702
- set correct SELinux context for logfiles generated in %%post (#754555)
- create systemd tmpfiles in %%post
- created -server-systemd subpackage providing a clamd@.service template
- made script in -scanner-systemd an instance of clamd@.service

* Tue Oct 18 2011 Nick Bebout <nb@fedoraproject.org> - 0.97.3-1700
- updated to 0.97.3
- CVE-2011-3627 clamav: Recursion level crash fixed in v0.97.3

* Thu Aug  4 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.2-1700
- moved sysv wrapper script into -sysv subpackage
- start systemd services after network.target and nss-lookup.target

* Tue Jul 26 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.2-1600
- updated to 0.97.2
- CVE-2011-2721 Off-by-one error by scanning message hashes (#725694)
- fixed systemd scripts and their installation

* Thu Jun  9 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97.1-1600
- updated to 0.97.1
- fixed Requires(preun) vs. Requires(postun) inconsistency

* Sat Apr 23 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97-1601
- fixed tmpfiles.d syntax (#696812)

* Sun Feb 20 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.97-1600
- updated to 0.97
- rediffed some patches

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.96.5-1503
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Jan  8 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.5-1502
- fixed signal specifier in clamd-wrapper (#668131, James Ralston)

* Fri Dec 24 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.5-1501
- added systemd init scripts which obsolete to old sysvinit ones
- added tmpfiles.d/ descriptions

* Sat Dec  4 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.5-1500
- updated to 0.96.5
- CVE-2010-4260 Multiple errors within the processing of PDF files can
  be exploited to e.g. cause a crash.
- CVE-2010-4261 An off-by-one error within the "icon_cb()" function
  can be exploited to cause a memory corruption.

* Sun Oct 31 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.4-1500
- updated to 0.96.4
- execute 'make check' (#640347) but ignore errors for now because
  four checks are failing on f13

* Wed Sep 29 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.3-1501
- lowered stop priority of sysv initscripts (#629435)

* Wed Sep 22 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.3-1500
- updated to 0.96.3
- fixes CVE-2010-0405 in shipped bzlib.c copy

* Sun Aug 15 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.2-1500
- updated to 0.96.2
- rediffed patches
- removed the -jit-disable patch which is replaced upstream by a more
  detailed configuration option.

* Wed Aug 11 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
- removed old %%trigger which renamed the 'clamav' user- and groupnames
  to 'clamupdate'
- use 'groupmems', not 'usermod' to add a user to a group because
  'usermod' does not work when user does not exist in local /etc/passwd

* Tue Jul 13 2010 Dan Horák <dan[at]danny.cz> - 0.96.1-1401
- ocaml not available (at least) on s390(x)

* Tue Jun  1 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96.1-1400
- updated to 0.96.1
- rediffed patches

* Sat May 29 2010 Rakesh Pandit <rakesh@fedoraproject.org> - 0.96.1403
- CVE-2010-1639 Clam AntiVirus: Heap-based overflow, when processing malicious PDF file(s)

* Wed Apr 21 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96-1402
- updated to final 0.96
- applied upstream patch which allows to disable JIT compiler (#573191)
- build JIT compiler again
- disabled JIT compiler by default
- removed explicit 'pkgconfig' requirements in -devel (#533956)

* Sat Mar 20 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96-0.1401.rc1
- do not build the bytecode JIT compiler for now until it can be disabled
  at runtime (#573191)

* Thu Mar 11 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.96-1400.rc1
- updated to 0.96rc1
- added some BRs

* Sun Dec  6 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.3-1301
- updated -upstart to upstart 0.6.3

* Sat Nov 21 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
- adjusted chkconfig positions for clamav-milter (#530101)
- use %%apply instead of %%patch

* Thu Oct 29 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.3-1300
- updated to 0.95.3

* Sun Sep 13 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
- conditionalized build of noarch subpackages to ease packaging under RHEL5

* Sun Aug  9 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.2-5
- modified freshclam configuration to log by syslog by default
- disabled LocalSocket option in sample configuration
- fixed clamav-milter sysv initscript to use bash interpreter and to
  be disabled by default

* Sat Aug  8 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.2-4
- renamed 'clamav' user/group to 'clamupdate'
- add the '%milteruser' user to the '%scanuser' group when the -scanner
  subpackage is installed

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.95.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jun 11 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.2-1
- updated to 0.95.2

* Sun Apr 19 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.1-3
- fixed '--without upstart' operation

* Wed Apr 15 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95.1-2
- added '%%bcond_without upstart' conditional to ease skipping of
  -upstart subpackage creation e.g. on EL5 systems
- fixed Provides/Obsoletes: typo in -milter-sysvinit subpackage which
  broke update path

* Fri Apr 10 2009 Robert Scheck <robert@fedoraproject.org> - 0.95.1-1
- Upgrade to 0.95.1 (#495039)

* Wed Mar 25 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95-1
- updated to final 0.95
- added ncurses-devel (-> clamdtop) BR
- enforced IPv6 support

* Sun Mar  8 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.95-0.1.rc1
- updated to 0.95rc1
- added -upstart subpackages
- renamed -sysv to -sysvinit to make -upstart win the default dep resolving
- reworked complete milter stuff
- added -scanner subpackage which contains a preconfigured daemon
  (e.g. for use by -milter)
- moved %%changelog entries from 2006 and before into ChangeLog-rpm.old

* Wed Feb 25 2009 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.94.2-3
- made some subpackages noarch
- fixed typo in SysV initscript which removes 'touch' file (#473513)

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.94.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Dec 02 2008 Robert Scheck <robert@fedoraproject.org> - 0.94.2-1
- Upgrade to 0.94.2 (#474002)

* Wed Nov 05 2008 Robert Scheck <robert@fedoraproject.org> - 0.94.1-1
- Upgrade to 0.94.1

* Sun Oct 26 2008 Robert Scheck <robert@fedoraproject.org> - 0.94-1
- Upgrade to 0.94 (SECURITY), fixes #461461:
- CVE-2008-1389 Invalid memory access in the CHM unpacker
- CVE-2008-3912 Out-of-memory NULL pointer dereference in mbox/msg
- CVE-2008-3913 Memory leak in code path in freshclam's manager.c
- CVE-2008-3914 Multiple file descriptor leaks on the code paths

* Sun Jul 13 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.93.3-1
- updated to 0.93.3; another fix for CVE-2008-2713 (out-of-bounds read
  on petite files)
- put pid instead of pgrp into pidfile of clamav-milter (bz #452359)
- rediffed patches

* Tue Jun 17 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.93.1-1
- updated to 0.93.1
- rediffed -path patch
- CVE-2008-2713 Invalid Memory Access Denial Of Service Vulnerability

* Mon Apr 14 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.93-1
- updated to final 0.93
- removed daily.inc + main.inc directories; they are now replaced by
  *.cld containers
- trimmed down MAILTO list of cronjob to 'root' again; every well
  configured system has an alias for this recipient

* Wed Mar 12 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.93-0.1.rc1
- moved -milter scriptlets into -milter-core subpackage
- added a requirement on the milteruser to the -milter-sendmail
  subpackage (reported by Bruce Jerrick)

* Tue Mar  4 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.93-0.0.rc1
- updated to 0.93rc1
- fixed rpath issues

* Mon Feb 11 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.92.1-1
- updated to 0.92.1

* Tue Jan  1 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.92-6
- redisabled unrar stuff completely by using clean sources
- splitted -milter subpackage into pieces to allow use without sendmail
  (#239037)

* Tue Jan  1 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.92-5
- use a better way to disable RPATH-generation (needed for '--with
  unrar' builds)

* Mon Dec 31 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.92-4
- added a README.fedora to the milter package (#240610)
- ship original sources again; unrar is now licensed correctly (no more
  stolen code put under GPL). Nevertheless, this license is not GPL
  compatible, and to allow libclamav to be used by GPL applications,
  unrar is disabled by a ./configure switch.
- use pkg-config in clamav-config to emulate --cflags and --libs
  operations (fixes partly multilib issues)
- registered some more auto-updated files and marked them as %%ghost

* Fri Dec 21 2007 Tom "spot" Callaway <tcallawa@redhat.com> - 0.92-3
- updated to 0.92 (SECURITY):
- CVE-2007-6335 MEW PE File Integer Overflow Vulnerability

* Mon Oct 29 2007 Tom "spot" Callaway <tcallawa@redhat.com> - 0.91.2-3
- remove RAR decompression code from source tarball because of
  legal problems (resolves 334371)
- correct license tag

* Mon Sep 24 2007 Jesse Keating <jkeating@redhat.com> - 0.91.2-2
- Bump release for upgrade path.

* Sat Aug 25 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.91.2-1
- updated to 0.91.2 (SECURITY):
- CVE-2007-4510 DOS in RTF parser
- DOS in html normalizer
- arbitrary command execution by special crafted recipients in
  clamav-milter's black-hole mode
- fixed an open(2) issue

* Tue Jul 17 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.91.1-0
- updated to 0.91.1

* Thu Jul 12 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.91-1
- updated to 0.91

* Thu May 31 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90.3-1
- updated to 0.90.3
- BR tcpd.h instead of tcp_wrappers(-devel) to make it build both
  in FC6- and F7+

* Fri Apr 13 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90.2-1
- [SECURITY] updated to 0.90.2; fixes CVE-2007-1745, CVE-2007-1997

* Fri Mar  2 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90.1-2
- BR 'tcp_wrappers-devel' instead of plain 'tcp_wrappers'

* Fri Mar  2 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90.1-1
- updated to 0.90.1
- updated %%doc list

* Sun Feb 18 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90-1
- updated to final 0.90
- removed -visibility patch since fixed upstream

* Sun Feb  4 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90-0.3.rc3
- build with -Wl,-as-needed and cleaned up pkgconfig file
- removed old hack which forced installation of freshclam.conf; related
  check was removed upstream
- removed static library
- removed %%changelog entries from before 2004

* Sat Feb  3 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.90-0.2.rc3
- updated to 0.90rc3
- splitted mandatory parts from the data-file into a separate -filesystem
  subpackage
- added a -data-empty subpackage to allow a setup where database is
  updated per cron-job and user does not want to download the large
  -data package with outdated virus definitations (#214949)
- %%ghost'ed the files downloaded by freshclam
