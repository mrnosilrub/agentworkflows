"""Local checks of CI policy; not a claim of a live GitHub Actions run."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CIPolicyTests(unittest.TestCase):
    def test_ci_runs_only_maintainer_authorized_revisions(self):
        text = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertRegex(text, r'(?m)^  workflow_dispatch:$')
        self.assertNotRegex(text, r'(?m)^  pull_request(?:_target)?:$')
        self.assertIn('branches: [main]', text)
        self.assertIn('contents: read', text)
        self.assertNotIn('contents: write', text)
        self.assertNotIn('allow-unsafe-pr-checkout', text)
        self.assertIn('run: python3 -I trusted/tools/catalog.py check --root trusted', text)
        self.assertIn('ref: ${{ github.sha }}', text)
        self.assertEqual(text.count('persist-credentials: false'), 1)

    def test_trusted_validator_ignores_candidate_programs_and_pythonpath(self):
        with tempfile.TemporaryDirectory(prefix='untrusted-contribution-') as directory:
            candidate = Path(directory)
            shutil.copytree(ROOT / 'workflows', candidate / 'workflows')
            (candidate / 'tools').mkdir()
            marker = candidate / 'UNTRUSTED-CODE-RAN'
            payload = 'from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("bad")\n'
            (candidate / 'tools/catalog.py').write_text(payload)
            (candidate / 'json.py').write_text(payload)
            environment = dict(os.environ, PYTHONPATH=str(candidate))
            result = subprocess.run([sys.executable, '-I', str(ROOT / 'tools/catalog.py'),
                                     'check', '--root', str(candidate)], cwd=candidate,
                                    env=environment, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['workflow_count'], 2)
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
