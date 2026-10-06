#!/bin/bash
set -euo pipefail
: "${NPA_PASSWORD:?NPA_PASSWORD must be set}"
if [[ "$NPA_PASSWORD" == *$'\n'* || "$NPA_PASSWORD" == *$'\r'* ]]; then
    echo 'NPA_PASSWORD must be a single line.' >&2
    exit 1
fi
printf 'npa_desktop:%s\n' "$NPA_PASSWORD" | chpasswd
unset NPA_PASSWORD

mkdir -p /run/dbus /run/xrdp/sockdir
chown xrdp:xrdp /run/xrdp /run/xrdp/sockdir
chmod 2775 /run/xrdp
chmod 3777 /run/xrdp/sockdir
rm -f /run/xrdp/*.pid /run/dbus/pid
dbus-uuidgen --ensure=/etc/machine-id

# Replace distribution snake-oil links with a container-local TLS certificate.
if [[ ! -f /etc/xrdp/.playground-certificate ]]; then
    rm -f /etc/xrdp/cert.pem /etc/xrdp/key.pem
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout /etc/xrdp/key.pem -out /etc/xrdp/cert.pem \
        -days 3650 -subj '/CN=linux-desktop' >/dev/null 2>&1
    chown root:ssl-cert /etc/xrdp/key.pem
    chmod 640 /etc/xrdp/key.pem
    touch /etc/xrdp/.playground-certificate
fi

exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/playground.conf
