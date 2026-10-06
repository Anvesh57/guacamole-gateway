#!/bin/sh
set -eu
unset DBUS_SESSION_BUS_ADDRESS SESSION_MANAGER
export XDG_RUNTIME_DIR="/tmp/runtime-$(id -u)"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
exec dbus-run-session -- xfce4-session
