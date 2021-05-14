Name:	  smartctl-exporter
Version:  0.0.1
%global gittag 0.0.1
Release:  1%{?dist}
Summary:  Prometheus exporter for smartctl stats

License:  Apache License 2.0
URL:      https://github.com/guilbaults/smartctl-exporter
Source0:  https://github.com/guilbaults/%{name}/archive/v%{gittag}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:	systemd
Requires:       python2-prometheus_client

%description
Prometheus exporter for smartctl stats

%prep
%autosetup -n %{name}-%{gittag}
%setup -q

%build

%install
mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{_unitdir}

sed -i -e '1i#!/usr/bin/python' smartctl-exporter.py
install -m 0755 %{name}.py %{buildroot}/%{_bindir}/%{name}
install -m 0644 smartctl-exporter.service %{buildroot}/%{_unitdir}/smartctl-exporter.service

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_bindir}/%{name}
%{_unitdir}/smartctl-exporter.service

%changelog
* Fri May 14 2021 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.1-1
- Initial release
