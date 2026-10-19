"""Isolated, range-capable hot-update test server. Never serves HotUpdateServer/.

Usage: python boot_validation_server.py --root Builds/BootRefactor/Server --port 18000
faults.json in the test root can contain patterns, status, corrupt, delay, kbps.
All faults are confined to this server and recorded in requests.jsonl.
"""
import argparse
import fnmatch
import json
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if root.name != 'Server' or root.parent.name != 'BootRefactor':
        raise SystemExit('Test root must be Builds/BootRefactor/Server')

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)

        def log_message(self, fmt, *values):
            with (root.parent / 'requests.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'time': time.time(), 'client': self.client_address[0], 'message': fmt % values}) + '\n')

        def do_GET(self):
            relative = unquote(urlsplit(self.path).path).lstrip('/')
            try:
                fault = json.loads((root / 'faults.json').read_text())
            except (OSError, ValueError):
                fault = {}
            matched = any(fnmatch.fnmatch(relative, p) for p in fault.get('patterns', []))
            if not matched:
                fault = {}
            if fault.get('delay'):
                time.sleep(min(40, float(fault['delay'])))
            if fault.get('status'):
                self.send_error(int(fault['status']), 'Injected isolated test failure')
                return
            target = (root / relative).resolve()
            if root not in target.parents or not target.is_file():
                self.send_error(404)
                return
            size = target.stat().st_size
            offset = 0
            if self.headers.get('Range', '').startswith('bytes='):
                offset = int(self.headers['Range'].split('=')[1].split('-')[0])
                if offset >= size:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{size}')
                    self.end_headers()
                    return
            self.send_response(206 if offset else 200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(size - offset))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Accept-Ranges', 'bytes')
            if offset:
                self.send_header('Content-Range', f'bytes {offset}-{size-1}/{size}')
            self.end_headers()
            self.log_message('TRANSFER path=%s range=%s fault=%s', relative, self.headers.get('Range', ''), fault)
            try:
                with target.open('rb') as stream:
                    stream.seek(offset)
                    first = True
                    transferred = 0
                    while data := stream.read(16384):
                        if first and fault.get('corrupt'):
                            data = bytes([data[0] ^ 255]) + data[1:]
                        first = False
                        self.wfile.write(data)
                        self.wfile.flush()
                        transferred += len(data)
                        if fault.get('disconnect_after') and transferred >= int(fault['disconnect_after']):
                            self.close_connection = True
                            return
                        if fault.get('kbps'):
                            time.sleep(len(data) / (float(fault['kbps']) * 1024))
            except (ConnectionError, OSError):
                pass

        def do_PUT(self):
            relative = unquote(urlsplit(self.path).path).lstrip('/')
            target = (root / relative).resolve()
            if root not in target.parents:
                self.send_error(403)
                return
            length = int(self.headers.get('Content-Length', '0'))
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.uploading')
            with temporary.open('wb') as stream:
                while length:
                    data = self.rfile.read(min(131072, length))
                    if not data:
                        self.send_error(400)
                        return
                    stream.write(data)
                    length -= len(data)
            temporary.replace(target)
            self.send_response(201)
            self.send_header('Content-Length', '0')
            self.end_headers()

    server = ThreadingHTTPServer(('0.0.0.0', args.port), Handler)
    print(f'Isolated server {root} on {args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
