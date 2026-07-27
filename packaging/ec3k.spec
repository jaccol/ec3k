Name:           ec3k
Version:        1.2.1
Release:        1%{?dist}
Summary:        Receive EnergyCount 3000 transmissions with RTL-SDR
License:        GPL-3.0-or-later
URL:            https://github.com/jaccol/ec3k
Source0:        %{name}-%{version}.tar.gz
BuildArch:       noarch

BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-devel
BuildRequires:  python3-pytest
BuildRequires:  python3-setuptools >= 68
BuildRequires:  python3-wheel

Requires:       python3-gnuradio >= 3.10
Requires:       SoapySDR
Requires:       SoapyRTLSDR
Requires:       rtl-sdr

%description
ec3k receives and decodes EnergyCount 3000 power-sensor transmissions using
an RTL-SDR receiver. It writes a stable tab-separated record for each valid
packet and can optionally produce JSON Lines output.

%prep
%autosetup

%generate_buildrequires
%pyproject_buildrequires -r

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files capture ec3k

%check
%pytest

%files -f %{pyproject_files}
%license LICENSE
%doc README.rst HISTORY
%{_bindir}/capture.py
%{_bindir}/ec3k_recv

%changelog
* Mon Jul 27 2026 Jacco <jacco@localhost> - 1.2.1-1
- Calibrate the GNU Radio default frequency and restore hexadecimal JSON IDs

* Mon Jul 27 2026 Jacco <jacco@localhost> - 1.2.0-1
- Modernize for Python 3, GNU Radio 3.10, and SoapyRTLSDR
