---
name: project-hygiene
description: Organize project artifacts, maintain a root-bound manifest, suggest basic cleanup at completed-work checkpoints, and route ProjectClean, ProjectDoneClean and ProjectManifestAudit on demand.
---
# Project Hygiene

Keep this core small. Read command references only when invoked; never preload all three.

Use the bundled `scripts/project_hygiene.py` with the explicit exact project root. Initialize once. The root manifest has a project slug, UUID and absolute-root/Git binding; never borrow a parent/neighbor project's manifest.

Create new temporary work in these root-relative directories:
- `./tmp`: general temporary files unless a category below fits.
- `./tmplogs`: disposable traces, captured output and debug logs.
- `./test-tools`: small temporary testing tools, not permanent regression tests.
- `./scaffolding`: project-wide development scaffolding used from start to finish. Basic cleanup always preserves it, preventing removal of permanent/project-lifetime tools while cleaning small temporary tools.
- `./tmpartifacts`: miscellaneous development artifacts.
- `./dependencies`: project-local external dependencies where the ecosystem permits. Preserve required package-manager layouts; document exceptions instead of breaking them. Runtime dependencies are retained, not automatically trash.

Do not move existing project files merely to impose this layout. Preserve established source, assets, permanent tests/tools, local configuration and finished output locations. Create folders only when needed. Folder membership is organization, not deletion permission.

Register exact files as created: `tracked`, `ignored-retained`, `disposable`, or `deliverable`, with a work ID. Mark disposable artifacts `--useful` if they may help later during development. Unknown files are retained. Secrets/custom credentials/local configuration are ignored-retained, never disposable; do not inspect secret contents to classify them. Git ignore is not cleanup permission. Read [cli.md](references/cli.md) when syntax/schema details are needed.

## Delegated work

Apply these rules whenever otherwise-authorized delegation is used for implementation, testing, research or review. They neither require delegation nor change when it is allowed.

- As parent, explicitly give each worker this skill's location, the exact project root, its assigned work ID and permitted artifact locations. Require reading the skill before creating artifacts; do not assume inherited instructions. If a worker cannot access it, supply the relevant instructions directly and disclose that limitation.
- Use distinct worker subdirectories under the appropriate `tmp`, `tmplogs`, `test-tools`, `scaffolding`, `tmpartifacts` or `dependencies` category, for example `tmplogs/<work-id>/<worker-id>/`. Create only what is needed. Preserve established source, permanent test/tool and deliverable locations and required package-manager layouts.
- Designate one writer per shared manifest. Workers must promptly report exact artifact paths, purpose, classification and work ID as files are created; the designated writer registers them and updates work states serially. Do not allow unsynchronized concurrent manifest writes.
- Keep read-only workers read-only. If they cannot create files, have them return findings and artifact information to the parent instead of expanding permissions. Route any needed CLI operations that write, even transiently, through the authorized designated writer.
- Before accepting completion, reconcile each worker's artifact report with the manifest and actual files, preserve useful evidence, and resolve unexplained artifacts without deleting them. Mark a work ID complete only when all work assigned to it is genuinely complete; a stopped or failed worker is not completed work.
- Apply these rules recursively when workers delegate further, retaining the designated writer for each shared manifest. Delegation grants no cleanup, deletion, installation, commit or push authority.
- Keep all existing protections: retain unknown files; do not treat ignored files as automatically disposable; retain secrets/configuration; preserve scaffolding during basic cleanup; leave recoverable-removal rules unchanged. Never clean another worker's active files.

## Completion and commands

After implementation and its testing complete, mark only that work ID completed and run `status`. If `suggest_clean` is true, offer `/ProjectClean` once per `suggestion_id` in the current session. Do not scan every turn, create a background service, or interpret model/session termination as completion. This is an advisory function, not automatic removal.

Route commands lazily:
- `/ProjectClean`: read [project-clean.md](references/project-clean.md).
- `/ProjectDoneClean`: read [project-done-clean.md](references/project-done-clean.md).
- `/ProjectManifestAudit`: read [project-manifest-audit.md](references/project-manifest-audit.md).

The CLI provides deterministic checks; the LLM supplies semantic judgment. No skill can prove a file has no future use. Git staging/pushes and permanent purge are not implicit cleanup actions.
