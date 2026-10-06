#!/bin/bash
set -euo pipefail
: "${NPA_PASSWORD:?NPA_PASSWORD must be set}"
if [[ "$NPA_PASSWORD" == *$'\n'* || "$NPA_PASSWORD" == *$'\r'* ]]; then
    echo 'NPA_PASSWORD must be a single line.' >&2
    exit 1
fi
printf '%s:%s\n' "$NPA_USER" "$NPA_PASSWORD" | chpasswd
unset NPA_PASSWORD
mkdir -p /run/sshd /etc/ssh/host_keys
if [[ ! -s /etc/ssh/host_keys/ssh_host_ed25519_key ]]; then
    ssh-keygen -q -t ed25519 -N '' -f /etc/ssh/host_keys/ssh_host_ed25519_key
fi
if [[ ! -s /etc/ssh/host_keys/ssh_host_rsa_key ]]; then
    ssh-keygen -q -t rsa -b 3072 -N '' -f /etc/ssh/host_keys/ssh_host_rsa_key
fi
/usr/sbin/sshd -t
exec /usr/sbin/sshd -D -e
