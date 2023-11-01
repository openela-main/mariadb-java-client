Name:		mariadb-java-client
Version:	2.7.1
Release:	2%{?dist}
Summary:	Connects applications developed in Java to MariaDB and MySQL databases
# added BSD license because of https://bugzilla.redhat.com/show_bug.cgi?id=1291558#c13
License:	BSD and LGPLv2+
URL:		https://mariadb.com/kb/en/mariadb/about-mariadb-connector-j/
Source0:	https://github.com/mariadb-corporation/mariadb-connector-j/archive/refs/tags/%{version}.tar.gz/mariadb-connector-j-%{version}.tar.gz

# optional dependency not in Fedora
Patch0:		remove_waffle-jna.patch
Patch1:		compliance-for-jna-4.patch

BuildArch:	noarch
BuildRequires:	maven-local
BuildRequires:	mvn(net.java.dev.jna:jna)
BuildRequires:	mvn(net.java.dev.jna:jna-platform)
BuildRequires:	mvn(org.apache.felix:maven-bundle-plugin)
BuildRequires:	mvn(org.codehaus.mojo:build-helper-maven-plugin)
BuildRequires:	mvn(org.osgi:osgi.cmpn)
BuildRequires:	mvn(org.osgi:osgi.core)
BuildRequires:	mvn(org.slf4j:slf4j-api)
# since version 1.5.2 missing optional dependency (windows)
#BuildRequires:	mvn(com.github.dblock.waffle:waffle-jna)

Suggests:	mariadb-server

%description
MariaDB Connector/J is a Type 4 JDBC driver, also known as the Direct to
Database Pure Java Driver. It was developed specifically as a lightweight
JDBC connector for use with MySQL and MariaDB database servers.

%package javadoc
Summary:	Javadoc for %{name}

%description javadoc
This package contains the API documentation for %{name}.

%prep
%setup -qn mariadb-connector-j-%{version}

