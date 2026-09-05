import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('workflows', 'templates', 'skills', 'assets'):
            if (ROOT / name).exists():
                shutil.copytree(ROOT / name, self.root / name)
        for name in ('LICENSE', 'CONTRIBUTING.md', 'site.json'):
            shutil.copy2(ROOT / name, self.root / name)
        (self.root / 'site.json').write_text(json.dumps({'repository_url': None}))

    def build(self):
        return subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--root', str(self.root)],
                              capture_output=True, text=True)

    def test_build_uses_same_workflows_for_pages_and_catalog(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads((self.root / 'dist/catalog.json').read_text())
        expected = sorted(p.name for p in (self.root / 'workflows').iterdir())
        self.assertEqual([x['id'] for x in catalog['workflows']], expected)
        for item in catalog['workflows']:
            self.assertTrue((self.root / 'dist' / item['skill_url'].lstrip('/')).is_file())
            self.assertTrue((self.root / 'dist/workflows' / item['id'] / 'index.html').is_file())
        self.assertTrue((self.root / 'dist/contribute/SKILL.md').is_file())
        self.assertFalse((self.root / 'dist/tools').exists())


    def test_rebuild_removes_deleted_workflow_routes(self):
        self.assertEqual(self.build().returncode, 0)
        shutil.rmtree(self.root / 'workflows/documentation-update')
        self.assertEqual(self.build().returncode, 0)
        self.assertFalse((self.root / 'dist/workflows/documentation-update').exists())


    def test_exported_support_symlinks_are_rejected_without_losing_output(self):
        self.assertEqual(self.build().returncode, 0)
        before = (self.root / 'dist/index.html').read_bytes()
        outside = self.root / 'private.txt'
        outside.write_text('PRIVATE-SENTINEL')
        for relative in ('assets/site.js', 'CONTRIBUTING.md', 'templates/workflow/SKILL.md', 'skills/contribute-agentworkflows/SKILL.md'):
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_bytes()
                path.unlink()
                path.symlink_to(outside)
                result = self.build()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((self.root / 'dist/index.html').read_bytes(), before)
                path.unlink()
                path.write_bytes(original)
        assets = self.root / 'assets'
        assets.rename(self.root / 'moved-assets')
        assets.symlink_to(self.root / 'moved-assets', target_is_directory=True)
        self.assertNotEqual(self.build().returncode, 0)

    def test_build_preserves_unowned_output_directory(self):
        (self.root / 'dist').mkdir()
        (self.root / 'dist/keep.txt').write_text('unrelated work')
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / 'dist/keep.txt').read_text(), 'unrelated work')

    def test_render_failure_preserves_last_good_output(self):
        self.assertEqual(self.build().returncode, 0)
        before = (self.root / 'dist/index.html').read_bytes()
        (self.root / 'CONTRIBUTING.md').unlink()
        self.assertNotEqual(self.build().returncode, 0)
        self.assertEqual((self.root / 'dist/index.html').read_bytes(), before)
        self.assertTrue((self.root / 'dist/contribute/index.html').is_file())


    def test_build_rejects_non_github_repository_url(self):
        (self.root / 'site.json').write_text(json.dumps({'repository_url': 'javascript:alert(1)'}))
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse((self.root / 'dist').exists())


    def test_build_exports_supplementary_example_markdown(self):
        extra = 'workflows/documentation-update/examples/extra notes.md'
        (self.root / extra).write_text('A supplementary public example note.')
        self.assertEqual(self.build().returncode, 0)
        self.assertTrue((self.root / 'dist' / extra).is_file())
        data = json.loads((self.root / 'dist/catalog.json').read_text())
        entry = next(w for w in data['workflows'] if w['id'] == 'documentation-update')
        self.assertIn('/workflows/documentation-update/examples/extra%20notes.md', entry.get('example_urls', []))


    def test_public_walkthrough_is_rendered_from_validated_example(self):
        source = self.root / 'workflows/release-notes-digest/examples/real-run.md'
        source.write_text('# A real release digest\n\nA bounded run, not certification.\n')
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.root / 'dist/examples/release-notes-digest/index.html'
        self.assertIn('<h1>A real release digest</h1>', page.read_text())
        self.assertIn('/examples/release-notes-digest/', (self.root / 'dist/index.html').read_text())
        self.assertIn('/examples/release-notes-digest/', (self.root / 'dist/workflows/release-notes-digest/index.html').read_text())

    def test_build_preserves_binary_share_card_bytes(self):
        image = b'\x89PNG\r\n\x1a\n\xff\x00binary-test-fixture'
        (self.root / 'assets/share-card.png').write_bytes(image)
        self.assertEqual(self.build().returncode, 0)
        self.assertEqual((self.root / 'dist/assets/share-card.png').read_bytes(), image)

    def test_build_does_not_publish_unlisted_support_files(self):
        (self.root / 'assets/private-note.txt').write_text('not a public asset')
        (self.root / 'templates/workflow/private-note.txt').write_text('not a public template')
        self.assertEqual(self.build().returncode, 0)
        self.assertFalse((self.root / 'dist/assets/private-note.txt').exists())
        self.assertFalse((self.root / 'dist/contribute/template/private-note.txt').exists())


if __name__ == '__main__':
    unittest.main()
