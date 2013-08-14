# bcond default logic is nicely backwards...
%bcond_without tcl
%bcond_with static
%bcond_without check

%define rpmver 2.2.1

Summary: AES encryption for SQLite databases
Name: sqlcipher
Version: %{rpmver}
Release: 1%{?dist}
License: BSD
Group: Applications/Databases
URL: http://sqlcipher.net/
Source0: https://github.com/sqlcipher/sqlcipher/archive/v%{version}.tar.gz
# Shut up stupid tests depending on system settings of allowed open fd's
Patch1: sqlite-3.7.7.1-stupid-openfiles-test.patch
# Shut up pagecache overflow test whose expected result depends on compile
# options and whatnot. Dunno why this started failing in 3.7.10 but
# doesn't seem particularly critical...
Patch2: sqlite-3.7.10-pagecache-overflow-test.patch
# sqlite >= 3.7.10 is buggy if malloc_usable_size() is detected, disable it:
# https://bugzilla.redhat.com/show_bug.cgi?id=801981
# http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=665363
Patch3: sqlcipher-3.7.15-no-malloc-usable-size.patch
BuildRequires: ncurses-devel readline-devel glibc-devel
BuildRequires: autoconf
BuildRequires: openssl-devel
%if %{with tcl}
BuildRequires: /usr/bin/tclsh
BuildRequires: tcl-devel
%{!?tcl_version: %global tcl_version 8.5}
%{!?tcl_sitearch: %global tcl_sitearch %{_libdir}/tcl%{tcl_version}}
%endif
BuildRoot: %{_tmppath}/%{name}-root

%description
 SQLCipher is a C library that implements an encryption in the SQLite 3
 database engine.  Programs that link with the SQLCipher library can have SQL
 database access without running a separate RDBMS process.  It allows one to
 have per-database or page-by-page encryption using AES-256 from Open

 SQLCipher has a small footprint and great performance so it’s ideal for
 protecting embedded application databases and is well suited for mobile
 development.
 
  * as little as 5-15% overhead for encryption
  * 100% of data in the database file is encrypted
  * Uses good security practices (CBC mode, key derivation)
  * Zero-configuration and application level cryptography
  * Algorithms provided by the peer reviewed OpenSSL crypto library.

 SQLCipher has broad platform support for with C/C++, Obj-C, QT, Win32/.NET,
 Java, Python, Ruby, Linux, Mac OS X, iPhone/iOS, Android, Xamarin.iOS, and
 Xamarin.Android.

 SQLCipher v2.1.1 is based on SQLite3 v3.7.17.

%package devel
Summary: Development tools for the sqlite3 embeddable SQL database engine
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}
Requires: pkgconfig

%description devel
This package contains the header files and development documentation 
for %{name}. If you like to develop programs using %{name}, you will need 
to install %{name}-devel.

%if %{with tcl}
%package tcl
Summary: Tcl module for the sqlite3 embeddable SQL database engine
Group: Development/Languages
Requires: %{name} = %{version}-%{release}
Requires: tcl(abi) = %{tcl_version}

%description tcl
This package contains the tcl modules for %{name}.
%endif

%prep
%setup -q
%patch1 -p1 -b .stupid-openfiles-test
%patch2 -p1 -b .pagecache-overflow-test
%patch3 -p1 -b .no-malloc-usable-size

autoconf # Rerun with new autoconf to add support for aarm64

%build
export CFLAGS="$RPM_OPT_FLAGS -DSQLITE_HAS_CODEC -DSQLITE_ENABLE_COLUMN_METADATA=1 -DSQLITE_DISABLE_DIRSYNC=1 -DSQLITE_ENABLE_FTS3=3 -DSQLITE_ENABLE_RTREE=1 -DSQLITE_SECURE_DELETE=1 -DSQLITE_ENABLE_UNLOCK_NOTIFY=1 -Wall -fno-strict-aliasing"
%configure %{!?with_tcl:--disable-tcl} \
           --enable-threadsafe \
           --enable-threads-override-locks \
           --enable-load-extension \
           %{?with_tcl:TCLLIBDIR=%{tcl_sitearch}/sqlcipher}

# rpath removal
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=${RPM_BUILD_ROOT} install

install -D -m0644 sqlcipher.1 $RPM_BUILD_ROOT/%{_mandir}/man1/sqlcipher.1

%if %{with tcl}
# fix up permissions to enable dep extraction
chmod 0755 ${RPM_BUILD_ROOT}/%{tcl_sitearch}/sqlcipher/*.so
%endif

%if ! %{with static}
rm -f $RPM_BUILD_ROOT/%{_libdir}/*.{la,a}
%endif

%if %{with check}
%check
# XXX shell tests are broken due to loading system libsqlite3, work around...
#export LD_LIBRARY_PATH=`pwd`/.libs
#export MALLOC_CHECK_=3
make testfixture
%ifarch s390 s390x ppc ppc64 %{sparc} %{arm}
./testfixture test/crypto.test || : 
%else
./testfixture test/crypto.test
%endif
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-, root, root)
%doc README
%{_bindir}/sqlcipher
%{_libdir}/*.so.*
%{_mandir}/man?/*

%files devel
%defattr(-, root, root)
%{_includedir}/sqlcipher/*.h
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
%if %{with static}
%{_libdir}/*.a
%exclude %{_libdir}/*.la
%endif

%if %{with tcl}
%files tcl
%defattr(-, root, root)
%{tcl_sitearch}/sqlcipher
%endif

%changelog
* Tue Aug 13 2013 Abel Luck <abel@outcomedubious.im> - 2.2.1-1
- Initial SQLCipher package based on SQLite 3.7.17

