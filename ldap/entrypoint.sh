#!/bin/sh
set -eu
umask 077

install -d -m 0750 -o openldap -g openldap /run/slapd /var/lib/ldap
python3 /opt/ldap/render.py config /etc/ldap/slapd.conf.template /run/slapd/slapd.conf
chown root:openldap /run/slapd/slapd.conf
chmod 640 /run/slapd/slapd.conf
slaptest -f /run/slapd/slapd.conf -u

if [ ! -f /var/lib/ldap/data.mdb ]; then
    python3 /opt/ldap/render.py seed /opt/ldap/seed.ldif.template /run/slapd/seed.ldif
    slapadd -f /run/slapd/slapd.conf -l /run/slapd/seed.ldif
    rm -f /run/slapd/seed.ldif
    chown -R openldap:openldap /var/lib/ldap
    echo 'LDAP initialized: two people, two access groups, three connections.'
else
    echo 'Using existing LDAP data; seed and membership changes are preserved.'
fi

exec slapd -f /run/slapd/slapd.conf -h 'ldap://0.0.0.0:389/' -u openldap -g openldap -d 0
