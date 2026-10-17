#!/usr/bin/env python3
"""Install/update/uninstall only this package's OpenCode skill and commands."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import uuid

PACKAGE = Path(__file__).resolve().parents[1]
RECEIPT = '.project-hygiene-install.json'
BACKUPS = '.project-hygiene-install-backups'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def safe(base, relative):
    parts = Path(relative).parts
    if Path(relative).is_absolute() or '..' in parts:
        raise ValueError('Unsafe package path')
    p = base
    for part in parts:
        p = p / part
        if p.exists() or p.is_symlink():
            s = p.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Symlink/reparse point refused: ' + str(p))
    return p


def sources():
    result = {}
    for p in (PACKAGE / 'skills/project-hygiene').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
            result[p.relative_to(PACKAGE).as_posix()] = p
    for p in (PACKAGE / '.opencode/commands').glob('*.md'):
        result['commands/' + p.name] = p
    return result


def run(action, destination):
    destination = Path(destination).absolute()
    for p in (destination, *destination.parents):
        if p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked destination refused')
    destination.mkdir(parents=True, exist_ok=True)
    lock = destination / '.project-hygiene-install-lock'
    lock.mkdir()
    try:
        receipt = safe(destination, RECEIPT)
        old = json.loads(receipt.read_text()) if receipt.exists() else None
        if action in ('update', 'uninstall') and old is None:
            raise ValueError('No owned installation; use install first')
        if action == 'install' and old is not None:
            raise ValueError('Already installed; use update')
        if old and (old.get('package') != 'project-hygiene-skill' or old.get('destination') != str(destination)):
            raise ValueError('Installation receipt identity mismatch')
        previous = old['files'] if old else {}
        incoming = sources() if action != 'uninstall' else {}
        # Check every owned file and collision before moving anything.
        for rel, sha in previous.items():
            if not (rel.startswith('skills/project-hygiene/') or rel in ['commands/' + n + '.md' for n in ('ProjectClean', 'ProjectDoneClean', 'ProjectManifestAudit')]):
                raise ValueError('Unexpected owned path')
            p = safe(destination, rel)
            if p.exists() and (not p.is_file() or digest(p) != sha):
                raise ValueError('Locally changed installed file; preserve/reconcile before retry: ' + rel)
        for rel in incoming:
            p = safe(destination, rel)
            if p.exists() and rel not in previous:
                raise ValueError('Unowned destination collision: ' + rel)
        backup = safe(destination, BACKUPS + '/' + str(uuid.uuid4()))
        backup.mkdir(parents=True)
        (backup / 'operation.json').write_text(json.dumps({'action': action, 'destination': str(destination), 'old': old, 'incoming': list(incoming)}, indent=2))
        print('Recovery backup: ' + str(backup), file=sys.stderr)
        # Stage every new file before touching the installed version.
        staged = backup / 'staged-new'
        for rel, source in incoming.items():
            target = safe(staged, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(source.read_bytes())
        moved_old, moved_new = [], []
        receipt_moved = False
        creating_receipt = False
        try:
            for rel in previous:
                p = safe(destination, rel)
                if p.exists():
                    target = safe(backup, rel)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(p, target)
                    moved_old.append(rel)
            if receipt.exists():
                os.rename(receipt, backup / RECEIPT)
                receipt_moved = True
            for rel in incoming:
                target = safe(destination, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.rename(safe(staged, rel), target)
                moved_new.append(rel)
            if action != 'uninstall':
                data = {'package': 'project-hygiene-skill', 'version': '0.1.0', 'destination': str(destination),
                        'files': {rel: digest(safe(destination, rel)) for rel in incoming}}
                creating_receipt = True
                with receipt.open('x', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception:
            # Preserve new/partial files too; never permanently delete during rollback.
            failed = backup / 'failed-new'
            if creating_receipt and receipt.exists():
                failed.mkdir(parents=True, exist_ok=True)
                os.rename(receipt, failed / RECEIPT)
            for rel in reversed(moved_new):
                target = safe(failed, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.rename(safe(destination, rel), target)
            for rel in reversed(moved_old):
                target = safe(destination, rel)
                if target.exists():
                    raise ValueError('Rollback collision; inspect recovery backup: ' + str(backup))
                os.rename(safe(backup, rel), target)
            if receipt_moved:
                os.rename(backup / RECEIPT, receipt)
            raise
        return {'action': action, 'destination': str(destination), 'backup': str(backup), 'installed_files': len(incoming)}
    finally:
        lock.rmdir()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('install', 'update', 'uninstall'))
    p.add_argument('--config-dir', type=Path, default=Path.home() / '.config/opencode', help='OpenCode configuration directory; use PROJECT/.opencode for project-local install')
    args = p.parse_args()
    try:
        print(json.dumps(run(args.action, args.config_dir), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        p.exit(1, 'Project Hygiene installer: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
