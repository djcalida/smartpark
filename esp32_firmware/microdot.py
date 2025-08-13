# main.py -- put your code here!# microdot.py - Minimal Microdot server for MicroPython (by Miguel Grinberg)
# https://github.com/miguelgrinberg/microdot

import ure as re
import usocket as socket

class Request:
    def __init__(self, reader):
        self.reader = reader
        self.method = None
        self.path = None
        self.headers = {}

    async def read(self):
        request_line = await self.reader.readline()
        if not request_line:
            return
        self.method, self.path, _ = request_line.decode().split()
        while True:
            line = await self.reader.readline()
            if line == b'' or line == b'\r\n':
                break
            header, value = line.decode().split(":", 1)
            self.headers[header.strip()] = value.strip()

class Response:
    default_content_type = 'text/plain'

    def __init__(self, body='', status_code=200, headers=None):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

    def to_bytes(self):
        lines = [f'HTTP/1.0 {self.status_code} OK']
        self.headers.setdefault('Content-Type', self.default_content_type)
        self.headers.setdefault('Content-Length', str(len(self.body)))
        for header, value in self.headers.items():
            lines.append(f'{header}: {value}')
        lines.append('')
        lines.append(self.body)
        return '\r\n'.join(lines).encode()

class Microdot:
    def __init__(self):
        self.routes = {}

    def route(self, path, methods=['GET']):
        def decorator(func):
            self.routes[(path, tuple(methods))] = func
            return func
        return decorator

    def run(self, host='0.0.0.0', port=80):
        addr = socket.getaddrinfo(host, port)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        print(f'Microdot is running on http://{host}:{port}')
        while True:
            client, addr = s.accept()
            try:
                request_line = client.readline()
                if not request_line:
                    client.close()
                    continue
                method, path, _ = request_line.decode().split()
                while True:
                    line = client.readline()
                    if not line or line == b'\r\n':
                        break
                for (route_path, route_methods), handler in self.routes.items():
                    if path == route_path and method in route_methods:
                        response = handler(Request(None))
                        if isinstance(response, str):
                            response = Response(response)
                        client.send(response.to_bytes())
                        break
                else:
                    client.send(Response('Not found', 404).to_bytes())
            except Exception as e:
                client.send(Response('Internal server error', 500).to_bytes())
            finally:
                client.close()