# convert files from dos to unix line encoding
for file in README.md documentation/*.creole; do
 sed -i.orig 's|\r||g' $file
 touch -r $file.orig $file
 rm $file.orig
done

# remove missing optional dependency waffle-jna
%pom_remove_dep com.github.waffle:waffle-jna
%pom_remove_dep ch.qos.logback:logback-classic
%pom_remove_dep junit:junit
%pom_remove_dep com.amazonaws:aws-java-sdk-rds

# remove and add jna, so that it is stated as
# non-optional dependency
%pom_remove_dep net.java.dev.jna:jna
%pom_add_dep net.java.dev.jna:jna

# change required version of the jna-platform, as mariadb-java-client is patched to
# be compliant also with jna 4
%pom_change_dep net.java.dev.jna:jna-platform net.java.dev.jna:jna-platform:any

# use latest OSGi implementation
%pom_change_dep -r :org.osgi.core org.osgi:osgi.core
%pom_change_dep -r :org.osgi.compendium org.osgi:osgi.cmpn


# also remove the file using the removed plugin
rm -r src/main/java/org/mariadb/jdbc/credential/aws
rm src/main/java/org/mariadb/jdbc/internal/com/send/authentication/gssapi/WindowsNativeSspiAuthentication.java
# patch the sources so that the missing file is not making trouble
%patch0 -p1
%patch1 -p1

%mvn_file org.mariadb.jdbc:%{name} %{name}
%mvn_alias org.mariadb.jdbc:%{name} mariadb:mariadb-connector-java

%pom_remove_plugin org.jacoco:jacoco-maven-plugin
%pom_remove_plugin org.apache.maven.plugins:maven-source-plugin
%pom_remove_plugin org.apache.maven.plugins:maven-javadoc-plugin
%pom_remove_plugin org.sonatype.plugins:nexus-staging-maven-plugin
%pom_remove_plugin com.coveo:fmt-maven-plugin
%pom_remove_plugin -r :maven-gpg-plugin

# remove preconfigured OSGi manifest file and generate OSGi manifest file
# with maven-bundle-plugin instead of using maven-jar-plugin
rm src/main/resources/META-INF/MANIFEST.MF
%pom_xpath_set "pom:packaging" bundle
%pom_xpath_set "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-jar-plugin']/pom:configuration/pom:archive/pom:manifestFile" '${project.build.outputDirectory}/META-INF/MANIFEST.MF'
%pom_xpath_remove "pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-jar-plugin']/pom:configuration/pom:archive/pom:manifestEntries"

%pom_add_plugin org.apache.felix:maven-bundle-plugin:2.5.4 . '
<extensions>true</extensions>
<configuration>
  <instructions>
    <Bundle-SymbolicName>${project.groupId}</Bundle-SymbolicName>
    <Bundle-Name>MariaDB JDBC Client</Bundle-Name>
    <Bundle-Version>${project.version}.0</Bundle-Version>
    <Export-Package>org.mariadb.jdbc.*</Export-Package>
    <Import-Package>
      !com.sun.jna.*,
      javax.net;resolution:=optional,
      javax.net.ssl;resolution:=optional,
      javax.sql;resolution:=optional,
      javax.transaction.xa;resolution:=optional
    </Import-Package>
  </instructions>
</configuration>
<executions>
  <execution>
    <id>bundle-manifest</id>
    <phase>process-classes</phase>
    <goals>
      <goal>manifest</goal>
    </goals>
  </execution>
</executions>'

%build
# tests are skipped, while they require running application server
%mvn_build -f

%install
%mvn_install

%files -f .mfiles
%doc documentation/* README.md
%license LICENSE

%files javadoc -f .mfiles-javadoc
%license LICENSE

%changelog
* Tue May 24 2022 Zuzana Miklankova <zmiklank@redhat.com> - 2.7.1-2
- autogenerate the Requires only for jna, not jna-platform
- change required version of jna-platform to 'any' in pom.xml
  Resolves: #2089627

* Mon Feb 07 2022 Zuzana Miklankova <zmiklank@redhat.com> - 2.7.1-1
- Update to 2.7.1
- Retain compatibility with jna4
- Adjust pom.xml, so that the rpm Requires jna and jna-platform
  Resolves: #2043212

* Fri Jun 26 2020 Michal Schorm <mschorm@redhat.com> - 2.2.5-3
- Fix requirement on MariaDB
  Resolves: #1797057

* Thu Jun 14 2018 Jakub Janco <jjanco@redhat.com> - 2.2.5-1
- update version

* Mon May 28 2018 Michael Simacek <msimacek@redhat.com> - 2.2.3-2
- Remove BR on maven-javadoc-plugin

* Tue Mar 13 2018 Jakub Janco <jjanco@redhat.com> - 2.2.3-1
- update version

* Mon Feb 26 2018 Jakub Janco <jjanco@redhat.com> - 2.2.2-1
- update version

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 03 2018 Jakub Janco <jjanco@redhat.com> - 2.2.1-1
- Update to 2.2.1

* Tue Nov 21 2017 Jakub Janco <jjanco@redhat.com> - 2.2.0-1
- Update to 2.2.0

* Tue Aug 29 2017 Tomas Repik <trepik@redhat.com> - 2.1.0-1
- Update to 2.1.0

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 26 2017 Tomas Repik <trepik@redhat.com> - 2.0.2-1
- version update

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 28 2016 Tomas Repik <trepik@redhat.com> - 1.5.5-1
- version update

* Mon Oct 03 2016 Tomas Repik <trepik@redhat.com> - 1.5.3-1
- version update

* Wed Sep 14 2016 Tomas Repik <trepik@redhat.com> - 1.5.2-1
- version update

* Tue Jun 21 2016 Tomas Repik <trepik@redhat.com> - 1.4.6-1
- version update

* Mon Apr 18 2016 Tomas Repik <trepik@redhat.com> - 1.4.2-1
- version update

* Wed Mar 23 2016 Tomas Repik <trepik@redhat.com> - 1.3.7-1
- version update
- BSD license added
- cosmetic updates in prep phase

* Thu Mar 10 2016 Tomas Repik <trepik@redhat.com> - 1.3.6-1
- version update

* Mon Feb 15 2016 Tomas Repik <trepik@redhat.com> - 1.3.5-1
- version update

* Wed Jan 20 2016 Tomáš Repík <trepik@redhat.com> - 1.3.3-3
- generating OSGi manifest file with maven-bundle-plugin

* Wed Dec 16 2015 Tomáš Repík <trepik@redhat.com> - 1.3.3-2
- installing LICENSE added
- conversion from dos to unix line encoding revised
- unnecessary tasks removed

* Wed Dec  9 2015 Tomáš Repík <trepik@redhat.com> - 1.3.3-1
- Initial package
