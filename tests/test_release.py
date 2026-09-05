import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
import test_build
ROOT = test_build.ROOT


class ReleaseTests(unittest.TestCase):
    root: test_build.Path
    setUp = test_build.BuildTests.setUp
    build = test_build.BuildTests.build
    def test_production_requires_repository_before_replacing_preview(self):
        self.assertEqual(self.build().returncode, 0)
        before = (self.root / 'dist/index.html').read_bytes()
        result = subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--root', str(self.root), '--production'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('repository', result.stderr)
        self.assertEqual((self.root / 'dist/index.html').read_bytes(), before)

    def test_preview_rebuild_removes_production_discovery(self):
        (self.root / 'site.json').write_text(json.dumps({'repository_url': 'https://github.com/example/library'}))
        result = subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--root', str(self.root), '--production'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.build().returncode, 0)
        self.assertFalse((self.root / 'dist/sitemap.xml').exists())
        self.assertIn('Disallow: /', (self.root / 'dist/robots.txt').read_text())
        for page in (self.root / 'dist').rglob('*.html'):
            self.assertIn('noindex,nofollow', page.read_text())
            self.assertNotIn('rel="canonical"', page.read_text())
        self.assertIn('X-Robots-Tag: noindex, nofollow', (self.root / 'dist/_headers').read_text())

    def test_production_has_canonical_discovery_and_headers(self):
        (self.root / 'workflows/release-notes-digest/examples/real-run.md').write_text('# A real run\n\nHistorical sources; human review required.\n')
        (self.root / 'site.json').write_text(json.dumps({'repository_url': 'https://github.com/example/workflows'}))
        result = subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--root', str(self.root), '--production'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        dist = self.root / 'dist'
        urls = []
        for page in sorted(dist.rglob('index.html')):
            path = page.relative_to(dist).as_posix()
            html = (dist / path).read_text()
            route = '/' if path == 'index.html' else '/' + path[:-len('index.html')]
            urls.append('https://agentworkflows.wiki' + route)
            self.assertIn('rel="canonical" href="https://agentworkflows.wiki' + route + '"', html)
            self.assertEqual(html.count('rel="canonical"'), 1)
            self.assertIn('property="og:url" content="https://agentworkflows.wiki' + route + '"', html)
            self.assertNotIn('noindex', html)
        self.assertIn('noindex', (dist / '404.html').read_text())
        self.assertIn('Sitemap: https://agentworkflows.wiki/sitemap.xml', (dist / 'robots.txt').read_text())
        # Parse only our generated offline sitemap, never contributor XML.
        sitemap = ET.parse(dist / 'sitemap.xml')
        actual = [x.text or '' for x in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(sorted(actual), sorted(urls))
        headers = (dist / '_headers').read_text()
        self.assertIn("frame-ancestors 'none'", headers)
        self.assertIn('X-Content-Type-Options: nosniff', headers)
        self.assertNotIn('immutable', headers)


if __name__ == '__main__':
    unittest.main()
