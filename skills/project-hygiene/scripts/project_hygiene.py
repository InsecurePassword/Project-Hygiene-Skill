#!/usr/bin/env python3
"""Explicit, recoverable project cleanup. Python 3.10+, standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import uuid

CATEGORIES = ('tracked', 'ignored-retained', 'disposable', 'deliverable')
TRASH = '.project-hygiene-trash'


def fail(message):
    raise ValueError(message)


def link(path):
    s = path.lstat()
    return stat.S_ISLNK(s.st_mode) or bool(getattr(s, 'st_file_attributes', 0) & 0x400)


def safe(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        fail('Use a relative POSIX file path, without drive names or backslashes')
    p = PurePosixPath(relative)
    if p.is_absolute() or any(x in ('', '.', '..') for x in relative.split('/')):
        fail('Unsafe path: ' + relative)
    for part in p.parts:
        if part.rstrip(' .') != part or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', part, re.I):
            fail('Non-portable Windows path component: ' + part)
    out = root
    for part in p.parts:
        out = out / part
        if out.exists() or out.is_symlink():
            if link(out):
                fail('Links/junctions are not supported: ' + str(out))
    return out


def protected(relative):
    parts = PurePosixPath(relative).parts
    for name in parts:
        n = name.lower()
        if n in ('.git', TRASH, '.ssh', '.aws', '.azure', '.gnupg') or n.startswith('.project-hygiene-'):
            return True
        if n == '.env' or n.startswith('.env.') or n in ('credentials', 'credentials.json', 'secrets.json', 'auth.json'):
            return True
        if n.endswith(('.pem', '.key', '.p12', '.pfx', '.keystore')):
            return True
    return False


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=False)
    if result.returncode:
        fail('Git query failed; cleanup refused: ' + result.stderr.decode(errors='replace').strip())
    return result.stdout


def identity(root):
    try:
        p = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True)
    except FileNotFoundError:
        fail('Git must be installed (also for non-repository projects)')
    if p.returncode:
        # Do not quietly treat a broken repository as a non-repository.
        if any((p / '.git').exists() for p in (root, *root.parents)):
            fail('Repository exists but Git cannot identify it')
        return None
    top = Path(os.fsdecode(p.stdout).strip()).resolve()
    if top != root:
        fail('Select the exact Git repository root, not a child folder')
    return os.fsdecode(git(root, 'rev-parse', '--absolute-git-dir')).strip()


def tracked(root, repo):
    return set(os.fsdecode(git(root, 'ls-files', '-z')).split('\0')) if repo else set()


def write_json(path, data):
    tmp = path.with_name(path.name + '.tmp')
    # Exclusive temp creation avoids following an existing link or clobbering another operation.
    with tmp.open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load(root):
    found = list(root.glob('.project-hygiene-*.json'))
    if len(found) != 1:
        fail('Expected exactly one project manifest in the selected root; run init or resolve ambiguity')
    path = found[0]
    safe(root, path.name)
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('version') != 1 or data.get('root') != str(root) or data.get('git_dir') != identity(root):
        fail('Manifest project/root/repository mismatch; copied or relocated manifests are not accepted')
    project_id = str(uuid.UUID(data['project_id']))
    if path.name != f".project-hygiene-{data['slug']}-{project_id}.json":
        fail('Manifest filename does not match project identity')
    if not isinstance(data.get('files'), dict) or not isinstance(data.get('work'), dict):
        fail('Invalid manifest records')
    for work, state in data['work'].items():
        if not isinstance(work, str) or state not in ('active', 'completed'):
            fail('Invalid work state')
    for rel, record in data['files'].items():
        safe(root, rel)
        if record.get('category') not in CATEGORIES or type(record.get('useful')) is not bool or not isinstance(record.get('work'), str):
            fail('Invalid file record: ' + rel)
        if record['work'] not in data['work']:
            fail('File refers to unknown work: ' + rel)
    return path, data


def plan(root, data, final=False):
    versioned = {os.path.normcase(x) for x in tracked(root, data['git_dir'])}
    selected, kept = [], []
    for rel, record in sorted(data['files'].items()):
        path = safe(root, rel)
        reason = None
        if record['category'] != 'disposable':
            reason = record['category']
        elif protected(rel):
            reason = 'protected name'
        elif os.path.normcase(rel) in versioned and not final:
            reason = 'Git-tracked; only explicit final cleanup may remove this artifact'
        elif record['useful'] and not final:
            reason = 'potentially useful; explicitly retained'
        elif not final and PurePosixPath(rel).parts[0] == 'scaffolding':
            reason = 'project-lifetime scaffolding'
        elif not final and data['work'][record['work']] != 'completed':
            reason = 'work is active'
        elif not path.exists():
            reason = 'already absent'
        elif not path.is_file() or path.stat().st_nlink != 1:
            reason = 'not an ordinary single-link file'
        if reason:
            kept.append({'path': rel, 'reason': reason})
        else:
            selected.append({'path': rel, 'bytes': path.stat().st_size})
    return {'files': selected, 'bytes': sum(p['bytes'] for p in selected), 'kept': kept}


def audit(root, data):
    """Metadata-only inventory, not semantic proof that a file is unnecessary."""
    unknown, missing, warnings = [], [], []
    for folder, dirs, names in os.walk(root, followlinks=False):
        base = Path(folder)
        dirs[:] = [d for d in dirs if d not in ('.git', TRASH, '.project-hygiene-lock')
                   and not link(base / d)]
        for name in names:
            rel = (base / name).relative_to(root).as_posix()
            if rel.startswith('.project-hygiene-'):
                continue
            if rel not in data['files']:
                unknown.append(rel)
    for rel, record in data['files'].items():
        if not safe(root, rel).exists():
            missing.append(rel)
        if record['category'] == 'disposable' and PurePosixPath(rel).parts[0] == 'dependencies':
            warnings.append({'path': rel, 'reason': 'Verify no runtime/build dependency before cleanup'})
    return {'unknown': sorted(unknown), 'missing': sorted(missing), 'warnings': warnings,
            'basic': plan(root, data), 'final': plan(root, data, True),
            'semantic_review_required': True}


class Lock:
    def __init__(self, root):
        self.path = root / '.project-hygiene-lock'
    def __enter__(self):
        self.path.mkdir()  # Existing lock fails closed; never remove another process's lock.
    def __exit__(self, *args):
        self.path.rmdir()


def clean(root, data, final, apply):
    result = plan(root, data, final)
    result['applied'] = False
    if not apply or not result['files']:
        return result
    batch = str(uuid.uuid4())
    dest = safe(root, f'{TRASH}/{data["project_id"]}/{batch}')
    dest.mkdir(parents=True)
    journal = {'version': 1, 'project_id': data['project_id'], 'root': str(root),
               'files': [x['path'] for x in result['files']]}
    write_json(dest / 'receipt.json', journal)
    # Receipt is durable before any move. Restore detects completed and incomplete moves.
    for item in result['files']:
        rel = item['path']
        src = safe(root, rel)
        target = safe(dest, 'files/' + rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            fail('Quarantine collision')
        os.rename(src, target)  # Same filesystem only; no copy or permanent-delete fallback.
    result.update(applied=True, batch=batch, quarantine=str(dest))
    return result


def restore(root, data, batch, apply):
    batch = str(uuid.UUID(batch))
    dest = safe(root, f'{TRASH}/{data["project_id"]}/{batch}')
    receipt = safe(dest, 'receipt.json')
    journal = json.loads(receipt.read_text(encoding='utf-8'))
    if journal.get('version') != 1 or journal.get('root') != str(root) or journal.get('project_id') != data['project_id']:
        fail('Receipt identity mismatch')
    paths = journal.get('files')
    if not isinstance(paths, list) or any(not isinstance(x, str) for x in paths) or len(paths) != len(set(paths)):
        fail('Invalid receipt')
    moves = []
    for rel in paths:
        src, target = safe(dest, 'files/' + rel), safe(root, rel)
        if protected(rel):
            fail('Protected restore target')
        if not src.exists():
            if target.is_file():
                continue  # Already restored, or never moved after interruption.
            fail('Missing both quarantine and original: ' + rel)
        if not src.is_file() or src.stat().st_nlink != 1:
            fail('Invalid quarantine file')
        if target.exists():
            fail('Restore would overwrite: ' + rel)
        moves.append((src, target))
    if apply:
        for src, target in moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.rename(src, target)
    return {'restore_files': [str(t.relative_to(root)) for _, t in moves], 'applied': apply}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='Exact project root; never searches parents')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('status')
    sub.add_parser('audit')
    add = sub.add_parser('add')
    add.add_argument('paths', nargs='+', help='Exact relative file paths; no globs/directories')
    add.add_argument('--category', choices=CATEGORIES, required=True)
    add.add_argument('--work', required=True)
    add.add_argument('--useful', action='store_true', help='Keep during basic cleanup; final cleanup removes disposable artifacts even if useful')
    work = sub.add_parser('work')
    work.add_argument('name')
    work.add_argument('--state', choices=('active', 'completed'), required=True)
    for cmd in ('clean', 'done'):
        p = sub.add_parser(cmd)
        p.add_argument('--apply', action='store_true')
        if cmd == 'done':
            p.add_argument('--owner-confirmed', action='store_true')
    r = sub.add_parser('restore')
    r.add_argument('batch')
    r.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    original = Path(args.root).absolute()
    # Reject a linked root or linked ancestors before canonicalizing.
    for p in (original, *original.parents):
        if p.exists() and link(p):
            fail('Root or ancestor is a link/junction')
    root = original.resolve(strict=True)
    if not root.is_dir():
        fail('Root must be a directory')
    with Lock(root):
        if args.command == 'init':
            if list(root.glob('.project-hygiene-*.json')):
                fail('Manifest already exists')
            slug = re.sub('[^a-z0-9-]+', '-', root.name.lower()).strip('-') or 'project'
            data = {'version': 1, 'project_id': str(uuid.uuid4()), 'slug': slug,
                    'root': str(root), 'git_dir': identity(root), 'work': {}, 'files': {}}
            path = root / f'.project-hygiene-{slug}-{data["project_id"]}.json'
            write_json(path, data)
            result = {'manifest': str(path)}
        else:
            path, data = load(root)
            if args.command == 'add':
                for rel in args.paths:
                    target = safe(root, rel)
                    if not target.is_file():
                        fail('Register existing individual files, not directories: ' + rel)
                    if args.category == 'disposable' and protected(rel):
                        fail('Protected file cannot be disposable: ' + rel)
                    data['files'][rel] = {'category': args.category, 'work': args.work, 'useful': args.useful}
                data['work'].setdefault(args.work, 'active')
                write_json(path, data)
                result = {'registered': args.paths}
            elif args.command == 'work':
                if args.name not in data['work']:
                    fail('Unknown work')
                data['work'][args.name] = args.state
                write_json(path, data)
                result = {'work': args.name, 'state': args.state}
            elif args.command == 'audit':
                result = audit(root, data)
            elif args.command == 'status':
                result = plan(root, data)
                digest = hashlib.sha256(json.dumps(result['files'], sort_keys=True).encode()).hexdigest()
                result.update(suggest_clean=bool(result['files']), suggestion_id=digest)
            elif args.command == 'restore':
                result = restore(root, data, args.batch, args.apply)
            else:
                if args.command == 'done' and not args.owner_confirmed:
                    fail('Final cleanup requires explicit owner confirmation (--owner-confirmed)')
                result = clean(root, data, args.command == 'done', args.apply)
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Project Hygiene: ' + str(error), file=sys.stderr)
        sys.exit(1)
