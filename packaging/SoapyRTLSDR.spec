Name:           SoapyRTLSDR
Version:        0.3.3
Release:        1%{?dist}
Summary:        SoapySDR driver module for RTL-SDR devices
License:        MIT
URL:            https://github.com/pothosware/SoapyRTLSDR
Source0:        %{url}/archive/refs/tags/soapy-rtl-sdr-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  SoapySDR-devel
BuildRequires:  rtl-sdr-devel

Requires:       SoapySDR%{?_isa}
Requires:       rtl-sdr%{?_isa}

%description
SoapyRTLSDR is a SoapySDR driver module for RTL-SDR USB receivers.

%prep
%autosetup -n SoapyRTLSDR-soapy-rtl-sdr-%{version}

%build
%cmake
%cmake_build

%install
%cmake_install

%files
%doc README.md
%{_libdir}/SoapySDR/modules*/librtlsdrSupport.so

%changelog
* Mon Jul 27 2026 Jacco <jacco@localhost> - 0.3.3-1
- Initial EL10 package
