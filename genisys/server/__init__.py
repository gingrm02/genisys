#!/usr/bin/env python3
from io import TextIOWrapper
import ssl
import pwd
import grp
import os
import sys
import json
import textwrap
from warnings import warn
from signal import signal, SIGTERM
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing_extensions import Self, Dict, TypedDict, cast
from genisys.config_parser import YAMLParser
import genisys.server.tls

DEFAULT_PORT = 15206
DEFAULT_INVENTORY = "/etc/ansible/hosts"

class ServerOptions(TypedDict):
    port: int
    user: str
    group: str
    ssl: Dict[str, str]

class GenisysHTTPRequestHandler(BaseHTTPRequestHandler):
    """Process client "hello"s by running ansible playbooks on a received POST"""
    def do_POST(self: Self):
        """On POST, store the client in the Ansible inventory and run playbooks"""
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        print(body)
        self.wfile.write(bytes(textwrap.dedent("""\
        HTTP/1.1 200 OK
        Content-Type: text/plain
        Content-Length: 7

        Success"""), encoding='utf-8'))

class GenisysHTTPServer(HTTPServer):
    """HTTP Server wrapper to allow server global variables to be used for processing requests"""
    inventory_file: TextIOWrapper

def run(config: YAMLParser):
    """Drops priviledges, creates the server (with SSL, if applicable), then waits for requests"""
    # parse config
    network = config.get_section("Network")
    server_options = cast(ServerOptions, network.get("server", {}) or {})

    # drop priviledges
    if not drop_priviledges(server_options):
        warn("Unable to drop privledges to the specified user. Continuing as current user.")

    # create a server
    server_address = network.get('ip', '')
    server_port = server_options.get("port", DEFAULT_PORT)
    httpd = GenisysHTTPServer((server_address, server_port), GenisysHTTPRequestHandler)

    # apply TLS if applicable
    if 'ssl' in server_options:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_cert = genisys.server.tls.get_keychain(server_options['ssl'] or {})
        ssl_context.load_cert_chain(**ssl_cert)
        httpd.socket = ssl_context.wrap_socket(httpd.socket)

    # install additional data for the server to use
    ansible_cfg = config.get_section("ansible")
    inventory_path = ansible_cfg.get("inventory", DEFAULT_INVENTORY)
    httpd.inventory_file = open(inventory_path, 'w', encoding='utf-8')

    # run until SIGTERM is caught
    def sigterm_handler(*_):
        print("killed")
        httpd.inventory_file.close()
        sys.exit(SIGTERM)
    signal(SIGTERM, sigterm_handler)
    httpd.serve_forever()

def drop_priviledges(config: ServerOptions) -> bool:
    """Attempts to drop the priviledges to that of the specified users, returns false on failure"""
    if 'user' not in config:
        warn("No user specified. Continuing as current user.")
        return True

    grpnam = config.get('group', config['user'])
    uid = pwd.getpwnam(config['user'])
    gid = grp.getgrnam(grpnam)

    try:
        os.setuid(uid.pw_uid)
        os.setgid(gid.gr_gid)
        return True
    except PermissionError:
        return False
