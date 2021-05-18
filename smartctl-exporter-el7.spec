Name:	  smartctl-exporter
Version:  0.0.3
%global gittag 0.0.3
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
* Tue May 18 2021 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.3-1
- Fixing a bug while reading SSDs counters
- Adding SSDs wear indicator
- Configurable smartd.conf path
- Fixing a bug with smart health indicator
* Mon May 17 2021 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.2-1
- Adding self-test errors count and non-medium errors count
* Fri May 14 2021 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.1-1
- Initial release
