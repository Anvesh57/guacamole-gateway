#!/usr/bin/env python3
"""Render LDAP seed/config safely; passwords are never interpolated as LDIF."""
import base64
import hashlib
import os
from pathlib import Path
import re
import sys


def password(name):
    value = os.environ.get(name, "")
    if not value or any(c in value for c in "\r\n\0"):
        raise ValueError(f"{name} must be nonempty and contain no newlines or NUL")
    return value


def b64(value):
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def ssha(value):
    salt = os.urandom(16)
    digest = hashlib.sha1(value.encode("utf-8") + salt).digest()
    return "{SSHA}" + base64.b64encode(digest + salt).decode("ascii")


def render(mode, template):
    if mode == "config":
        values = {"ROOT_PASSWORD_HASH": ssha(password("LDAP_ADMIN_PASSWORD"))}
    elif mode == "seed":
        values = {
            "BOB_PASSWORD_HASH_B64": b64(ssha(password("BOB_PASSWORD"))),
            "ALICE_PASSWORD_HASH_B64": b64(ssha(password("ALICE_PASSWORD"))),
            "DESKTOP_PASSWORD_PARAMETER_B64": b64("password=" + password("NPA_DESKTOP_PASSWORD")),
            "SSH1_PASSWORD_PARAMETER_B64": b64("password=" + password("NPA_SSH1_PASSWORD")),
            "SSH2_PASSWORD_PARAMETER_B64": b64("password=" + password("NPA_SSH2_PASSWORD")),
        }
    else:
        raise ValueError("mode must be config or seed")
    return re.sub(r"@@([A-Z0-9_]+)@@", lambda m: values[m[1]], template)


if __name__ == "__main__":
    try:
        mode, source, destination = sys.argv[1:]
        Path(destination).write_text(render(mode, Path(source).read_text()), encoding="utf-8")
    except (ValueError, KeyError) as exc:
        sys.exit(f"LDAP configuration error: {exc}")
