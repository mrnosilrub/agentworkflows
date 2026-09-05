import importlib.util
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import test_build


class ExchangeTests(unittest.TestCase):
    root: Path
    setUp = test_build.BuildTests.setUp

    def module(self):
        with patch.object(sys, 'path', [str(test_build.ROOT / 'tools')] + sys.path):
            spec = importlib.util.spec_from_file_location('build_under_test', test_build.ROOT / 'tools/build.py')
            if spec is None or spec.loader is None:
                raise RuntimeError('Unable to load build module')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    def test_exchange_failure_leaves_previous_build_in_place(self):
        module = self.module()
        module.build(self.root)
        before = (self.root / 'dist/index.html').read_bytes()
        with patch.object(module, '_exchange_directories', side_effect=OSError('injected unsupported exchange')):
            with self.assertRaises(OSError):
                module.build(self.root)
        self.assertEqual((self.root / 'dist/index.html').read_bytes(), before)

    def test_exchange_replaces_without_first_removing_dist(self):
        module = self.module()
        module.build(self.root)
        original = module._exchange_directories
        observed = []
        def exchange(left, right):
            observed.append((left.is_dir(), right.is_dir()))
            original(left, right)
            self.assertTrue(left.is_dir())
            self.assertTrue(right.is_dir())
        with patch.object(module, '_exchange_directories', side_effect=exchange):
            module.build(self.root)
        self.assertEqual(observed, [(True, True)])
