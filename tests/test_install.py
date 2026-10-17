import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'scripts/install_opencode.py')
i = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(i)

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / 'config'

    def test_roundtrip_update_uninstall(self):
        r = i.run('install', self.config)
        self.assertGreater(r['installed_files'], 3)
        self.assertTrue((self.config / 'skills/project-hygiene/SKILL.md').exists())
        (self.config / 'unrelated.txt').write_text('keep')
        updated = i.run('update', self.config)
        self.assertTrue((Path(updated['backup']) / 'skills/project-hygiene/SKILL.md').exists())
        removed = i.run('uninstall', self.config)
        self.assertFalse((self.config / 'commands/ProjectClean.md').exists())
        self.assertTrue((self.config / 'unrelated.txt').exists())
        self.assertTrue((Path(removed['backup']) / 'commands/ProjectClean.md').exists())

    def test_modified_file_refused(self):
        i.run('install', self.config)
        p = self.config / 'commands/ProjectClean.md'
        p.write_text('local edit')
        with self.assertRaises(ValueError):
            i.run('uninstall', self.config)
        self.assertEqual(p.read_text(), 'local edit')

    def test_unowned_collision_refused(self):
        p = self.config / 'commands/ProjectClean.md'
        p.parent.mkdir(parents=True)
        p.write_text('existing')
        with self.assertRaises(ValueError):
            i.run('install', self.config)
        self.assertEqual(p.read_text(), 'existing')

    def test_pi_package_manifest(self):
        data = json.loads((i.PACKAGE / 'package.json').read_text())
        self.assertTrue(data['private'])
        self.assertEqual(data['pi']['skills'], ['./skills'])
        self.assertEqual(data['pi']['prompts'], ['./prompts/*.md'])
        self.assertNotIn('dependencies', data)

    def test_update_failure_rolls_back(self):
        i.run('install', self.config)
        before = (self.config / i.RECEIPT).read_bytes()
        original = i.os.rename
        failed = False
        def break_new_once(src, dst):
            nonlocal failed
            if 'staged-new' in str(src) and not failed:
                failed = True
                raise OSError('injected move failure')
            return original(src, dst)
        with patch.object(i.os, 'rename', side_effect=break_new_once):
            with self.assertRaises(OSError):
                i.run('update', self.config)
        self.assertEqual((self.config / i.RECEIPT).read_bytes(), before)
        for rel, sha in json.loads(before)['files'].items():
            self.assertEqual(i.digest(self.config / rel), sha)
        i.run('update', self.config)
