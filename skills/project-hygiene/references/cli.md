# CLI reference

Requires Python 3.10+ and Git on PATH. No Python packages, inference, network service or model calls.

Use a full path to the installed skill's script, for example:

```
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" init
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" add tmplogs/physics-probe.log --category disposable --work physics
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" add tmpartifacts/physics-comparison.json --category disposable --work physics --useful
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" add .env --category ignored-retained --work setup
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" work physics --state completed
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" status
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" clean
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" clean --apply
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" done --owner-confirmed
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" restore <batch-uuid>
python <skill>/scripts/project_hygiene.py --root "G:/Projects/MyGame" restore <batch-uuid> --apply
```

`add` registers existing individual files only (multiple paths allowed); no globs or directory-wide permissions. Repeat `add` to reclassify a file; omitting `--useful` clears its development-useful flag. New work starts active. The CLI never reads file payloads. `status` is a read-only eligible-cleanup report and suggestion fingerprint, not an inventory scanner.

Manifest: `.project-hygiene-<project-slug>-<uuid>.json` in the exact root. Schema version 1 stores `project_id`, `slug`, canonical absolute `root`, `git_dir` (or null), `work` mapping names to active/completed, and `files` mapping exact relative POSIX paths to category/work/useful. The filename, UUID, root and Git directory must agree. Multiple manifests fail closed. A copied manifest cannot run in another root; relocation requires deliberately creating a fresh manifest and re-registering files, not disabling checks. Absolute local paths mean the manifest is local metadata, not a portable checked-in policy.

Quarantine: `.project-hygiene-trash/<project-uuid>/<batch-uuid>/files/` plus a receipt. Same-filesystem rename only. The receipt precedes moves so an interrupted batch can be restored. Restore preflights collisions and never deliberately overwrites an existing original. Repeated clean/restore is a no-op when files are already absent/restored. Preserve quarantine receipts until restoration or owner-managed disposal.

Protected name checks cover `.git`, hygiene metadata, `.env*`, common credential names and private-key extensions. These are a backstop, not secret detection: nonstandard credentials must be registered ignored-retained. No file-content secret scanning is performed. Unregistered files never qualify.

Stop writers and test processes before apply/restore. The lock excludes concurrent Hygiene processes, not arbitrary editors or other agents. The filesystem is assumed trusted and quiescent: this is not protection against a malicious concurrent process racing path replacement. Symlinks, Windows junction/reparse points and hard-linked files are not cleanup candidates. A stale lock after a crash requires the owner to verify no Hygiene process is running before removing the empty `.project-hygiene-lock` directory.

Git is queried read-only. Basic cleanup protects tracked files and project-lifetime scaffolding; final cleanup permits a tracked file only when explicitly disposable. Ignore rules do not grant cleanup rights. Consider ignoring local manifests, `.project-hygiene-lock/`, `.project-hygiene-trash/`, and the disposable directories; never use blanket ignored-file deletion. The tool does not alter `.gitignore` or push code.

`audit` adds a metadata inventory of unknown/missing files and basic/final plans. It does not prove semantic safety. `--useful` protects disposable files during basic cleanup only; final cleanup intentionally removes all explicitly disposable development artifacts. Reclassify essential files as ignored-retained/tracked/deliverable before final cleanup.
