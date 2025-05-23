#!/usr/bin/env python3
"""
MPRIS Server for PrestoDeck
--------------------------
A web server to expose MPRIS media player interfaces over HTTP/HTTPS
"""
from flask import Flask
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from config import DEFAULT_PORT
from modules.player_monitor import start_monitor_thread
from utils.ssl_utils import create_ssl_context, get_server_ip
from modules.auth import API_TOKEN
from api.routes import register_routes

DBusGMainLoop(set_as_default=True)

app = Flask(__name__)

register_routes(app)

if __name__ == '__main__':
    ssl_context = create_ssl_context()
    ip_address = get_server_ip()
    
    port = DEFAULT_PORT
    
    print(f"\nServer running at: https://{ip_address}:{port}")
    print(f"\nAdd to your env file:")
    print(f"MPRIS_API_TOKEN = \"{API_TOKEN}\"")
    print(f"MPRIS_SERVER_URL = \"https://{ip_address}:{port}\"")
    
    monitor_thread = start_monitor_thread()
    app.run(host='0.0.0.0', port=port, ssl_context=ssl_context)
