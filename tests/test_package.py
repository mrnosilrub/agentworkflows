"""An installed regular package must not shadow our local tooling package."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_local_tools_win_over_an_unrelated_installed_package(self):
        with tempfile.TemporaryDirectory(prefix='unrelated-tools-package-') as directory:
            unrelated = Path(directory) / 'tools'
            unrelated.mkdir()
            (unrelated / '__init__.py').write_text("raise RuntimeError('Wrong tools package imported')\n")
            result = subprocess.run(
                [sys.executable, '-c', 'from tools import web; print(web.__file__)'],
                cwd=ROOT, env=dict(os.environ, PYTHONPATH=directory), text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(result.stdout.strip()).resolve(), ROOT / 'tools/web.py')


if __name__ == '__main__':
    unittest.main()
