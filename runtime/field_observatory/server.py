"""Loopback app server with explicit static routes and opt-in API execution."""
import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from .prompts import ROOT, compile_prompt, encoded


def make_server(session, port=8768):
    nonce = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, status, value, content_type='application/json; charset=utf-8'):
            data = value if isinstance(value, bytes) else encoded(value)
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.valid_host():
                return self.respond(403, {'error': 'Loopback host required'})
            path = urlsplit(self.path).path
            if path == '/api/session':
                return self.respond(200, {**session.info(), 'nonce': nonce})
            files = {'/': ROOT / 'app/index.html'}
            for folder in ('app', 'data', 'prompts'):
                for file in (ROOT / folder).rglob('*'):
                    if file.is_file() and not file.is_symlink() and file.suffix in ('.html', '.css', '.js', '.json', '.md'):
                        files['/' + str(file.relative_to(ROOT))] = file
            file = files.get(path)
            if not file or not file.resolve().is_relative_to(ROOT):
                return self.respond(404, {'error': 'Not found'})
            kind = mimetypes.guess_type(file.name)[0] or 'text/plain'
            self.respond(200, file.read_bytes(), kind + '; charset=utf-8')

        def do_POST(self):
            if not self.valid_host() or self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}':
                return self.respond(403, {'error': 'Same-origin request required'})
            if not secrets.compare_digest(self.headers.get('X-Observatory-Nonce', ''), nonce):
                return self.respond(403, {'error': 'Session token required'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 20000 or self.headers.get_content_type() != 'application/json':
                    raise ValueError('Expected a bounded JSON request')
                self.connection.settimeout(10)
                value = json.loads(self.rfile.read(length))
                if not isinstance(value, dict):
                    raise ValueError('Expected an object')
                if self.path == '/api/preview':
                    result = compile_prompt(value.get('preset', 'quiet-dialogue'), value.get('mode', 'structured'),
                                            language=value.get('language', 'en'), field_ids=value.get('fields'))
                elif self.path == '/api/run':
                    result = session.run(value.get('input'), value.get('preset', 'quiet-dialogue'), value.get('mode', 'structured'),
                                         language=value.get('language', 'en'), field_ids=value.get('fields'))
                else:
                    return self.respond(404, {'error': 'Not found'})
                self.respond(200, result)
            except (ValueError, TypeError, KeyError):
                self.respond(400, {'error': 'Check the input, selection and execution budget.', 'code': 'invalid_request'})
            except Exception:
                self.respond(500, {'error': 'The operation could not be completed. It will not be retried automatically.', 'code': 'request_failed'})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)
