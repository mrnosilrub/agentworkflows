"""Optional local release rehearsal; not a Cloudflare or repository-existence check.

Use the same PUPPETEER_MODULE / CHROME_PATH variables as browser.mjs.
The example repository URL below is synthetic test configuration, never deployed.
"""
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    with tempfile.TemporaryDirectory(prefix='agentworkflows-release-') as temp:
        root = Path(temp)
        for name in ('workflows', 'templates', 'skills', 'assets'):
            shutil.copytree(ROOT / name, root / name, symlinks=True)
        for name in ('LICENSE', 'CONTRIBUTING.md'):
            shutil.copyfile(ROOT / name, root / name, follow_symlinks=False)
        (root / 'site.json').write_text(json.dumps({'repository_url': 'https://github.com/example/workflows'}))
        subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--root', str(root), '--production'], check=True)
        dist = root / 'dist'
        header_lines = (dist / '_headers').read_text().splitlines()
        require(header_lines[0] == '/*', 'Expected global header rule')
        headers = [line.strip().split(': ', 1) for line in header_lines[1:] if line.strip()]

        class Handler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                for key, value in headers:
                    self.send_header(key, value)
                super().end_headers()

            def log_message(self, format, *args):
                pass

            def send_error(self, code, message=None, explain=None):
                if code != 404:
                    return super().send_error(code, message, explain)
                body = (dist / '404.html').read_bytes()
                self.send_response(404)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(body)

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(dist)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = 'http://127.0.0.1:' + str(server.server_port)
        try:
            checked = []
            for path in sorted(dist.rglob('*')):
                if not path.is_file() or path.name.startswith(('.', '_')):
                    continue
                route = '/' + path.relative_to(dist).as_posix()
                with urllib.request.urlopen(base + route) as response:
                    require(response.status == 200, 'status mismatch: ' + route)
                    require(response.read() == path.read_bytes(), 'byte mismatch: ' + route)
                    require(response.headers['X-Content-Type-Options'] == 'nosniff', 'missing nosniff: ' + route)
                    require("frame-ancestors 'none'" in response.headers['Content-Security-Policy'], 'missing CSP: ' + route)
                checked.append(route)
            for route in ('/missing-workflow/', '/.git/config', '/.local/production-trial/report.md', '/tools/catalog.py'):
                try:
                    urllib.request.urlopen(base + route)
                    raise AssertionError('Unexpected public path: ' + route)
                except urllib.error.HTTPError as exc:
                    require(exc.code == 404, 'private path status: ' + route)
                    require(exc.read() == (dist / '404.html').read_bytes(), '404 body mismatch')
            env = dict(os.environ, PREVIEW_URL=base, REQUIRE_RELEASE_HEADERS='1')
            subprocess.run(['node', str(ROOT / 'tests/browser.mjs')], cwd=ROOT, env=env, check=True)
            receipt = {'scope': 'local header-applied production-mode rehearsal, synthetic repository URL', 'file_count': len(checked), 'paths': checked, 'private_path_checks': 'pass', 'browser': 'pass', 'cloudflare_verified': False}
            output = ROOT / '.local/qa/release.json'
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(receipt, indent=2) + '\n')
            print(json.dumps(receipt))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    main()
