"""Static server for the ABOM website that never calls os.getcwd().

The preview harness spawns its server from a working directory the macOS
sandbox may deny; `python -m http.server` crashes there because its argparse
default is os.getcwd() (evaluated before our --directory is read). This script
passes the docroot explicitly, so the process CWD is never consulted.

Usage: python3 serve.py <port>
"""
import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = "/Users/josephassiga/Desktop/abom/website"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4599

Handler = functools.partial(SimpleHTTPRequestHandler, directory=ROOT)
print(f"serving {ROOT} on http://127.0.0.1:{PORT}", flush=True)
ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
