#!/usr/bin/env python3
"""Guacamole 1.6.0 API/RBAC and remote-display smoke test, standard library only."""
import argparse
import codecs
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

BASE = os.environ.get("GUAC_URL", "http://localhost:8080/guacamole").rstrip("/")
EXPECTED = {
    "bob": {"Linux Server 1": "ssh", "Linux Server 2": "ssh"},
    "alice": {"Linux Desktop": "rdp"},
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def request(path, *, form=None, token=None, method=None, data=None, headers=None, timeout=35):
    if token:
        path += ("&" if "?" in path else "?") + urlencode({"token": token})
    headers = dict(headers or {})
    if form is not None:
        data = urlencode(form, doseq=True).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    return urlopen(Request(BASE + path, data=data, headers=headers, method=method), timeout=timeout)


def api(path, **kwargs):
    with request("/api" + path, **kwargs) as response:
        data = response.read()
    return json.loads(data) if data else None


def login(username, password):
    return api("/tokens", form={"username": username, "password": password})


def logout(session):
    try:
        api("/tokens/" + quote(session["authToken"], safe=""), method="DELETE")
    except (HTTPError, URLError, TimeoutError):
        pass


def wait_for_portal():
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            with request("/", timeout=5) as response:
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            pass
        time.sleep(2)
    raise RuntimeError("Guacamole did not become ready in 180 seconds")


def denied(action, label):
    try:
        result = action()
    except HTTPError as exc:
        require(exc.code in (401, 403, 404), f"{label}: unexpected HTTP {exc.code}")
        print(f"PASS {label}")
        return
    if hasattr(result, "close"):
        result.close()
    raise RuntimeError(f"{label}: access unexpectedly succeeded")


def connect(session, connection_id):
    return request("/tunnel?connect", form={
        "token": session["authToken"],
        "GUAC_DATA_SOURCE": session["dataSource"],
        "GUAC_ID": connection_id,
        "GUAC_TYPE": "c",
        "GUAC_WIDTH": "1024",
        "GUAC_HEIGHT": "768",
        "GUAC_DPI": "96",
        "GUAC_IMAGE": ["image/png", "image/jpeg"],
        "GUAC_TIMEZONE": "Etc/UTC",
    })


class Parser:
    """Length-prefixed Guacamole instructions, including partial UTF-8 input."""
    def __init__(self):
        self.buffer = ""
        self.decoder = codecs.getincrementaldecoder("utf-8")()

    def feed(self, data):
        self.buffer += self.decoder.decode(data)
        while self.buffer:
            position, fields = 0, []
            while True:
                dot = self.buffer.find(".", position)
                if dot < 0:
                    return
                digits = self.buffer[position:dot]
                require(digits.isdigit(), "Invalid instruction length")
                length = int(digits)
                require(length <= 16_000_000, "Instruction exceeds smoke-test limit")
                end = dot + 1 + length
                if len(self.buffer) <= end:
                    return
                fields.append(self.buffer[dot + 1:end])
                separator = self.buffer[end]
                require(separator in ",;", "Invalid instruction separator")
                position = end + 1
                if separator == ";":
                    self.buffer = self.buffer[position:]
                    yield fields
                    break


def instruction(*parts):
    return (",".join(f"{len(str(p))}.{p}" for p in parts) + ";").encode("utf-8")


def check_stream(session, connection):
    with connect(session, connection["identifier"]) as response:
        tunnel_id = response.read().decode("ascii").strip()
        tunnel_token = response.headers.get("Guacamole-Tunnel-Token")
    require(tunnel_token and tunnel_id, "Tunnel did not return its session token")
    headers = {"Guacamole-Tunnel-Token": tunnel_token, "Content-Type": "application/octet-stream"}

    def write(data):
        with request("/tunnel?write:" + tunnel_id, data=data, headers=headers, timeout=5) as response:
            response.read()

    parser = Parser()
    have_size = have_drawing = False
    deadline = time.monotonic() + 45
    try:
        with request("/tunnel?read:" + tunnel_id + ":0", headers=headers) as stream:
            while time.monotonic() < deadline:
                chunk = stream.read1(65536)
                require(chunk, f"{connection['name']}: remote stream closed")
                for fields in parser.feed(chunk):
                    opcode = fields[0]
                    if opcode == "error":
                        raise RuntimeError(f"{connection['name']}: Guacamole error: {' '.join(fields[1:])}")
                    if opcode == "disconnect":
                        raise RuntimeError(f"{connection['name']}: disconnected before display output")
                    if opcode == "size" and fields[1] == "0":
                        have_size = int(fields[2]) > 0 and int(fields[3]) > 0
                    if opcode in ("img", "png", "jpeg", "copy", "cfill"):
                        have_drawing = True
                    if opcode == "blob":
                        # Acknowledge each stream chunk, as a browser client would.
                        write(instruction("ack", fields[1], "OK", "0"))
                    if opcode == "sync":
                        write(instruction("sync", fields[1]))
                        if have_size and have_drawing:
                            print(f"PASS {connection['name']}: {connection['protocol'].upper()} tunnel produced display output")
                            return
        raise RuntimeError(f"{connection['name']}: no display output within 45 seconds")
    finally:
        try:
            write(instruction("disconnect"))
        except (HTTPError, URLError, TimeoutError):
            pass


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--matrix-only", action="store_true", help="Skip opening remote sessions")
    args.add_argument("--bob-extra-desktop", action="store_true", help="For the group-change demonstration only")
    options = args.parse_args()
    expected = {user: dict(items) for user, items in EXPECTED.items()}
    if options.bob_extra_desktop:
        expected["bob"]["Linux Desktop"] = "rdp"

    wait_for_portal()
    sessions, connections = {}, {}
    try:
        for username in ("bob", "alice"):
            password = os.environ.get(username.upper() + "_PASSWORD", "")
            require(password, f"Set {username.upper()}_PASSWORD")
            session = sessions[username] = login(username, password)
            require(session["dataSource"] == "ldap", f"{username}: authentication source is not LDAP")
            require(set(session["availableDataSources"]) == {"ldap"}, "Unexpected non-LDAP data source")
            records = api("/session/data/ldap/connections", token=session["authToken"])
            connections[username] = records
            actual = {item["name"]: item["protocol"] for item in records.values()}
            require(actual == expected[username], f"{username}: expected {expected[username]}, got {actual}")
            print(f"PASS {username}: LDAP login; visible machines = {', '.join(sorted(actual))}")

        denied(lambda: login("bob", "Definitely-Wrong-Password"), "wrong portal password is rejected")
        denied(lambda: login("npa_ssh1", "not-a-portal-account"), "target NPA is not a portal user")

        for username, other in (("bob", "alice"), ("alice", "bob")):
            session = sessions[username]
            for cid, connection in connections[other].items():
                if connection["name"] in expected[username]:
                    continue
                path = "/session/data/ldap/connections/" + quote(cid, safe="")
                denied(lambda p=path: api(p, token=session["authToken"]),
                       f"{username} cannot retrieve {connection['name']} by ID")
                denied(lambda c=cid: connect(session, c),
                       f"{username} cannot open a tunnel to {connection['name']}")

        if not options.matrix_only:
            for username, records in connections.items():
                for connection in records.values():
                    check_stream(sessions[username], connection)
        print("PASS all requested checks. Complete the README's visual/NPA identity check in your browser.")
    finally:
        for session in sessions.values():
            logout(session)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, ValueError, HTTPError, URLError, TimeoutError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        sys.exit(1)
