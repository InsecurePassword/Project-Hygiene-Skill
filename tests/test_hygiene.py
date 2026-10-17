import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/project-hygiene/scripts/project_hygiene.py'
spec = importlib.util.spec_from_file_location('hygiene', SCRIPT)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

class HygieneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'Project'
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.run_cli('init')
    def tearDown(self):
        self.temp.cleanup()
    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return h.main(['--root', str(self.root), *args])
    def file(self, rel, category='disposable', useful=False, work='task'):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('example')
        args = ['add', rel, '--category', category, '--work', work]
        if useful: args += ['--useful']
        self.run_cli(*args)
        return path
    def complete(self): self.run_cli('work', 'task', '--state', 'completed')
    def test_dry_run_active_then_completed(self):
        p = self.file('tmp/a'); self.assertFalse(self.run_cli('clean')['files'])
        self.complete(); self.assertEqual(self.run_cli('clean')['bytes'], 7); self.assertTrue(p.exists())
    def test_clean_restore_idempotent(self):
        p = self.file('tmp/a'); self.complete()
        r = self.run_cli('clean', '--apply'); self.assertFalse(p.exists())
        self.assertFalse(self.run_cli('clean', '--apply')['files'])
        self.run_cli('restore', r['batch'], '--apply'); self.assertEqual(p.read_text(), 'example')
        self.assertEqual(self.run_cli('restore', r['batch'], '--apply')['restore_files'], [])
    def test_retained_and_deliverable(self):
        for category in ('tracked', 'ignored-retained', 'deliverable'):
            self.file(category, category)
        self.assertFalse(self.run_cli('done', '--owner-confirmed', '--apply')['files'])
    def test_final_removes_useful_disposable(self):
        p = self.file('test-tools/probe.py', useful=True); self.complete()
        self.assertFalse(self.run_cli('clean')['files'])
        self.run_cli('done', '--owner-confirmed', '--apply'); self.assertFalse(p.exists())
    def test_scaffolding_basic_retention(self):
        p = self.file('scaffolding/runner.py'); self.complete()
        self.assertFalse(self.run_cli('clean')['files'])
        self.run_cli('done', '--owner-confirmed', '--apply'); self.assertFalse(p.exists())
    def test_final_requires_confirmation(self):
        with self.assertRaises(ValueError): self.run_cli('done', '--apply')
    def test_unknown_ignored_not_deleted(self):
        (self.root / '.gitignore').write_text('unknown\n')
        (self.root / 'unknown').write_text('keep')
        self.run_cli('done', '--owner-confirmed', '--apply')
        self.assertTrue((self.root / 'unknown').exists())
    def test_secrets_protected(self):
        for rel in ('.env', '.env.local', 'nested/credentials.json', 'key.pem'):
            with self.assertRaises(ValueError): self.file(rel)
    def test_copy_wrong_root(self):
        other = Path(self.temp.name) / 'Other'; shutil.copytree(self.root, other)
        with self.assertRaises(ValueError): h.load(other)
    def test_manifest_wrong_filename(self):
        p = next(self.root.glob('.project-hygiene-*.json'))
        p.rename(self.root / '.project-hygiene-wrong.json')
        with self.assertRaises(ValueError): self.run_cli('status')
    def test_multiple_manifests(self):
        (self.root / '.project-hygiene-other.json').write_text('{}')
        with self.assertRaises(ValueError): self.run_cli('status')
    def test_paths(self):
        for rel in ('../outside', '/etc/passwd', 'a/../b', 'C:/data', 'a\\b', 'a//b', 'tmp/a.', 'tmp/a ', 'CON', 'aux.txt'):
            with self.assertRaises(ValueError): h.safe(self.root, rel)
    def test_symlink(self):
        p = self.file('tmp/a'); p.unlink(); p.symlink_to(Path(self.temp.name))
        with self.assertRaises(ValueError): self.run_cli('clean', '--apply')
    def test_hardlink_kept(self):
        p = self.file('tmp/a'); (self.root / 'link').hardlink_to(p); self.complete()
        self.assertFalse(self.run_cli('clean')['files'])
    def test_collision_restore(self):
        p = self.file('tmp/a'); self.complete(); r = self.run_cli('clean', '--apply')
        p.write_text('new')
        with self.assertRaises(ValueError): self.run_cli('restore', r['batch'], '--apply')
        self.assertEqual(p.read_text(), 'new')
    def test_lock_blocks(self):
        (self.root / '.project-hygiene-lock').mkdir()
        with self.assertRaises(FileExistsError): self.run_cli('status')
    def test_audit_reports_unknown(self):
        (self.root / 'unknown').write_text('keep')
        self.assertIn('unknown', self.run_cli('audit')['unknown'])
    def test_suggestion_fingerprint(self):
        self.file('tmp/a'); self.complete()
        a = self.run_cli('status'); b = self.run_cli('status')
        self.assertTrue(a['suggest_clean']); self.assertEqual(a['suggestion_id'], b['suggestion_id'])
    def test_git_tracked_explicit_final_only(self):
        # Reinitialize identity deliberately for this fixture after git init.
        next(self.root.glob('.project-hygiene-*.json')).unlink()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.run_cli('init'); p = self.file('test-tools/probe.py')
        subprocess.run(['git', '-C', str(self.root), 'add', 'test-tools/probe.py'], check=True)
        self.complete(); self.assertFalse(self.run_cli('clean')['files'])
        self.run_cli('done', '--owner-confirmed', '--apply'); self.assertFalse(p.exists())
    def test_interrupted_move_receipt(self):
        from unittest.mock import patch
        a = self.file('tmp/a'); b = self.file('tmp/b'); self.complete()
        rename = h.os.rename
        def broken(src, dst):
            if Path(src).name == 'b': raise OSError('simulated failure')
            return rename(src, dst)
        with patch.object(h.os, 'rename', broken):
            with self.assertRaises(OSError): self.run_cli('clean', '--apply')
        batch = next((self.root / h.TRASH).glob('*/*')).name
        self.run_cli('restore', batch, '--apply')
        self.assertTrue(a.exists()); self.assertTrue(b.exists())

if __name__ == '__main__': unittest.main()
